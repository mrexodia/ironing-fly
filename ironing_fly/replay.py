"""Replay exported actions and neural inputs; verify the recorded trajectory."""
import argparse
import json
import numpy as np
from .data import load_circuit
from .cloth import Cloth
from .neural import Brain, NeuralConfig

def replay(data):
    circuit = load_circuit()
    if [n['id'] for n in circuit['nodes']] != data['node_ids']:
        raise ValueError('Export uses a different circuit')
    if circuit['provenance']['files'] != data['provenance']['files']:
        raise ValueError('Export uses different source files')
    s = data['settings']
    cloth = Cloth(s['seed'], s['fabric'], s['garment'], s['temperature'])
    brain = Brain(circuit, NeuralConfig(**s['neural']), s['seed'], s['controller'] if s['controller'] in ['real','shuffled','zero'] else 'real')
    for row in data['history']:
        brain.advance(row['input_hz'])
        cloth.features()
        cloth.step(row['action'])
        for metric in ['smooth_percent','scorch_percent','max_temperature_c','reward']:
            if not np.isclose(cloth.metrics()[metric], row[metric], rtol=1e-9, atol=1e-10):
                raise AssertionError(f'{metric} mismatch at {row["time_s"]}s')
    if [list(e) for e in brain.events] != data['spikes_ms_index']:
        raise AssertionError('Spike replay mismatch')
    return {'verified_ticks':len(data['history']), 'verified_spikes':len(brain.events), **cloth.metrics()}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify an Ironing Fly JSON export by replaying its logged actions and neural inputs')
    parser.add_argument('file')
    args = parser.parse_args()
    with open(args.file, encoding='utf-8') as f:
        print(json.dumps(replay(json.load(f)), indent=2))
