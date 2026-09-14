"""Only the linear motor readout is fitted; anatomical weights stay frozen."""
from dataclasses import asdict
import hashlib
import json
import numpy as np
from .data import DATA
from .neural import Brain, NeuralConfig
from .cloth import Cloth

TRAIN_VERSION = 1

def key(circuit, config, wiring):
    payload = json.dumps({'v': TRAIN_VERSION, 'neural': asdict(config), 'wiring': wiring,
                          'circuit': circuit}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:20]

class Readout:
    def __init__(self, mean, scale, weights, bias, report):
        self.mean, self.scale, self.weights, self.bias, self.report = mean, scale, weights, bias, report

    def predict(self, trace):
        return np.clip(((trace - self.mean) / self.scale) @ self.weights + self.bias, [-1, -1, 0, 0], [1, 1, 1, 1])

def train(circuit, config=None, wiring='real', samples=420):
    config = config or NeuralConfig()
    path = DATA / 'models' / (key(circuit, config, wiring) + '.npz')
    bundled = DATA / 'pretrained' / path.name
    cached = path if path.exists() else bundled
    if cached.exists():
        with np.load(cached, allow_pickle=False) as d:
            return Readout(d['mean'], d['scale'], d['weights'], d['bias'], json.loads(str(d['report'])))
    print(f'Fitting {wiring} motor readout ({samples} feature probes)', flush=True)
    rng = np.random.default_rng(731)
    brain = Brain(circuit, config, seed=991, wiring=wiring)
    brain.record = False
    x, y, split = [], [], []
    for i in range(samples):
        dx, dy = rng.uniform(-1, 1, 2)
        hot, steam, on_cloth = rng.random(), float(rng.random() < .33), float(rng.random() < .9)
        feature = np.array([max(dx, 0), max(-dx, 0), max(dy, 0), max(-dy, 0), 1 - hot, hot, steam, on_cloth])
        for t in range(10):
            brain.advance(feature * config.stimulus_hz)
            # 100 ms washout after each change; collect individual traces as at inference.
            if t >= 5:
                x.append(brain.trace[brain.motors].copy())
                y.append(Cloth.expert(feature))
                split.append(i < int(samples * .8))
    x, y, split = np.array(x), np.array(y), np.array(split)
    mean, scale = x[split].mean(0), x[split].std(0)
    scale = np.maximum(scale, 1.)
    z = (x - mean) / scale
    bias = y[split].mean(0)
    candidates = []
    for alpha in [1., 10., 100., 1000.]:
        weights = np.linalg.solve(z[split].T @ z[split] + np.eye(z.shape[1]) * alpha, z[split].T @ (y[split] - bias))
        mse = float(np.mean((z[~split] @ weights + bias - y[~split]) ** 2))
        candidates.append((mse, alpha, weights))
    mse, alpha, weights = min(candidates, key=lambda item: item[0])
    report = {'training_seed': 731, 'neural_seed': 991, 'probes': samples, 'washout_ms': 100,
              'alpha': alpha, 'validation_mse': mse, 'constant_validation_mse': float(np.mean((y[~split] - bias) ** 2)),
              'active_motor_features': int((x.std(0) > 0).sum()),
              'method': 'Ridge on 64 filtered motor spike traces; synthetic feature probes and scripted action labels; final 20% of probes select alpha. This is validation, not a held-out task benchmark.'}
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, mean=mean, scale=scale, weights=weights, bias=bias, report=json.dumps(report))
    print(json.dumps(report), flush=True)
    return Readout(mean, scale, weights, bias, report)
