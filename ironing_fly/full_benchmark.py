"""Short, fixed-setting causal controls; not an ironing competence benchmark."""
import json
import numpy as np
from .data import DATA
from .neural import NeuralConfig
from .full_session import FullSession

def run(seconds=4, backend='auto'):
    rows=[]
    for condition in ['real','shuffled','zero','ablated','silent']:
        for seed in ([42,43,44] if condition in ['real','shuffled','zero'] else [42]):
            config=NeuralConfig(weight_scale=2,stimulus_hz=0 if condition=='silent' else 150)
            session=FullSession(config,seed,controller=condition if condition in ['real','shuffled','zero'] else 'real',backend=backend,ablate_outputs=condition=='ablated',decoder_version=1)
            travel=0.
            for _ in range(round(seconds/.02)):
                before=session.cloth.position.copy()
                session.step(1)
                travel+=float(np.linalg.norm(session.cloth.position-before))
            row={'condition':condition,'seed':seed,'travel':travel,**session.cloth.metrics(),**session.brain.diagnostics()}
            rows.append(row)
            print(json.dumps(row),flush=True)
    result={'seconds':seconds,'settings':{'weight_scale':2,'stimulus_hz':150,'cutoff':5,'background_hz':0,'fabric':'cotton','garment':'shirt','temperature':170},
            'scope':'Exploratory short causal controls; no claim of biological advantage or learned ironing. Ablated and silent conditions use seed 42 only.',
            'provenance':session.graph.provenance,'rows':rows}
    (DATA/'full_benchmark.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    run()
