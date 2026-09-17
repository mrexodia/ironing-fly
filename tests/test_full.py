import numpy as np
import pytest
from ironing_fly.connectome import Connectome
from ironing_fly.full_neural import FullBrain
from ironing_fly.neural import NeuralConfig
from ironing_fly.cloth import Cloth
from ironing_fly.senses import Senses, MotorDecoder

def graph(sign=1):
    return Connectome(
        [{'id':str(100000000000000000+i),'super_class': 'visual_projection' if i==0 else 'descending','cell_type':'LC11' if i==0 else 'DNp66','side':'left'} for i in range(3)],
        np.array([0,1],dtype=np.int32),np.array([1,2],dtype=np.int32),np.array([300,100]),np.array([sign,1,1]),
        {'LC11_left':[0],'DNp66_left':[1],'front_motor_left':[2],'display':[0,1,2]}, {'test':True})

def test_coupled_exact_passive_solution_and_delay():
    brain=FullBrain(graph(),backend='cpu')
    brain.g[2]=2
    brain.advance([0],10)
    expected=-52+2*5/(5-20)*(np.exp(-10/5)-np.exp(-10/20))
    assert brain.v[2]==pytest.approx(expected)
    for sign in [1,-1]:
        brain=FullBrain(graph(sign),backend='cpu')
        brain.v[0]=-40
        brain.advance([0],2)
        assert brain.g[1]==0
        brain.advance([0],.5)
        assert np.sign(brain.g[1])==sign
        assert np.sign(brain.v[1]+52)==sign

def test_neural_causality_disconnection_and_ablation():
    for mode,ablate in [('real',False),('zero',False),('real',True)]:
        brain=FullBrain(graph(),backend='cpu',wiring=mode,ablate_outputs=ablate)
        brain.advance([150],500)
        assert brain.total_spikes[0]>0
        action,_,_=MotorDecoder().decode(brain.population_rates(),0)
        if mode=='zero' or ablate:
            assert brain.total_spikes[1:].sum()==0
            np.testing.assert_array_equal(action,np.zeros(4))
        else:
            assert brain.total_spikes[1:].sum()>0
            assert action[0]>0

def test_calibrated_adapter_uses_motor_spikes_and_preserves_silence():
    rates={'front_motor_left':6.,'front_motor_right':6.}
    old,_,_=MotorDecoder(1).decode(rates,0)
    new,_,_=MotorDecoder(2).decode(rates,0)
    assert old[0]==0 and new[0]>0
    assert new[2]>old[2] and new[3]>old[3]
    faster,_,_=MotorDecoder(3).decode(rates,0)
    assert faster[0]>new[0] and faster[2]==new[2]
    for version in [1,2,3]:
        decoder=MotorDecoder(version)
        decoder.decode(rates,0)
        action,heading,_=decoder.decode({},.5)
        np.testing.assert_array_equal(action,np.zeros(4))
        assert heading==pytest.approx(.5)
        escape,_,_=decoder.decode({**rates,'DNp01_left':60},0)
        assert escape[2]==0

def test_coverage_counts_contact_once_without_changing_cloth_physics():
    cloth=Cloth(select_target=False)
    cloth.step([0,0,0,0])
    assert cloth.metrics()['coverage_percent']==0
    cloth.step([0,0,1,0])
    first=cloth.metrics()['coverage_percent']
    for _ in range(10): cloth.step([0,0,1,0])
    assert cloth.metrics()['coverage_percent']==first
    cloth.step([1,0,1,0],dt=.5)
    assert cloth.metrics()['coverage_percent']>first
    assert cloth.metrics()['travel']==pytest.approx(.15)

def test_cpu_chunk_invariance_and_silence():
    whole,chunks=FullBrain(graph(),backend='cpu'),FullBrain(graph(),backend='cpu')
    whole.advance([150],200)
    events=[]
    for _ in range(10):
        chunks.advance([150],20)
        events.extend(chunks.last_events)
    assert events==whole.last_events
    np.testing.assert_array_equal(whole.v,chunks.v)
    silent=FullBrain(graph(),backend='cpu')
    silent.advance([0],200)
    assert silent.network_spikes==0

