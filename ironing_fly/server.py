from dataclasses import fields
from threading import RLock
from typing import Literal
import json
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field, ConfigDict
from .data import ROOT, load_circuit
from .neural import NeuralConfig
from .experiment import Session, neural_trial

app = FastAPI(title='Ironing Fly', docs_url='/api/docs')
circuit = load_circuit()
sessions = {}
lock = RLock()

class Settings(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    engine: Literal['legacy', 'full'] = 'legacy'
    backend: Literal['auto', 'cpu', 'cuda'] = 'auto'
    ablate_outputs: bool = False
    decoder_version: Literal[1,2,3] = 3
    seed: int = Field(42, ge=0, le=1000000)
    fabric: Literal['cotton', 'silk', 'wool'] = 'cotton'
    garment: Literal['shirt', 'trousers', 'patch'] = 'shirt'
    temperature: float = Field(170, ge=60, le=240)
    controller: Literal['real', 'shuffled', 'zero', 'random', 'expert', 'manual'] = 'real'
    stimulus_hz: float = Field(150, ge=0, le=300)
    weight_scale: float = Field(4, ge=0, le=8)
    cutoff: int = Field(5, ge=1, le=30)
    background_hz: float = Field(0, ge=0, le=20)

class Step(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    ticks: int = Field(5, ge=1, le=25)
    manual: list[float] | None = Field(None, min_length=4, max_length=4)

def neural(settings):
    config = NeuralConfig(**{f.name: getattr(settings, f.name) for f in fields(NeuralConfig) if hasattr(settings, f.name)})
    if settings.engine == 'full' and 'weight_scale' not in settings.model_fields_set:
        config.weight_scale = 2
    return config

@app.get('/api/full-benchmark')
def full_benchmark():
    path = ROOT / 'data' / 'coverage_improvement.json'
    return FileResponse(path) if path.exists() else {'rows': []}

@app.get('/api/circuit')
def get_circuit(engine: Literal['legacy','full'] = 'legacy'):
    if engine == 'full':
        from .connectome import load_full, display_circuit
        with lock:
            return display_circuit(load_full())
    return circuit

@app.get('/api/health')
def health():
    return {'status': 'ok', 'neurons': len(circuit['nodes'])}

@app.post('/api/session')
def create(settings: Settings):
    with lock:
        if settings.engine == 'full' and settings.controller not in ['real','shuffled','zero']:
            raise HTTPException(422, 'Full connectome supports real, shuffled and zero wiring.')
        if settings.engine == 'full' and settings.background_hz:
            raise HTTPException(422, 'Full mode uses zero background drive for reproducible sensory input streams.')
        if len(sessions) >= 16:
            sessions.pop(next(iter(sessions)))
        if settings.engine == 'full':
            from .full_session import FullSession
            try:
                temperature = settings.temperature if 'temperature' in settings.model_fields_set else {'cotton':170,'silk':110,'wool':150}[settings.fabric]
                session = FullSession(neural(settings), settings.seed, settings.fabric, settings.garment, temperature, settings.controller, settings.backend, settings.ablate_outputs, settings.decoder_version)
            except (RuntimeError, ValueError) as error:
                raise HTTPException(503, str(error)) from error
            display = session.display
        else:
            session = Session(circuit, neural(settings), settings.seed, settings.fabric, settings.garment, settings.temperature, settings.controller)
            display = circuit
        sid = uuid.uuid4().hex
        sessions[sid] = session
        return {'id': sid, 'circuit': display, **session.snapshot()}

def get_session(sid):
    if sid not in sessions:
        raise HTTPException(404, 'Session expired. Reset the experiment.')
    return sessions[sid]

@app.post('/api/session/{sid}/step')
def step(sid: str, body: Step):
    with lock:
        session = get_session(sid)
        if len(session.history) + body.ticks > 15000:
            raise HTTPException(409, 'Five-minute episode complete. Export or reset to continue.')
        return session.step(body.ticks, body.manual)

@app.get('/api/session/{sid}/export')
def export(sid: str):
    with lock:
        data = get_session(sid).export()
        return Response(json.dumps(data, allow_nan=False), media_type='application/json', headers={'Content-Disposition': 'attachment; filename="ironing-fly-experiment.json"'})

@app.post('/api/neural-trial')
def trial(settings: Settings):
    if settings.engine == 'full':
        raise HTTPException(422, 'This fitted-readout probe belongs to the 232-neuron demo. Use full-mode wiring and output-ablation controls instead.')
    config = neural(settings)
    return {'baseline': neural_trial(circuit, config, 0, settings.seed), 'stimulated': neural_trial(circuit, config, settings.stimulus_hz, settings.seed),
            'motor_ids': [circuit['nodes'][i]['id'] for i in circuit['motors']], 'settings': config.__dict__}

@app.get('/api/benchmark')
def benchmark():
    path = ROOT / 'outputs' / 'benchmark.json'
    if not path.exists():
        path = ROOT / 'data' / 'benchmark.json'
    if not path.exists():
        return {'controls': [], 'neural_sweep': [], 'status': 'Run uv run python -m ironing_fly.experiment to generate the benchmark.'}
    return FileResponse(path)
