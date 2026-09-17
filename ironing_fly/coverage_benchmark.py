"""Paired v2/v3 evaluation; never use these seeds to choose v3 gains."""
import json
from .data import DATA
from .neural import NeuralConfig
from .full_session import FullSession

def run(backend='auto'):
    rows, extended, controls = [], [], []
    cases = [(condition,seed,'cotton',170) for seed in [81,82,83] for condition in ['before','real']]
    cases += [('shuffled',81,'cotton',170),('real',81,'silk',110),('real',81,'wool',150)]
    cases += [(condition,81,'cotton',170) for condition in ['zero','ablated','silent']]
    for condition,seed,fabric,temperature in cases:
        config = NeuralConfig(weight_scale=2,stimulus_hz=0 if condition=='silent' else 150)
        session = FullSession(config,seed,fabric,temperature=temperature,
            controller=condition if condition in ['real','shuffled','zero'] else 'real',backend=backend,
            ablate_outputs=condition=='ablated',decoder_version=2 if condition=='before' else 3)
        causal = condition in ['zero','ablated','silent']
        durations = [3] if causal else ([12,24] if seed==81 and fabric=='cotton' and condition in ['before','real'] else [12])
        for seconds in durations:
            while session.cloth.time < seconds-1e-8:
                session.step(25)
            row = {'condition':condition,'seed':seed,'fabric':fabric,'temperature':temperature,
                   'decoder_version':session.decoder.version,'seconds':seconds,
                   **session.cloth.metrics(),**session.brain.diagnostics()}
            (controls if causal else extended if seconds==24 else rows).append(row)
            print(json.dumps(row),flush=True)
    result = {'seconds':12,'evaluation_seeds':[81,82,83],'tuning_seeds':[42],
              'labels':{'before':'Calibrated push (v2)','real':'Coverage push (v3)'},
              'scope':'Paired cotton trials on new seeds 81/82/83. Extended 24-second runs, other fabrics and shuffled wiring use seed 81 only. Silent/disconnected/ablated interventions last 3 seconds. No claim of learned behavior or biological advantage.',
              'settings':{'weight_scale':2,'stimulus_hz':150,'cutoff':5,'background_hz':0,'garment':'shirt'},
              'provenance':session.graph.provenance,'rows':rows,'extended_rows':extended,'causal_controls':controls}
    (DATA/'coverage_improvement.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    run()
