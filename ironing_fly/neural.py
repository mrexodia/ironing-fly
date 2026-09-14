"""Current-based LIF, in mV and ms; no physiological validation is implied."""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.sparse import csr_matrix

@dataclass
class NeuralConfig:
    dt_ms: float = 0.5
    tau_membrane_ms: float = 20.0
    tau_synapse_ms: float = 5.0
    rest_mv: float = -52.0
    reset_mv: float = -52.0
    threshold_mv: float = -45.0
    refractory_ms: float = 2.5
    delay_ms: float = 2.0
    weight_mv: float = 0.275
    weight_scale: float = 4.0
    cutoff: int = 5
    background_hz: float = 0.0
    stimulus_hz: float = 150.0
    external_jump_mv: float = 16.0
    trace_ms: float = 100.0
    glutamate_sign: int = -1
    unknown_sign: int = 0

class Brain:
    def __init__(self, circuit, config=None, seed=42, wiring='real'):
        self.circuit = circuit
        self.config = c = config or NeuralConfig()
        if c.dt_ms <= 0 or c.dt_ms > min(c.tau_membrane_ms, c.tau_synapse_ms) / 2:
            raise ValueError('Timestep must resolve the membrane and synaptic constants')
        self.n = len(circuit['nodes'])
        self.inputs = np.array(circuit['inputs'], dtype=int)
        self.motors = np.array(circuit['motors'], dtype=int)
        self.rng = np.random.default_rng(seed)
        edge = np.array(circuit['edges'], dtype=int)
        edge = edge[edge[:, 2] >= c.cutoff]
        pre, post, count = edge.T
        if wiring == 'shuffled':
            # Permutes target stubs: preserves each source's outgoing weights and
            # each target's incoming edge count, but changes partners. May add autapses.
            post = np.random.default_rng(2026).permutation(post)
        signs = {'acetylcholine': 1, 'gaba': -1, 'glutamate': c.glutamate_sign, 'histamine': -1}
        sign = np.array([signs.get(n['neurotransmitter_verified'] or n['neurotransmitter_predicted'], c.unknown_sign) for n in circuit['nodes']])
        weights = count * c.weight_mv * c.weight_scale * sign[pre]
        if wiring == 'zero':
            weights = weights * 0
        self.matrix = csr_matrix((weights, (post, pre)), shape=(self.n, self.n))
        self.edge_count = len(edge)
        self.v = np.full(self.n, c.rest_mv)
        self.g = np.zeros(self.n)
        self.refractory = np.zeros(self.n)
        self.trace = np.zeros(self.n)
        self.delay_steps = max(1, round(c.delay_ms / c.dt_ms))
        self.queue = np.zeros((self.delay_steps, self.n))
        self.step_index = 0
        self.total_spikes = np.zeros(self.n, dtype=int)
        self.events = []
        self.record = True

    @property
    def time_ms(self):
        return self.step_index * self.config.dt_ms

    def advance(self, rates, duration_ms=20.0):
        c = self.config
        rates = np.asarray(rates, dtype=float)
        if rates.shape != (len(self.inputs),) or not np.isfinite(rates).all() or (rates < 0).any():
            raise ValueError('Provide a finite nonnegative rate for each input')
        steps = round(duration_ms / c.dt_ms)
        if abs(steps * c.dt_ms - duration_ms) > 1e-6:
            raise ValueError('Duration must be a multiple of dt')
        counts = np.zeros(self.n)
        em = np.exp(-c.dt_ms / c.tau_membrane_ms)
        es = np.exp(-c.dt_ms / c.tau_synapse_ms)
        et = np.exp(-c.dt_ms / c.trace_ms)
        for _ in range(steps):
            slot = self.step_index % self.delay_steps
            self.g = self.g * es + self.queue[slot]
            self.queue[slot] = 0
            active = self.refractory <= 0
            self.v[active] = c.rest_mv + (self.v[active] - c.rest_mv) * em + self.g[active] * (1 - em)
            if c.background_hz:
                self.v += self.rng.poisson(c.background_hz * c.dt_ms / 1000, self.n) * c.external_jump_mv * active
            self.v[self.inputs] += self.rng.poisson(rates * c.dt_ms / 1000) * c.external_jump_mv * active[self.inputs]
            fired = (self.v >= c.threshold_mv) & active
            self.refractory -= c.dt_ms
            self.v[fired] = c.reset_mv
            self.g[fired] = 0
            self.refractory[fired] = c.refractory_ms
            self.queue[slot] = self.matrix @ fired.astype(float)
            self.trace = self.trace * et + fired * (1000 / c.trace_ms)
            self.total_spikes += fired
            counts += fired
            self.step_index += 1
            if self.record:
                self.events.extend((round(self.time_ms, 3), int(i)) for i in np.flatnonzero(fired))
        if not np.isfinite(self.v).all() or not np.isfinite(self.g).all():
            raise FloatingPointError('Non-finite neural state')
        return counts

    def settings(self):
        return asdict(self.config)

    def diagnostics(self):
        rates = self.total_spikes / max(self.time_ms / 1000, 1e-9)
        return {'silent': bool(not self.total_spikes.sum()), 'max_rate_hz': float(rates.max()),
                'high_rate': bool(rates.max() > 300), 'finite': bool(np.isfinite(self.v).all()),
                'motor_mean_hz': float(rates[self.motors].mean())}
