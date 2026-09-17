"""Versioned full eligible BANC graph; never confused with the 232-cell demo."""
from dataclasses import dataclass
from functools import lru_cache
import json
import urllib.request
import numpy as np
import pandas as pd
from .data import DATA, BASE, FILES, digest

CACHE = DATA / 'full_banc'
VERSION = 2
VISUAL = ['LC11','LC4','LPLC1','LPLC2','LLPC1','LC12','LPC1','LC10a','LC10d']
DESCENDING = ['DNa02','DNp09','DNp01','MDN','DNp66','DNp03']

@dataclass
class Connectome:
    nodes: list
    pre: np.ndarray
    post: np.ndarray
    counts: np.ndarray
    signs: np.ndarray
    groups: dict
    provenance: dict

    @property
    def n(self):
        return len(self.nodes)

def prepare_full():
    raw = DATA / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = raw / name
        if not target.exists():
            partial = target.with_suffix('.part')
            urllib.request.urlretrieve(BASE + name, partial)
            partial.replace(target)
    print('Preparing full eligible BANC connectome', flush=True)
    meta = pd.read_feather(raw / FILES[0])
    excluded = meta.status.fillna('').str.contains('UNROOTED|TOO_SMALL|NOT_A_NEURON|TRACING_ISSUE(?!_RESOLVED)', regex=True)
    eligible = meta[(meta.proofread == 'TRUE') & ~excluded & meta.super_class.notna() & ~meta.super_class.isin(['glia','trachea','not_a_neuron'])].copy()
    eligible = eligible.sort_values('banc_888_id').reset_index(drop=True)
    assert not eligible.banc_888_id.duplicated().any()
    edge = pd.read_feather(raw / FILES[1], columns=['pre','post','count'])
    index = pd.Index(eligible.banc_888_id)
    pre, post = index.get_indexer(edge.pre), index.get_indexer(edge.post)
    keep = (pre >= 0) & (post >= 0) & (edge['count'].to_numpy() > 0)
    counts = edge['count'].to_numpy()[keep].astype(np.int32)
    pre, post = pre[keep].astype(np.int32), post[keep].astype(np.int32)
    columns = ['banc_888_id','cell_type','side','super_class','region','body_part_effector','cell_class','cell_sub_class','neurotransmitter_predicted','neurotransmitter_verified']
    nodes = eligible[columns].fillna('').rename(columns={'banc_888_id':'id'}).to_dict('records')
    mapping = {'acetylcholine':1, 'gaba':-1, 'glutamate':-1, 'histamine':-1}
    signs = np.array([mapping.get(n['neurotransmitter_verified'] or n['neurotransmitter_predicted'],0) for n in nodes], dtype=np.int8)
    groups = {}
    for cell in VISUAL + DESCENDING:
        for side in ['left','right']:
            groups[f'{cell}_{side}'] = [i for i,n in enumerate(nodes) if n['cell_type']==cell and n['side']==side]
    for side in ['left','right']:
        groups[f'contact_{side}'] = [i for i,n in enumerate(nodes) if n['super_class']=='sensory' and n['cell_type']=='SNta29' and n['side']==side]
        groups[f'thermal_{side}'] = [i for i,n in enumerate(nodes) if n['cell_class']=='thermosensory_receptor_neuron' and n['side']==side]
        groups[f'front_motor_{side}'] = [i for i,n in enumerate(nodes) if n['super_class']=='motor' and n['body_part_effector']=='front_leg' and n['side']==side]
    for cell in VISUAL + DESCENDING:
        for side in ['left','right']:
            if not groups[f'{cell}_{side}']:
                raise ValueError(f'Missing annotated population {cell}_{side}')
    # Visualizations use a fixed, named-population-rich sample, not all cells.
    rng = np.random.default_rng(2026)
    selected = {i for key, group in groups.items() for i in (group if key.startswith(('DN','MDN','front_motor')) else rng.choice(group,min(8,len(group)),replace=False).tolist())}
    sample = sorted(selected | set(rng.choice(len(nodes), 250, replace=False).tolist()))
    groups['display'] = sample
    provenance = {
        'dataset':'BANC', 'materialization':888, 'connectivity_version':'simple_v3', 'builder_version':VERSION,
        'files':[{'name':n,'url':BASE+n,'sha256':digest(raw/n),'bytes':(raw/n).stat().st_size} for n in FILES],
        'counts':{'neurons':len(nodes),'edges':len(counts),'synapses':int(counts.sum())},
        'metadata_rows':len(meta), 'selection':'All proofread neurons with an annotated neuronal superclass; exclude glia, trachea, not_a_neuron, unrooted, too-small and unresolved tracing issues. No task-based node pruning. All induced positive-count edges retained before runtime threshold. This is the full eligible graph, not every reconstructed cell.',
        'group_counts':{k:len(v) for k,v in groups.items()},
        'unknown_or_modulatory_sign_neurons':int((signs==0).sum()),
        'id_policy':'String root IDs, int32 local indices; no float ID conversion.',
        'sources':['https://github.com/sjcabs/fly_connectome_data_tutorial/blob/main/data/dataset_documentation/banc_data.md','https://www.nature.com/articles/s41586-026-10735-w'],
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE/'graph.part.npz',pre=pre,post=post,counts=counts,signs=signs)
    (CACHE/'graph.part.npz').replace(CACHE/'graph.npz')
    (CACHE/'metadata.part.json').write_text(json.dumps({'nodes':nodes,'groups':groups,'provenance':provenance},separators=(',',':')),encoding='utf-8')
    (CACHE/'metadata.part.json').replace(CACHE/'metadata.json')
    (DATA/'full_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(json.dumps(provenance['counts']), flush=True)

@lru_cache(maxsize=1)
def load_full():
    if not (CACHE/'metadata.json').exists() or not (CACHE/'graph.npz').exists():
        prepare_full()
    metadata = json.loads((CACHE/'metadata.json').read_text(encoding='utf-8'))
    if metadata['provenance']['builder_version'] != VERSION:
        prepare_full()
        metadata = json.loads((CACHE/'metadata.json').read_text(encoding='utf-8'))
    with np.load(CACHE/'graph.npz',allow_pickle=False) as g:
        return Connectome(metadata['nodes'],g['pre'],g['post'],g['counts'],g['signs'],metadata['groups'],metadata['provenance'])

def display_circuit(graph):
    ids = graph.groups['display']
    index = {i:j for j,i in enumerate(ids)}
    inputs = {i for name,group in graph.groups.items() if name.startswith(tuple(VISUAL)+('contact_','thermal_')) for i in group}
    outputs = {i for name,group in graph.groups.items() if name.startswith(tuple(DESCENDING)+('front_motor_',)) for i in group}
    keep = np.isin(graph.pre,ids)&np.isin(graph.post,ids)
    selected = np.flatnonzero(keep)
    selected = selected[np.argsort(graph.counts[selected])[-1000:]]
    return {'nodes':[graph.nodes[i] for i in ids], 'edges':[[index[int(graph.pre[i])],index[int(graph.post[i])],int(graph.counts[i])] for i in selected],
            'inputs':[j for j,i in enumerate(ids) if i in inputs],
            'motors':[j for j,i in enumerate(ids) if i in outputs],
            'provenance':graph.provenance, 'sampled':True, 'global_indices':ids}

if __name__ == '__main__':
    prepare_full()
