"""Public BANC ingestion. Root IDs never pass through floating point."""
from pathlib import Path
import hashlib
import json
import urllib.request
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
BASE = 'https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/'
FILES = ['banc_888_meta.feather', 'banc_888_edgelist_simple_v3.feather']
TYPES = ['DNa02', 'DNa01', 'DNp09', 'DNp01']

def digest(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def prepare():
    raw = DATA / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = raw / name
        if not target.exists():
            print(f'Downloading {name}', flush=True)
            temporary = target.with_suffix('.part')
            urllib.request.urlretrieve(BASE + name, temporary)
            temporary.replace(target)
    print('Inspecting BANC tables', flush=True)
    meta = pd.read_feather(raw / FILES[0])
    edges = pd.read_feather(raw / FILES[1])
    assert meta.banc_888_id.notna().all() and not meta.banc_888_id.duplicated().any()
    assert edges[['pre', 'post', 'count']].notna().all().all()
    assert (edges['count'] > 0).all()
    duplicates = int(edges.duplicated(['pre', 'post']).sum())
    if duplicates:
        raise ValueError('Unexpected duplicate directed pairs; inspect upstream data')
    bad = meta.status.fillna('').str.contains('UNROOTED|TOO_SMALL|NOT_A_NEURON|TRACING_ISSUE(?!_RESOLVED)', regex=True)
    eligible = meta[(meta.proofread == 'TRUE') & ~bad & meta.super_class.isin(
        ['descending', 'ventral_nerve_cord_intrinsic', 'motor'])].copy()
    dn = eligible[(eligible.super_class == 'descending') & eligible.cell_type.isin(TYPES)].sort_values(['cell_type', 'side'])
    assert len(dn) == 8, 'Expected annotated bilateral DN pairs; inspect changed data'
    pool = set(eligible.banc_888_id)
    e = edges[edges.pre.isin(pool) & edges.post.isin(pool)]
    first = e[e.pre.isin(dn.banc_888_id) & (e['count'] >= 5)]
    ranked = first.groupby('post')['count'].sum().sort_values(ascending=False)
    interneurons = set(eligible[eligible.super_class == 'ventral_nerve_cord_intrinsic'].banc_888_id)
    intermediate = [i for i in ranked.index if i in interneurons][:160]
    outputs = set(eligible[(eligible.super_class == 'motor') & eligible.cell_type.notna() & (eligible.region == 'ventral_nerve_cord')].banc_888_id)
    motor_edges = e[e.pre.isin(set(dn.banc_888_id) | set(intermediate)) & e.post.isin(outputs) & (e['count'] >= 5)]
    motors = motor_edges.groupby('post')['count'].sum().sort_values(ascending=False).head(64).index.tolist()
    assert motors, 'No motor pathways found'
    ids = dn.banc_888_id.tolist() + sorted(set(intermediate) - set(dn.banc_888_id)) + sorted(motors)
    selected = eligible.set_index('banc_888_id').loc[ids].reset_index()
    selected_edges = e[e.pre.isin(ids) & e.post.isin(ids)].copy()
    index = {root: i for i, root in enumerate(ids)}
    columns = ['banc_888_id', 'cell_type', 'side', 'super_class', 'region', 'body_part_effector', 'neurotransmitter_predicted', 'neurotransmitter_verified', 'status']
    nodes = selected[columns].fillna('').to_dict('records')
    for node in nodes:
        node['id'] = node.pop('banc_888_id')
    links = [[index[r.pre], index[r.post], int(r.count)] for r in selected_edges.itertuples()]
    circuit = {'nodes': nodes, 'edges': links, 'inputs': list(range(len(dn))), 'motors': [index[i] for i in sorted(motors)]}
    provenance = {
        'dataset': 'BANC', 'materialization': 888, 'connectivity_version': 'simple_v3',
        'files': [{'name': name, 'url': BASE + name, 'sha256': digest(raw / name), 'bytes': (raw / name).stat().st_size} for name in FILES],
        'metadata_rows': len(meta), 'edge_rows': len(edges), 'duplicate_pairs': duplicates,
        'metadata_schema': {c: str(t) for c, t in meta.dtypes.items()},
        'edge_schema': {c: str(t) for c, t in edges.dtypes.items()},
        'missing_annotations': {c: int(meta[c].isna().sum()) for c in ['cell_type', 'super_class', 'neurotransmitter_predicted']},
        'selection': 'Proofread neurons; exclude unresolved tracing issues, unrooted, too-small and non-neurons. Eight annotated DNa01/DNa02/DNp01/DNp09 DNs; strongest 160 direct VNC interneuron targets at >=5 synapses; strongest 64 identified VNC motor targets reachable in one or two hops at >=5. Retain ALL induced edges for adjustable filtering. Omit all external input and all other neurons.',
        'id_policy': 'Root IDs are strings throughout; array indices are local only.',
        'counts': {'neurons': len(nodes), 'edges': len(links), 'synapses': sum(r[2] for r in links), 'inputs': len(dn), 'motors': len(motors)},
        'nt_counts': selected.neurotransmitter_predicted.fillna('unknown').value_counts().to_dict(),
        'sources': ['https://github.com/sjcabs/fly_connectome_data_tutorial/blob/main/data/dataset_documentation/banc_data.md', 'https://www.nature.com/articles/s41586-026-10735-w', 'https://github.com/philshiu/Drosophila_brain_model/blob/main/model.py'],
        'attribution': 'BANC: Bates, Phelps, Kim, Yang et al., Nature (2026). Compiled tables: S. J. C. Barnes / BANC tutorial. See linked sources for data terms.',
    }
    circuit['provenance'] = provenance
    (DATA / 'circuit.json').write_text(json.dumps(circuit, separators=(',', ':')), encoding='utf-8')
    (DATA / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print(json.dumps(provenance['counts']), flush=True)
    return circuit

def load_circuit():
    path = DATA / 'circuit.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else prepare()

if __name__ == '__main__':
    prepare()
