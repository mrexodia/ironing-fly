"""Versioned adapter comparison on seeds not used for tuning (61, 62, 63)."""
import json
from .data import DATA
from .neural import NeuralConfig
from .full_session import FullSession

def run(seconds=12, backend='auto'):
    rows=[]
    cases=[(condition,seed,'cotton',170) for seed in [61,62,63] for condition in ['before','real']]
    cases += [(condition,61,'cotton',170) for condition in ['shuffled','zero','ablated','silent']]
    cases += [('real',61,'silk',110),('real',61,'wool',150)]
    for condition,seed,fabric,temperature in cases:
        config=NeuralConfig(weight_scale=2,stimulus_hz=0 if condition=='silent' else 150)
        session=FullSession(config,seed,fabric,temperature=temperature,
            controller=condition if condition in ['real','shuffled','zero'] else 'real',backend=backend,
            ablate_outputs=condition=='ablated',decoder_version=1 if condition=='before' else 2)
        for _ in range(round(seconds/.02/25)):
            session.step(25)
        row={'condition':condition,'seed':seed,'fabric':fabric,'temperature':temperature,
             'decoder_version':session.decoder.version,'seconds':seconds,
             **session.cloth.metrics(),**session.brain.diagnostics()}
        rows.append(row)
        print(json.dumps(row),flush=True)
    result={'seconds':seconds,'settings':{'weight_scale':2,'stimulus_hz':150,'cutoff':5,'background_hz':0,'garment':'shirt'},
            'scope':'Adapter gains selected on cotton seed 42. Paired old/new cotton evaluation on untouched seeds 61/62/63. Other controls and materials use seed 61 only. No biological advantage or learned behavior claimed.',
            'provenance':session.graph.provenance,'rows':rows}
    (DATA/'ironing_improvement.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    run()
