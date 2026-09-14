import json
import numpy as np
import pytest
from fastapi.testclient import TestClient
from ironing_fly.data import load_circuit
from ironing_fly.neural import Brain, NeuralConfig
from ironing_fly.cloth import Cloth

@pytest.fixture(scope='module')
def circuit():
    return load_circuit()

def tiny(sign='acetylcholine'):
    return {'nodes': [{'neurotransmitter_predicted': sign, 'neurotransmitter_verified': ''} for _ in range(2)],
            'inputs': [0], 'motors': [1], 'edges': [[0, 1, 100]]}

def test_synaptic_delay_and_sign():
    brain = Brain(tiny(), NeuralConfig(weight_scale=1))
    brain.v[0] = -40
    brain.advance([0], .5)
    assert brain.total_spikes[0] == 1
    assert brain.g[1] == 0
    brain.advance([0], 1.5)
    assert brain.g[1] == 0
    brain.advance([0], .5)
    assert brain.g[1] == pytest.approx(27.5)
    assert brain.v[1] > -52
    inhibitory = Brain(tiny('gaba'))
    inhibitory.v[0] = -40
    inhibitory.advance([0], 3)
    assert inhibitory.v[1] < -52

def test_passive_membrane_matches_analytic_solution():
    brain = Brain(tiny())
    brain.v[1] = -48
    brain.advance([0], 10)
    assert brain.v[1] == pytest.approx(-52 + 4 * np.exp(-10/20))

def test_ids_and_motor_reachability(circuit):
    ids = [n['id'] for n in circuit['nodes']]
    assert len(ids) == len(set(ids)) == 232
    assert all(isinstance(i,str) and str(int(i)) == i and int(i) > 2**53 for i in ids)
    assert all(circuit['nodes'][i]['super_class']=='motor' for i in circuit['motors'])
    visited = set(circuit['inputs'])
    for _ in range(2):
        visited |= {b for a,b,n in circuit['edges'] if a in visited and n >= 5}
    assert set(circuit['motors']) <= visited
    assert any(a >= 8 and b >= 8 for a,b,_ in circuit['edges'])

def test_silence_and_seeded_chunk_invariance(circuit):
    silent = Brain(circuit)
    silent.advance(np.zeros(8), 100)
    assert silent.total_spikes.sum() == 0
    one, chunks = Brain(circuit), Brain(circuit)
    one.advance(np.ones(8)*150, 200)
    for _ in range(10):
        chunks.advance(np.ones(8)*150, 20)
    assert one.events == chunks.events
    np.testing.assert_array_equal(one.v, chunks.v)
    assert one.total_spikes[one.motors].sum() > 0

def test_controls_do_not_change_anatomical_source(circuit):
    original = json.dumps(circuit)
    real, shuffled, zero = [Brain(circuit, wiring=w) for w in ['real','shuffled','zero']]
    assert (real.matrix != shuffled.matrix).nnz > 0
    assert zero.matrix.count_nonzero() == 0
    np.testing.assert_allclose(real.matrix.sum(axis=0), shuffled.matrix.sum(axis=0))
    assert json.dumps(circuit) == original

def test_no_pressure_no_flattening_and_silk_burn():
    lifted = Cloth(fabric='silk', temperature=240)
    hot = Cloth(fabric='silk', temperature=240)
    for _ in range(500):
        lifted.step([0,0,0,0])
        hot.step([0,0,1,0])
    assert lifted.metrics()['smooth_percent'] == 0
    assert lifted.heat.max() == 22
    assert hot.metrics()['smooth_percent'] > 0
    assert hot.metrics()['scorch_percent'] > 0
    assert np.all(hot.heat[~hot.mask] == 22)
    assert 0 <= hot.scorch.min() <= hot.scorch.max() <= 1

def test_wool_steam_changes_smoothing():
    dry, wet = Cloth(fabric='wool'), Cloth(fabric='wool')
    for _ in range(200):
        dry.step([0,0,1,0]); wet.step([0,0,1,1])
    assert wet.metrics()['smooth_percent'] > dry.metrics()['smooth_percent'] > 0

def test_garments_reproducible():
    for garment in ['shirt','trousers','patch']:
        a,b = Cloth(seed=17,garment=garment),Cloth(seed=17,garment=garment)
        np.testing.assert_array_equal(a.wrinkle,b.wrinkle)
        assert a.mask.sum() > 100

def test_api_roundtrip_and_validation():
    from ironing_fly.server import app
    with TestClient(app) as client:
        assert client.get('/api/health').status_code == 200
        assert client.post('/api/session',json={'stimulus_hz':-1}).status_code == 422
        assert client.post('/api/session',json={'fabric':'linen'}).status_code == 422
        sid = client.post('/api/session',json={'controller':'manual','fabric':'silk','temperature':210}).json()['id']
        assert client.post(f'/api/session/{sid}/step',json={'ticks':0}).status_code == 422
        assert client.post(f'/api/session/{sid}/step',json={'manual':[1,2]}).status_code == 422
        result = client.post(f'/api/session/{sid}/step',json={'ticks':25,'manual':[1,0,1,0]}).json()
        assert result['cloth']['time'] == .5
        assert result['cloth']['iron'][0] > .5
        export = client.get(f'/api/session/{sid}/export')
        assert 'attachment' in export.headers['content-disposition']
        data = export.json()
        assert len(data['history']) == 25
        assert data['settings']['temperature'] == 210
        assert all(isinstance(i,str) for i in data['node_ids'])
        from ironing_fly.replay import replay
        assert replay(data)['verified_ticks'] == 25
        trial = client.post('/api/neural-trial',json={'stimulus_hz':150}).json()
        assert trial['baseline']['diagnostics']['silent']
        assert trial['stimulated']['diagnostics']['motor_mean_hz'] > 0
        assert client.get('/api/session/missing/export').status_code == 404
