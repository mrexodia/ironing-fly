# Ironing Fly

A cute 3D fly operates a virtual iron using a **121,992-neuron BANC v888 connectome simulation**. Local visual, contact and temperature inputs stimulate annotated populations. Fixed neural output equations drive the iron; the new default mode has **no global wrinkle-target finder, trained readout or automatic forward motion**. The earlier 232-neuron trained-readout demo remains selectable.

This uses the full **eligible, proofread female BANC graph**, not every reconstruction and not the MaleCNS dataset used by CyberFly. Connectivity is anatomical; physiology, sensory encoding and the neural-to-tool adapter are assumed. The cloth remains a nearly flat 2D toy beneath the 3D scene. The fly has not learned to iron. The default Coverage push profile combines leg-motor-driven pushing with a shorter local visual lookahead. The earlier profiles remain selectable. See [full-connectome model and results](docs/full-connectome.md).

## Run locally

Install [uv](https://docs.astral.sh/uv/) and Node.js 22.13 or newer, then run from this folder:

```powershell
uv run --extra gpu python launch.py
```

Open **http://127.0.0.1:5173/**. The launcher installs missing frontend dependencies, starts the Python API and interface, and stops both on Ctrl+C. Ports 8000 and 5173 must be free. The lockfiles pin dependencies; `uv` supplies Python 3.12. The GPU extra uses NVIDIA CUDA and is recommended for full mode. Without an NVIDIA GPU, use `uv run python launch.py` for a slower CPU fallback. The first full-mode session downloads about 398 MiB of public BANC files and builds an ignored cache if missing; the files are already cached in this workspace. No account is required. Full mode runs around 0.4 simulated seconds per wall second on this RTX 3090. The 232-neuron mode needs no data download or GPU.

Press **Run experiment**. The default **Coverage push** profile uses stronger neural-driven pushing and a 0.25-board-width visual lookahead. Select **Calibrated push** (v2) or **Original adapter** (v1) to compare. The elapsed-time card also reports the percentage of cloth reached with pressure. Choosing a fabric in full mode applies an adjustable toy-model temperature preset: cotton 170°C, silk 110°C, wool 150°C. These are simulation settings, not garment-care advice. Pause or export at any time. Change a setting, then **Apply settings & reset**. Full-mode changes rebuild the sparse model without fitting. In the 232-neuron demo, new neural settings fit and cache a readout. Reproduction requires the same seed, settings, data, model version and backend; CPU and GPU spikes are not guaranteed identical. Each session is limited to five simulated minutes.

The default **3D scene** shows a little fly in an apron pushing an iron over a padded ironing board. Drag to orbit, scroll/pinch to zoom, or use the camera buttons. The iron position, garment mask, raised wrinkles, temperature colors and scorch come from the existing 2D simulation. Fly limbs and wings are illustrative animation. Switch to **2D map** for the original overhead view; browsers without WebGL automatically use that view. Switching views or moving the camera does not reset or advance the experiment.

**Legacy demo only:** select the 232-neuron model to access human control and the DNa02 probe. For human control, select it, apply, run, then use the on-screen arrows or keyboard arrows with focus outside a form control. Toggle pressure and steam separately. **Compare DNa02 with baseline** runs a separate one-second neural experiment at the selected neural settings. Export that comparison or the complete ironing episode as JSON.

## Reproduce and verify

```powershell
uv run --extra gpu pytest -q
uv run --extra gpu python -m ironing_fly.coverage_benchmark
uv run --extra gpu python -m ironing_fly.improvement_benchmark
uv run --extra gpu python -m ironing_fly.full_benchmark
uv run python -m ironing_fly.experiment
uv run --extra gpu python -m ironing_fly.replay path/to/ironing-fly-experiment.json
cd web
npm run lint
npm exec -- tsc --noEmit
npm run build
```

`coverage_benchmark` compares v2/v3 on new cotton seeds 81/82/83 over 12 seconds, extends seed 81 to 24 seconds, checks silk/wool and shuffled wiring at seed 81, and records three-second causal controls separately. The interface displays its `data/coverage_improvement.json`. V3 gains were selected from five candidates on tuning seed 42.

The historical `improvement_benchmark` compares the original and calibrated adapters over 12 seconds on cotton seeds 61/62/63, which were not used to choose the gains. It also runs shuffled/disconnected/ablated/silent controls and silk/wool checks at seed 61. Its results remain in `data/ironing_improvement.json`.

`full_benchmark` preserves the version-1 four-second cotton-shirt runs: real, shuffled and disconnected wiring across seeds 42/43/44, plus output ablation and zero sensory input at seed 42. It writes the historical `data/full_benchmark.json`.

The legacy `experiment` runs 108 DNa02 trials (three thresholds × three weight scales × four input rates × three seeds) and 45 ironing trials (five controllers × three fabrics × three seeds). It writes `outputs/benchmark.json`; the UI uses that file if present, otherwise the included `data/benchmark.json`. All ironing comparisons use 12 seconds, a T-shirt and default neural/temperature settings. Their numbers do not change when you adjust live settings, except the fabric row being displayed.

Full-mode schema-2 exports now record `decoder_version` (3 by default) and `sensory_version` (2 in the new profile); older exports without that field retain version-1 replay. Replay recomputes local senses, neural activity, actions and cloth metrics on the recorded backend. It verifies spikes for the explicit **573-cell display sample**; all 121,992 neurons are simulated, but full-population spike times are not exported. Exports include settings, hashes, sample IDs, inputs, named output rates, actions and final fields. Legacy schema-1 replay verifies logged inputs/actions, all 232 spike trains and cloth metrics without refitting. [Legacy defaults](experiments/default.json) remain compatible; new full-mode API sessions default to weight scale 2.

## Full connectome

- 121,992 eligible neurons; 10,293,444 induced positive-count edges representing 32,758,013 synapses before runtime filtering.
- At the default cutoff of 5 synapses: 1,495,993 edges, of which 1,360,624 have nonzero assumed fast weights.
- NumPy/SciPy CPU or CuPy CUDA sparse LIF with exact passive coupled exponential integration between discrete events. No change to anatomical weights through training.
- `data/full_provenance.json` records source hashes, eligibility and group counts. `uv run --extra gpu python -m ironing_fly.connectome` rebuilds the ignored cache.
- The interface shows the local 16 × 8 image, bilateral descending/motor rates, backend speed and real/disconnected/shuffled/output-ablation controls.

## Legacy 232-neuron model

- `data/circuit.json`: 232 annotated neurons, 3,788 directed connections, 59,959 synapses; eight descending inputs, 160 VNC intermediates and 64 identified motor outputs. All induced recurrent connections are retained before the adjustable count threshold.
- `data/provenance.json`: exact sources, SHA-256 hashes, schemas, row counts, missing annotations and selection rules. The current downloads contain 188,508 metadata rows and 13,620,865 edges; these differ from example counts in the guide. Non-neurons are excluded. Root IDs stay strings, including in JavaScript.
- `uv run python -m ironing_fly.data`: downloads matching public v888 metadata and simple-v3 aggregated edges (about 398 MiB combined), caches them in ignored `data/raw/`, inspects them and regenerates the selected circuit. No CAVE login is needed. The v3 detector's **synapse-size** filter is not a connection-count cutoff.
- CPU NumPy/SciPy LIF: 0.5 ms neural step, 20 ms membrane constant, 5 ms synaptic constant, 2 ms delay, 2.5 ms refractory, −52 mV rest/reset and −45 mV threshold. Synapse count × 0.275 mV × configurable scale; default scale 4 is an exploratory choice. Exponential leak with step-held current is an approximation to the coupled equations, not an exact reproduction of Brian2/Shiu.
- Acetylcholine is excitatory; GABA, glutamate and histamine inhibitory; unknown and modulatory transmitters have zero fast effect. This is an assumed mapping, not receptor physiology. Neural constants and transmitter handling are configurable in `NeuralConfig`.
- Eight engineered observation channels stimulate the annotated DN pairs. The controller sees wrinkle-target displacement, local heat risk, wool and cloth contact. This is not fly vision or biologically meaningful DN stimulation. A ridge readout of 64 motor spike traces (100 ms filter) alone predicts movement, pressure and steam. The connectome remains frozen.
- The near-flat cloth has heuristic temperature diffusion, local pressure smoothing, irreversible scorch, garment masks and a steam effect for wool. Fabric thresholds are fictional parameters, not care recommendations. Motor firing is not evidence of walking, flight or tool use.

## Results and scope

The latest paired evaluation on fresh seeds 81/82/83 improved 12-second smoothing from **28.05% (v2) to 34.24% (v3)**, about **22% more**, and coverage from **35.42% to 49.72%**, with no scorching. At 24 seconds on seed 81, v3 reached **65.32% smoothing** versus **48.09%** for v2. The longer result is one seed, not an average. The new profile changes motor gain and visual lookahead; the connectome and cloth physics are unchanged.

In the earlier matched 12-second cotton trials on seeds 61/62/63, the calibrated adapter removed **30.34%** of wrinkles versus **6.52%** with the original adapter—about **4.7×** as much. Cloth coverage rose from **6.98%** to **38.40%**, with zero scorch in both groups. This is an improvement to the engineered motor adapter, not evidence of learning or physiological fidelity.

In the historical four-second version-1 cotton trials, real wiring removed **2.14%** of wrinkles versus **1.48%** for shuffled wiring (three seeds). Real wiring traveled only **0.0085 board widths**, versus 0.4185 for shuffled wiring. Disconnected wiring, silenced outputs and zero sensory input all produced zero ironing action. No case scorched. These short exploratory trials demonstrate dependence on neural activity, **not useful ironing or a biological advantage**.

In the legacy mode, across three cotton seeds, real wiring removed **17.96%** of wrinkles, shuffled wiring **23.37%**, zero connections **11.59%**, random actions **11.71%**, and the expert **34.39%** in 12 seconds. This small benchmark provides **no advantage for biological wiring**. Silk can scorch; both smoothing and damage are shown.

See [experiment report](docs/experiment-report.md) for results and validation, [implementation decisions](docs/implementation.md) for model boundaries and CyberFly observations, and the original files under `docs/` for the broader full-brain/physics plan. The eligible full graph and CUDA backend are now implemented. Anatomical meshes, fly-body physics, calibrated sensory/motor mappings and dopamine plasticity remain future work.

The interface uses the Sites starter with a local Python backend. This version is local-only; a hosted Worker cannot run this Python process. Production build validation is included, but deploying only the frontend would not deploy the experiment.

## Sources

- [BANC data schemas and public downloads](https://github.com/sjcabs/fly_connectome_data_tutorial/blob/main/data/dataset_documentation/banc_data.md)
- [BANC: Bates, Phelps, Kim, Yang et al., Nature 2026](https://www.nature.com/articles/s41586-026-10735-w)
- [Shiu et al., Nature 2024](https://www.nature.com/articles/s41586-024-07763-9) and [original model](https://github.com/philshiu/Drosophila_brain_model/blob/main/model.py)
- [CyberFly / fly-brain-spectacles](https://github.com/PtPavloTkachenko/fly-brain-spectacles), particularly [its documented engineered behavior](https://github.com/PtPavloTkachenko/fly-brain-spectacles/blob/main/docs/DECISIONS.md). Reviewed as an architectural reference; no code or neuron IDs were copied.

Credit the BANC authors and compiled-data maintainers when using this circuit. Source data retain their original terms and attribution requirements.
