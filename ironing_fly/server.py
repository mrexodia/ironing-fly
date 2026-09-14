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
    return NeuralConfig(**{f.name: getattr(settings, f.name) for f in fields(NeuralConfig) if hasattr(settings, f.name)})

@app.get('/api/circuit')
def get_circuit():
    return circuit

@app.get('/api/health')
def health():
    return {'status': 'ok', 'neurons': len(circuit['nodes'])}

@app.post('/api/session')
def create(settings: Settings):
    with lock:
        if len(sessions) >= 16:
            sessions.pop(next(iter(sessions)))
        session = Session(circuit, neural(settings), settings.seed, settings.fabric, settings.garment, settings.temperature, settings.controller)
        sid = uuid.uuid4().hex
        sessions[sid] = session
        return {'id': sid, **session.snapshot()}

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
