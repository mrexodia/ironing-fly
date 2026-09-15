# Ironing Fly

A real **232-neuron BANC v888 circuit** drives a virtual iron through a trained linear readout. Explore cotton, silk and wool; T-shirts, trousers and cloth patches; stimulation strength; and real, shuffled, zero-connection, random, scripted and human controllers.

This is the smallest complete ironing experiment from the project docs. It uses a selected female BANC circuit, **not the full MaleCNS nervous system**. The cloth is a nearly flat height-field toy, not MuJoCo, a deformable garment solver, or a fly body. The fly did not learn to iron: only the external readout is fitted.

## Run locally

Install [uv](https://docs.astral.sh/uv/) and Node.js 22.13 or newer, then run from this folder:

```powershell
uv run python launch.py
```

Open **http://127.0.0.1:5173/**. The launcher installs missing frontend dependencies, starts the Python API and interface, and stops both on Ctrl+C. Ports 8000 and 5173 must be free. The lockfiles pin dependencies; `uv` supplies Python 3.12. The prepared real circuit, default trained readouts and benchmark are included, so no account, GPU or manual data preparation is needed.

Press **Run experiment**. Pause or export at any time. Change a setting, then **Apply settings & reset**. Changes to neural settings fit and cache a new readout, which can take tens of seconds; fabric, temperature, garment and seed changes reuse it. The same seed and settings reproduce the episode. Each session is limited to five simulated minutes.

The default **3D scene** shows a little fly in an apron pushing an iron over a padded ironing board. Drag to orbit, scroll/pinch to zoom, or use the camera buttons. The iron position, garment mask, raised wrinkles, temperature colors and scorch come from the existing 2D simulation. Fly limbs and wings are illustrative animation. Switch to **2D map** for the original overhead view; browsers without WebGL automatically use that view. Switching views or moving the camera does not reset or advance the experiment.

**Human control:** select it, apply, run, then use the on-screen arrows or keyboard arrows with focus outside a form control. Toggle pressure and steam separately. **Compare DNa02 with baseline** runs a separate one-second neural experiment at the selected neural settings. Export that comparison or the complete ironing episode as JSON.

## Reproduce and verify

```powershell
uv run pytest -q
uv run python -m ironing_fly.experiment
uv run python -m ironing_fly.replay path/to/ironing-fly-experiment.json
cd web
npm run lint
npm exec -- tsc --noEmit
npm run build
```

`experiment` runs 108 DNa02 trials (three thresholds × three weight scales × four input rates × three seeds) and 45 ironing trials (five controllers × three fabrics × three seeds). It writes `outputs/benchmark.json`; the UI uses that file if present, otherwise the included `data/benchmark.json`. All ironing comparisons use 12 seconds, a T-shirt and default neural/temperature settings. Their numbers do not change when you adjust live settings, except the fabric row being displayed.

Replay verifies the **logged actions and neural inputs**, cloth metrics and spike times; it does not retrain a controller. Exports include settings, source hashes, lossless IDs, per-tick inputs/actions, all spike times, final fields and fitted readout coefficients. Default API settings are in [experiments/default.json](experiments/default.json).

## Data and model

- `data/circuit.json`: 232 annotated neurons, 3,788 directed connections, 59,959 synapses; eight descending inputs, 160 VNC intermediates and 64 identified motor outputs. All induced recurrent connections are retained before the adjustable count threshold.
- `data/provenance.json`: exact sources, SHA-256 hashes, schemas, row counts, missing annotations and selection rules. The current downloads contain 188,508 metadata rows and 13,620,865 edges; these differ from example counts in the guide. Non-neurons are excluded. Root IDs stay strings, including in JavaScript.
- `uv run python -m ironing_fly.data`: downloads matching public v888 metadata and simple-v3 aggregated edges (about 398 MiB combined), caches them in ignored `data/raw/`, inspects them and regenerates the selected circuit. No CAVE login is needed. The v3 detector's **synapse-size** filter is not a connection-count cutoff.
- CPU NumPy/SciPy LIF: 0.5 ms neural step, 20 ms membrane constant, 5 ms synaptic constant, 2 ms delay, 2.5 ms refractory, −52 mV rest/reset and −45 mV threshold. Synapse count × 0.275 mV × configurable scale; default scale 4 is an exploratory choice. Exponential leak with step-held current is an approximation to the coupled equations, not an exact reproduction of Brian2/Shiu.
- Acetylcholine is excitatory; GABA, glutamate and histamine inhibitory; unknown and modulatory transmitters have zero fast effect. This is an assumed mapping, not receptor physiology. Neural constants and transmitter handling are configurable in `NeuralConfig`.
- Eight engineered observation channels stimulate the annotated DN pairs. The controller sees wrinkle-target displacement, local heat risk, wool and cloth contact. This is not fly vision or biologically meaningful DN stimulation. A ridge readout of 64 motor spike traces (100 ms filter) alone predicts movement, pressure and steam. The connectome remains frozen.
- The near-flat cloth has heuristic temperature diffusion, local pressure smoothing, irreversible scorch, garment masks and a steam effect for wool. Fabric thresholds are fictional parameters, not care recommendations. Motor firing is not evidence of walking, flight or tool use.

## Results and scope

Across three cotton seeds, real wiring removed **17.96%** of wrinkles, shuffled wiring **23.37%**, zero connections **11.59%**, random actions **11.71%**, and the expert **34.39%** in 12 seconds. This small benchmark provides **no advantage for biological wiring**. Silk can scorch; both smoothing and damage are shown.

See [experiment report](docs/experiment-report.md) for results and validation, [implementation decisions](docs/implementation.md) for model boundaries and CyberFly observations, and the original files under `docs/` for the broader full-brain/physics plan. Full CNS, GPU kernels, anatomical meshes, fly-body physics and dopamine plasticity remain later milestones.

The interface uses the Sites starter with a local Python backend. This version is local-only; a hosted Worker cannot run this Python process. Production build validation is included, but deploying only the frontend would not deploy the experiment.

## Sources

- [BANC data schemas and public downloads](https://github.com/sjcabs/fly_connectome_data_tutorial/blob/main/data/dataset_documentation/banc_data.md)
- [BANC: Bates, Phelps, Kim, Yang et al., Nature 2026](https://www.nature.com/articles/s41586-026-10735-w)
- [Shiu et al., Nature 2024](https://www.nature.com/articles/s41586-024-07763-9) and [original model](https://github.com/philshiu/Drosophila_brain_model/blob/main/model.py)
- [CyberFly / fly-brain-spectacles](https://github.com/PtPavloTkachenko/fly-brain-spectacles), particularly [its documented engineered behavior](https://github.com/PtPavloTkachenko/fly-brain-spectacles/blob/main/docs/DECISIONS.md). Reviewed as an architectural reference; no code or neuron IDs were copied.

Credit the BANC authors and compiled-data maintainers when using this circuit. Source data retain their original terms and attribution requirements.