@pytest.mark.parametrize('version',[1,2])
def test_local_senses_do_not_use_target_or_fabric_label(monkeypatch,version):
    def forbidden(*args): raise AssertionError('Target oracle called')
    monkeypatch.setattr(Cloth,'choose_target',forbidden)
    monkeypatch.setattr(Cloth,'features',forbidden)
    a,b=Cloth(fabric='cotton',select_target=False),Cloth(fabric='wool',select_target=False)
    left,right=Senses(version),Senses(version)
    assert left.observe(a,0,150)==right.observe(b,0,150)
    original=left.last['retina']
    a.position[0]=.8
    left.observe(a,0,150)
    assert left.last['retina']!=original
    assert left.last['channels_hz']['LLPC1_left']>0
    assert len(original)==128

def test_shorter_retina_ignores_changes_beyond_its_view():
    a,b=Cloth(select_target=False),Cloth(select_target=False)
    b.wrinkle[:,b.x[0]>.85]=1
    local_a,local_b=Senses(2),Senses(2)
    local_a.observe(a,0,150); local_b.observe(b,0,150)
    assert local_a.last['retina']==local_b.last['retina']
    far_a,far_b=Senses(1),Senses(1)
    far_a.observe(a,0,150); far_b.observe(b,0,150)
    assert far_a.last['retina']!=far_b.last['retina']

def test_full_api_and_replay_on_tiny_graph(monkeypatch):
    from fastapi.testclient import TestClient
    from ironing_fly import full_session
    from ironing_fly.server import app
    from ironing_fly.replay import replay
    monkeypatch.setattr(full_session,'load_full',graph)
    def forbidden(*args): raise AssertionError('Target oracle called')
    monkeypatch.setattr(Cloth,'choose_target',forbidden)
    with TestClient(app) as client:
        response=client.post('/api/session',json={'engine':'full','backend':'cpu'})
        assert response.status_code==200,response.text
        initial=response.json()
        assert initial['model']['neurons']==3
        assert initial['readout'] is None
        sid=initial['id']
        frame=client.post(f'/api/session/{sid}/step',json={'ticks':25}).json()
        assert frame['neural']['diagnostics']['network_spikes']>0
        assert not frame['cloth']['target_visible']
        data=client.get(f'/api/session/{sid}/export').json()
        assert replay(data)['verified_ticks']==25
        assert data['settings']['decoder_version']==3
        assert data['settings']['sensory_version']==2
        assert data['settings']['neural']['weight_scale']==2
        assert client.post('/api/session',json={'engine':'full','controller':'expert'}).status_code==422
        assert client.post('/api/neural-trial',json={'engine':'full'}).status_code==422
        assert client.post('/api/session',json={'engine':'full','decoder_version':4}).status_code==422
        for fabric,temperature in [('silk',110),('wool',150)]:
            sid=client.post('/api/session',json={'engine':'full','backend':'cpu','fabric':fabric,'decoder_version':1}).json()['id']
            client.post(f'/api/session/{sid}/step',json={'ticks':5})
            data=client.get(f'/api/session/{sid}/export').json()
            assert data['settings']['temperature']==temperature
            # Schema-2 exports made before versioning must still replay as v1.
            del data['settings']['decoder_version']
            del data['settings']['sensory_version']
            assert replay(data)['verified_ticks']==5
        sid=client.post('/api/session',json={'engine':'full','backend':'cpu','decoder_version':2}).json()['id']
        client.post(f'/api/session/{sid}/step',json={'ticks':5})
        data=client.get(f'/api/session/{sid}/export').json()
        del data['settings']['sensory_version']
        assert replay(data)['verified_ticks']==5

def test_gpu_matches_cpu_on_small_causal_fixture():
    pytest.importorskip('cupy')
    try:
        gpu=FullBrain(graph(),backend='cuda')
    except RuntimeError:
        pytest.skip('CUDA device unavailable')
    cpu=FullBrain(graph(),backend='cpu')
    gpu.advance([150],200)
    cpu.advance([150],200)
    assert gpu.last_events==cpu.last_events
    np.testing.assert_allclose(gpu.to_cpu(gpu.v),cpu.v,atol=2e-4)
