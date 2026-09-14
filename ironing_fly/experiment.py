from dataclasses import asdict
from bisect import bisect_left
import json
import time
import numpy as np
from .data import ROOT, load_circuit
from .neural import Brain, NeuralConfig
from .cloth import Cloth
from .readout import train

class Session:
    def __init__(self, circuit, config=None, seed=42, fabric='cotton', garment='shirt', temperature=170, controller='real', readout=None):
        self.config = config or NeuralConfig()
        self.circuit, self.seed, self.controller = circuit, seed, controller
        self.cloth = Cloth(seed, fabric, garment, temperature)
        wiring = controller if controller in ['real', 'shuffled', 'zero'] else 'real'
        self.brain = Brain(circuit, self.config, seed=seed, wiring=wiring)
        self.readout = (readout or train(circuit, self.config, wiring)) if controller in ['real', 'shuffled', 'zero'] else None
        self.rng = np.random.default_rng(seed + 101)
        self.history = []
        self.action = np.zeros(4)
        self.last_counts = np.zeros(self.brain.n)

    def step(self, ticks=5, manual=None):
        counts = np.zeros(self.brain.n)
        for _ in range(ticks):
            features = self.cloth.features()
            counts += self.brain.advance(features * self.config.stimulus_hz)
            if self.controller in ['real', 'shuffled', 'zero']:
                action = self.readout.predict(self.brain.trace[self.brain.motors])
            elif self.controller == 'expert':
                action = Cloth.expert(features)
            elif self.controller == 'manual':
                action = np.asarray(manual or [0, 0, 0, 0])
            else:
                # Hold random actions for 200ms so they have a meaningful effect.
                if len(self.history) % 10 == 0:
                    self.action = np.r_[self.rng.uniform(-1, 1, 2), self.rng.uniform(0, 1, 2)]
                action = self.action
            self.action = np.asarray(action)
            self.cloth.step(action)
            self.history.append({'time_s': round(self.cloth.time, 3), 'action': action.tolist(), 'input_hz': (features * self.config.stimulus_hz).tolist(), **self.cloth.metrics()})
        self.last_counts = counts
        return self.snapshot()

    def snapshot(self):
        start = bisect_left(self.brain.events, (self.brain.time_ms - 1000, -1))
        return {'cloth': self.cloth.snapshot(), 'controller': self.controller,
                'neural': {'time_ms': self.brain.time_ms, 'spikes': self.brain.events[start:],
                           'counts': self.last_counts.tolist(), 'rates': self.brain.trace.round(2).tolist(),
                           'diagnostics': self.brain.diagnostics()},
                'action': self.action.tolist(), 'readout': self.readout.report if self.readout else None}

    def export(self):
        return {'schema_version': 1, 'settings': {'seed': self.seed, 'fabric': self.cloth.fabric, 'garment': self.cloth.garment,
                    'temperature': self.cloth.iron_temperature, 'controller': self.controller, 'neural': asdict(self.config)},
                'provenance': self.circuit['provenance'], 'node_ids': [n['id'] for n in self.circuit['nodes']],
                'history': self.history, 'spikes_ms_index': self.brain.events, 'final': self.snapshot(),
                'readout_weights': None if self.readout is None else {
                    'mean': self.readout.mean.tolist(), 'scale': self.readout.scale.tolist(),
                    'weights': self.readout.weights.tolist(), 'bias': self.readout.bias.tolist(),
                    'report': self.readout.report}}

def neural_trial(circuit, config, rate, seed=42, duration=1000):
    brain = Brain(circuit, config, seed)
    rates = np.array([rate if circuit['nodes'][i]['cell_type'] == 'DNa02' else 0 for i in brain.inputs])
    brain.advance(rates, duration)
    return {'stimulus_hz': rate, 'seed': seed, 'motor_rates': (brain.total_spikes[brain.motors] / (duration / 1000)).tolist(),
            'spikes': brain.events, 'diagnostics': brain.diagnostics()}

def run_report():
    circuit = load_circuit()
    start = time.perf_counter()
    report = {'provenance': circuit['provenance'], 'default_neural': asdict(NeuralConfig()), 'neural_sweep': [], 'controls': []}
    for cutoff in [3, 5, 10]:
        for scale in [1., 2., 4.]:
            for rate in [0, 75, 150, 250]:
                for seed in [42, 43, 44]:
                    result = neural_trial(circuit, NeuralConfig(cutoff=cutoff, weight_scale=scale), rate, seed)
                    result.pop('spikes')
                    report['neural_sweep'].append({'cutoff': cutoff, 'weight_scale': scale, **result})
    for controller in ['real', 'shuffled', 'zero', 'random', 'expert']:
        for fabric in ['cotton', 'silk', 'wool']:
            for seed in [42, 43, 44]:
                session = Session(circuit, seed=seed, fabric=fabric, controller=controller)
                session.brain.record = False
                session.step(600)
                report['controls'].append({'controller': controller, 'fabric': fabric, 'seed': seed, 'duration_s': 12,
                                           **session.cloth.metrics(), 'diagnostics': session.brain.diagnostics(),
                                           'readout': session.readout.report if session.readout else None})
    report['wall_seconds'] = time.perf_counter() - start
    output = ROOT / 'outputs'
    output.mkdir(exist_ok=True)
    (output / 'benchmark.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'Wrote benchmark in {report["wall_seconds"]:.1f}s', flush=True)

if __name__ == '__main__':
    run_report()
