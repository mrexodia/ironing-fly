"""Full sparse LIF backend, with matching CPU/GPU equations and CPU-seeded inputs.

Exact passive integration of coupled exponential current between discrete
events; GPU uses float32, CPU uses float64. Cross-backend bit equality is NOT
assumed. A spike affects its target after the configured quantized delay.
"""
from dataclasses import asdict
from time import perf_counter
import numpy as np
from scipy.sparse import csr_matrix
from .neural import NeuralConfig

class FullBrain:
    def __init__(self, graph, config=None, seed=42, wiring='real', backend='auto', ablate_outputs=False):
        self.graph = graph
        self.config = c = config or NeuralConfig(weight_scale=1)
        self.n = graph.n
        self.rng = np.random.default_rng(seed)
        self.wiring = wiring
        if c.dt_ms <= 0 or c.delay_ms < c.dt_ms or c.tau_membrane_ms <= 0 or c.tau_synapse_ms <= 0:
            raise ValueError('Invalid full-network timing constants')
        self.xp = np
        self.backend = 'cpu'
        self.backend_note = ''
        self.device = None
        if backend in ['auto','cuda']:
            try:
                import cupy as cp
                cp.cuda.Device(0).use()
                cp.zeros(1).sum().item()
                from cupyx.scipy.sparse import csr_matrix as gpu_csr
                self.xp, self.backend = cp, 'cuda'
                self.device = cp.cuda.runtime.getDeviceProperties(0)['name'].decode()
            except Exception as error:
                if backend == 'cuda':
                    raise RuntimeError(f'CUDA backend unavailable: {error}') from error
                self.backend_note = f'CPU fallback: {type(error).__name__}. Install the gpu extra for CUDA.'
        xp = self.xp
        self.input_groups = {k:np.array(v,dtype=np.int32) for k,v in graph.groups.items() if k.startswith(('LC','LPLC','LLPC','LPC','contact_','thermal_'))}
        self.inputs = np.array(sorted({int(i) for group in self.input_groups.values() for i in group}),dtype=np.int32)
        self.input_index = {int(i):j for j,i in enumerate(self.inputs)}
        self.display = np.array(graph.groups['display'],dtype=np.int32)
        self.output_groups = {k:np.array(v,dtype=np.int32) for k,v in graph.groups.items() if k.startswith(('DNa','DNp','MDN','front_motor'))}
        self.outputs = np.array(sorted({int(i) for group in self.output_groups.values() for i in group}),dtype=np.int32)
        self.sample = np.unique(np.r_[self.inputs,self.outputs,self.display]).astype(np.int32)
        self.sample_index = {int(i):j for j,i in enumerate(self.sample)}
        keep = graph.counts >= c.cutoff
        pre, post = graph.pre[keep], graph.post[keep]
        if wiring == 'shuffled':
            post = np.random.default_rng(2026).permutation(post)
        weights = graph.counts[keep].astype(np.float64) * c.weight_mv * c.weight_scale * graph.signs[pre]
        if wiring == 'zero': weights[:] = 0
        if ablate_outputs:
            weights[np.isin(post,self.outputs)] = 0
        self.ablate_outputs = ablate_outputs
        cpu_matrix = csr_matrix((weights,(post,pre)),shape=(self.n,self.n))
        self.edge_count = int(keep.sum())
        self.effective_edges = int(np.count_nonzero(weights))
        dtype = xp.float32 if self.backend=='cuda' else xp.float64
        self.matrix = gpu_csr(cpu_matrix.astype(np.float32)) if self.backend=='cuda' else cpu_matrix
        self.v = xp.full(self.n,c.rest_mv,dtype=dtype)
        self.g = xp.zeros(self.n,dtype=dtype)
        self.refractory = xp.zeros(self.n,dtype=dtype)
        self.trace = xp.zeros(self.n,dtype=dtype)
        self.total_spikes = xp.zeros(self.n,dtype=xp.int64)
        self.delay_steps = max(1,round(c.delay_ms/c.dt_ms))
        self.queue = xp.zeros((self.delay_steps,self.n),dtype=dtype)
        self.xinputs, self.xsample = xp.asarray(self.inputs), xp.asarray(self.sample)
        self.step_index = 0
        self.wall_seconds = 0.
        self.last_events = []
        self.last_sample_counts = np.zeros(len(self.sample))
        self.sample_rates = np.zeros(len(self.sample))
        self.network_spikes = 0
        self.peak_rate = 0.

    @property
    def time_ms(self):
        return self.step_index*self.config.dt_ms

    def to_cpu(self,value):
        return self.xp.asnumpy(value) if self.backend=='cuda' else np.asarray(value)

    def encode_rates(self,channels):
        rates = np.zeros(len(self.inputs))
        for key, group in self.input_groups.items():
            value = max(0.,float(channels.get(key,0)))
            for cell in group: rates[self.input_index[int(cell)]] = value
        return rates

    def advance(self,rates,duration_ms=20):
        c,xp = self.config,self.xp
        rates = np.asarray(rates,dtype=float)
        if rates.shape!=(len(self.inputs),) or not np.isfinite(rates).all() or (rates<0).any():
            raise ValueError('Input rates must match the named sensory population')
        steps = round(duration_ms/c.dt_ms)
        if not np.isclose(steps*c.dt_ms,duration_ms): raise ValueError('Non-integral time step')
        start = perf_counter()
        # Draw once in step order; same Poisson stream on CPU and GPU.
        pulses = xp.asarray(self.rng.poisson(rates*c.dt_ms/1000,size=(steps,len(rates))) * c.external_jump_mv,dtype=self.v.dtype)
        em, es, et = np.exp(-c.dt_ms/c.tau_membrane_ms),np.exp(-c.dt_ms/c.tau_synapse_ms),np.exp(-c.dt_ms/c.trace_ms)
        coupling = c.dt_ms/c.tau_membrane_ms*em if c.tau_membrane_ms==c.tau_synapse_ms else c.tau_synapse_ms/(c.tau_synapse_ms-c.tau_membrane_ms)*(es-em)
        sampled_spikes = xp.zeros((steps,len(self.sample)),dtype=xp.bool_)
        for t in range(steps):
            slot = self.step_index % self.delay_steps
            current = self.g + self.queue[slot]
            active = self.refractory <= 0
            candidate = c.rest_mv+(self.v-c.rest_mv)*em+current*coupling
            self.v = xp.where(active,candidate,c.reset_mv)
            self.g = current*es
            self.v[self.xinputs] += pulses[t]*active[self.xinputs]
            if c.background_hz:
                # Independent CPU RNG, explicit optional drive; defaults to zero.
                background = self.rng.poisson(c.background_hz*c.dt_ms/1000,self.n)*c.external_jump_mv
                self.v += xp.asarray(background,dtype=self.v.dtype)*active
            fired = (self.v>=c.threshold_mv)&active
            if self.ablate_outputs: fired[xp.asarray(self.outputs)] = False
            self.refractory = xp.where(fired,c.refractory_ms,self.refractory-c.dt_ms)
            self.v = xp.where(fired,c.reset_mv,self.v)
            self.g = xp.where(fired,0,self.g)
            self.trace = self.trace*et+fired*(1000/c.trace_ms)
            self.total_spikes += fired
            self.queue[slot] = self.matrix @ fired.astype(self.v.dtype)
            sampled_spikes[t] = fired[self.xsample]
            self.step_index += 1
        events = self.to_cpu(sampled_spikes)
        self.last_sample_counts = events.sum(0)
        self.sample_rates = self.to_cpu(self.trace[self.xsample])
        self.last_events = [(round((self.step_index-steps+int(t)+1)*c.dt_ms,3),int(self.sample[i])) for t,i in zip(*np.nonzero(events))]
        self.network_spikes = int(self.total_spikes.sum().item())
        self.peak_rate = float(self.total_spikes.max().item())/max(self.time_ms/1000,1e-9)
        if not bool(xp.isfinite(self.v).all().item()) or not bool(xp.isfinite(self.g).all().item()):
            raise FloatingPointError('Non-finite full-network state')
        self.wall_seconds += perf_counter()-start
        return self.last_sample_counts

    def population_rates(self):
        return {name:float(np.mean([self.sample_rates[self.sample_index[int(i)]] for i in ids])) if len(ids) else 0. for name,ids in self.output_groups.items()}

    def diagnostics(self):
        return {'silent':self.network_spikes==0,'max_rate_hz':self.peak_rate,'high_rate':self.peak_rate>300,
                'finite':True,'motor_mean_hz':float(np.mean(list(self.population_rates().values()))),
                'backend':self.backend,'device':self.device,'backend_note':self.backend_note,
                'neurons':self.n,'edges':self.edge_count,'effective_edges':self.effective_edges,
                'network_spikes':self.network_spikes,'wall_seconds':round(self.wall_seconds,3),
                'sim_seconds_per_wall_second':self.time_ms/1000/max(self.wall_seconds,1e-9)}

    def settings(self):
        return asdict(self.config)
