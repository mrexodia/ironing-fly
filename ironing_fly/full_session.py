from dataclasses import asdict
from bisect import bisect_left
import numpy as np
from .cloth import Cloth
from .connectome import load_full,display_circuit
from .full_neural import FullBrain
from .senses import Senses,MotorDecoder

class FullSession:
    def __init__(self,config,seed=42,fabric='cotton',garment='shirt',temperature=170,controller='real',backend='auto',ablate_outputs=False,decoder_version=3):
        if controller not in ['real','shuffled','zero']:
            raise ValueError('Full connectome supports real, shuffled and zero controls')
        self.graph=load_full()
        self.config,self.seed,self.controller=config,seed,controller
        self.brain=FullBrain(self.graph,config,seed,controller,backend,ablate_outputs)
        self.cloth=Cloth(seed,fabric,garment,temperature,select_target=False)
        self.heading=-np.pi/2
        self.senses=Senses(2 if decoder_version == 3 else 1)
        self.decoder=MotorDecoder(decoder_version)
        self.history=[]
        self.events=[]
        self.action=np.zeros(4)
        self.decoded={}
        self.display=display_circuit(self.graph)
        self.display_index={global_id:i for i,global_id in enumerate(self.graph.groups['display'])}
        self.sample_display=[self.brain.sample_index[i] for i in self.graph.groups['display']]

    def step(self,ticks=5,manual=None):
        for _ in range(ticks):
            channels=self.senses.observe(self.cloth,self.heading,self.config.stimulus_hz)
            rates=self.brain.encode_rates(channels)
            self.brain.advance(rates)
            populations=self.brain.population_rates()
            self.action,self.heading,self.decoded=self.decoder.decode(populations,self.heading)
            self.cloth.step(self.action)
            self.events.extend((t,self.display_index[i]) for t,i in self.brain.last_events if i in self.display_index)
            self.history.append({'time_s':round(self.cloth.time,3),'action':self.action.tolist(),
                'heading_radians':self.heading,'channels_hz':channels,'populations_hz':populations,**self.cloth.metrics()})
        return self.snapshot()

    def snapshot(self):
        cloth=self.cloth.snapshot()
        cloth['target_visible']=False
        cloth['target']=self.cloth.position.tolist()
        cloth['heading_radians']=self.heading
        start=bisect_left(self.events,(self.brain.time_ms-1000,-1))
        return {'cloth':cloth,'controller':self.controller,'engine':'full','action':self.action.tolist(),'readout':None,
                'neural':{'time_ms':self.brain.time_ms,'spikes':self.events[start:],
                          'rates':self.brain.sample_rates[self.sample_display].round(2).tolist(),
                          'diagnostics':self.brain.diagnostics(),'sampled':True},
                'senses':self.senses.last,'populations_hz':self.brain.population_rates(),'decoder':self.decoded,
                'model':{'label':'Full eligible BANC connectome','decoder_version':self.decoder.version,'neurons':self.graph.n,'edges':self.brain.edge_count,
                         'display_neurons':len(self.display_index),'trained_readout':False,
                         'observation':'Local 16×8 retina + contact + temperature; no global wrinkle target.'}}

    def export(self):
        return {'schema_version':2,'settings':{'engine':'full','seed':self.seed,'fabric':self.cloth.fabric,'garment':self.cloth.garment,
                    'temperature':self.cloth.iron_temperature,'controller':self.controller,'neural':asdict(self.config),
                    'backend':self.brain.backend,'ablate_outputs':self.brain.ablate_outputs,'decoder_version':self.decoder.version,
                    'sensory_version':self.senses.version},
                'provenance':self.graph.provenance,'node_ids':[n['id'] for n in self.display['nodes']],
                'spike_recording':'Only the explicitly listed visualization sample is recorded; all eligible neurons are simulated.',
                'history':self.history,'spikes_ms_index':self.events,'final':self.snapshot(),
                'decoder':'Versioned fixed neural/tool adapter: descending yaw/drive/lift, motor pressure/steam, v2 pushing and v3 stronger pushing with shorter visual lookahead; see senses.py.'}
