"""Replay exported actions and neural inputs; verify the recorded trajectory."""
import argparse
import json
import numpy as np
from .data import load_circuit
from .cloth import Cloth
from .neural import Brain, NeuralConfig

def replay(data):
    if data.get('schema_version') == 2:
        return replay_full(data)
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

def replay_full(data):
    """Recompute senses, neural activity AND actions on the recorded backend."""
    from .full_session import FullSession
    s = data['settings']
    session = FullSession(NeuralConfig(**s['neural']),s['seed'],s['fabric'],s['garment'],s['temperature'],s['controller'],s['backend'],s['ablate_outputs'],s.get('decoder_version',1))
    if s.get('sensory_version',1) != session.senses.version:
        raise ValueError('Export uses an incompatible sensory encoder version')
    if session.graph.provenance != data['provenance'] or [n['id'] for n in session.display['nodes']] != data['node_ids']:
        raise ValueError('Export uses a different full-connectome build')
    for row in data['history']:
        session.step(1)
        actual = session.history[-1]
        keys = ['action','heading_radians','smooth_percent','scorch_percent','max_temperature_c','reward']
        keys += [key for key in ['coverage_percent','travel'] if key in row]
        for key in keys:
            if not np.allclose(actual[key],row[key],rtol=1e-7,atol=1e-8):
                raise AssertionError(f'{key} mismatch at {row["time_s"]}s; same-backend reproducibility required')
        for key in ['channels_hz','populations_hz']:
            if actual[key].keys() != row[key].keys() or not np.allclose(list(actual[key].values()),[row[key][k] for k in actual[key]],rtol=1e-7,atol=1e-8):
                raise AssertionError(f'{key} mismatch at {row["time_s"]}s')
    if [list(e) for e in session.events] != data['spikes_ms_index']:
        raise AssertionError('Sampled-spike replay mismatch')
    return {'verified_ticks':len(session.history),'verified_sampled_spikes':len(session.events),**session.cloth.metrics()}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify an Ironing Fly JSON export by replaying its logged actions and neural inputs')
    parser.add_argument('file')
    args = parser.parse_args()
    with open(args.file, encoding='utf-8') as f:
        print(json.dumps(replay(json.load(f)), indent=2))
