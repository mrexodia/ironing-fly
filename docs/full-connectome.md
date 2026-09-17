# Full eligible BANC control

The default interface now runs the whole eligible graph rather than the selected
232-cell reservoir. It retains the cute 3D scene and 2D cloth. This is an
exploratory connectome-driven controller, not a validated fly nervous system or
an animal that has learned ironing.

## Boundary and provenance

The public BANC v888 metadata has 188,508 rows. Builder version 2 selects
121,992 proofread neurons with an annotated neuronal superclass, excluding
non-neurons, unrooted/too-small cells and unresolved tracing issues. There is no
task-based neuron pruning. All induced positive-count edges are cached:
10,293,444 directed pairs representing 32,758,013 synapses. The default runtime
cutoff of 5 retains 1,495,993 pairs; 1,360,624 have nonzero assumed fast weights.
“Full” means this eligible graph, not every reconstructed cell or the MaleCNS
dataset. Root IDs are always strings.

[Source hashes and selection](../data/full_provenance.json) accompany the data.
Raw Feather downloads and the compressed graph/metadata cache are ignored by
Git and regenerated automatically. Source data and terms remain those of the
[BANC dataset](https://github.com/sjcabs/fly_connectome_data_tutorial/blob/main/data/dataset_documentation/banc_data.md).

## Closed loop

Every 20 ms of simulated time:

1. Render an egocentric 16 × 8 grayscale view ahead of the iron from local
   wrinkle slope, shading, garment boundaries and scorch. Extract left/right
   mean edge contrast and absolute temporal change. The latter is an optic-flow
   proxy, not a direction-selective motion model. Neither a strongest-wrinkle
   coordinate nor the fabric label is available to the controller.
2. Encode Poisson stimulation of annotated bilateral LC11, LC4, LPLC1, LPLC2,
   LLPC1, LC12, LPC1, LC10a and LC10d populations. LC11 and object channels have a
   small visual baseline; motion channels are zero for an unchanged image.
   Contact stimulates SNta29 cells; local temperature stimulates annotated
   thermosensory receptor neurons. Contact/heat are virtual-tool observations,
   not a biomechanical model of sensory organs. SNta29 selection includes all
   annotated body parts on each side.
3. Advance every eligible neuron's LIF state in 0.5 ms steps with sparse delayed
   synaptic propagation. The source synapse counts and assumed transmitter
   signs determine weights. Membrane/synaptic constants are 20/5 ms, delay 2 ms,
   refractory 2.5 ms, rest/reset −52 mV, threshold −45 mV. Weight is count ×
   0.275 mV × scale. Scale **2** is an exploratory application setting, not a
   physiological calibration. Unknown/modulatory transmitters have zero fast
   effect. No background drive, plasticity, reward learning or readout fitting.
4. Filter output spikes with a 100 ms trace and use fixed equations below.
5. Apply the resulting movement, pressure and steam to the existing cloth toy.

The eligible graph comes from BANC annotations. The choice of visual populations
was informed by [CyberFly's documented sensory and readout experiments](https://github.com/PtPavloTkachenko/fly-brain-spectacles/blob/main/docs/SENSES_AND_READOUTS.md).
Those MaleCNS observations do **not** establish the same response here. We copied
no neuron IDs or code. This input layer bypasses photoreceptors and much early
visual processing; it is more local than the original target oracle, not a
complete visual system.

### Explicit output adapter (current version 3)

For each population let L/R be the filtered mean rates in Hz:

- Yaw = `tanh((DNa02_R − DNa02_L + DNp66_R − DNp66_L + DNp03_L − DNp03_R) / 40)`.
  Heading advances at yaw × 3 radians/s.
- Speed = `tanh((mean(DNp09) + mean(DNp66) − mean(MDN)) / 35 + mean(front_leg_motor) / 15)`.
  Velocity follows heading, with a maximum 0.30 board widths/s.
- Escape lift = `clip(max(DNp01_L, DNp01_R) / 60, 0, 1)`.
- Pressure = `clip(mean(front_leg_motor) / 6, 0, 1) × (1 − escape_lift)`.
- Steam = `clip(mean(front_leg_motor) / 6, 0, 1)`.

Version 1 remains selectable as **Original adapter**. It omitted the motor push
term, used motor/30 pressure and (motor−10)/30 steam. Its selected descending
drive often fell silent after two seconds despite sustained leg motor activity,
leaving the iron pressing one spot. Version 2 uses that motor activity to push
and makes pressure/steam useful at the observed motor rates. Gains were selected
from three candidates on cotton seed 42; no connectivity or neural parameters
were trained or changed. No planner, target selector, position input, fabric
label or constant motion term was added. This is engineering calibration of a
virtual tool, not a claim that leg motor neurons naturally control irons.

Version 2 remains **Calibrated push** with the `/25` motor drive and the original
0.45-board-width visual lookahead. Version 3, **Coverage push**, uses `/15` and
a shorter 0.25-board-width lookahead (sensory encoder version 2). The near row
remains 0.025 board widths ahead; the 16 × 8 resolution and lateral span are
unchanged. Pressure, steam, escape and steering equations are unchanged from v2.
The shorter view reduces how far ahead boundaries influence its visual inputs.
Both changes were selected together from five candidates on seed 42; they do
not add a coverage planner, access to a visited map, pose-based action rules,
constant forward motion, learned weights or an easier cloth model.

The tuning run improved 12-second smoothing from 32.13% (v2) to 38.90% (v3)
and coverage from 41.89% to 57.09%. This is a selection result, not the held-out
evaluation. Other candidates tested faster push alone, faster push with stronger
turning, shorter lookahead alone, and weaker turning. This is a small search;
the selected gains are not an optimum or physiological calibration.

These gains and the ironing-tool interpretation are engineered assumptions.
DNp66 is an orientation-related candidate, not an established ironing/thrust
command. No movement or pressure is added when output neurons are silent.
The decoder receives only neural rates, not images, temperature, target
coordinates or cloth reward. The full-mode cloth constructor also skips the
legacy target finder.

## Version-3 coverage improvement

`uv run --extra gpu python -m ironing_fly.coverage_benchmark` generates the
[current evaluation](../data/coverage_improvement.json). Gains were frozen after
[five tuning candidates](../data/coverage_tuning.json) on seed 42; the paired
cotton trials then used new seeds 81, 82 and 83. Both profiles use the same
121,992 neurons, weights, neural constants, cloth model and 170°C temperature.

| Profile | 12s mean smoothed | 12s mean covered | Scorch |
|---|---:|---:|---:|
| Calibrated push, v2 | 28.05% | 35.42% | 0% |
| Coverage push, v3 | 34.24% | 49.72% | 0% |

All three paired runs improved. This is approximately 22% more wrinkle removal
and 40% more area reached relative to v2 on these seeds. These percentages must
not be compared as a matched test against the previous 61–63 benchmark, which
used different cloth/noise seeds.

The extended run on seed 81 reached **65.32% smoothing / 82.60% coverage** at
24 seconds, versus **48.09% / 52.87%** for v2, with zero scorch in both. This
longer comparison has only one seed and does not establish general performance.
V3 still revisits areas and can miss part of a garment; no coverage planner or
new learning mechanism was added.

Shuffled wiring at seed 81 smoothed 14.46% in 12 seconds. The benchmark also
records shorter, three-second disconnected/output-silenced/no-sensory controls
separately from the performance table; their durations are explicit in the UI
and JSON. Such controls test dependence on neural output, not biological
fidelity. Material smoke tests use seed 81 and the existing 110°C silk / 150°C
wool presets.
All three causal controls produced zero travel, coverage and smoothing. The
silk and wool smoke tests smoothed 36.52% and 29.41%, respectively, with no
scorch. These material results each represent one run, without a paired v2
material comparison.

## Historical version-2 ironing improvement

Run `uv run --extra gpu python -m ironing_fly.improvement_benchmark` for the
[paired results](../data/ironing_improvement.json). All trials last 12 simulated
seconds. The cotton comparison uses seeds 61, 62 and 63, separate from the
single tuning seed 42; identical connectome, neural parameters, input encoder,
temperature and cloth equations are used for both adapters.

| Adapter | Mean wrinkles removed | Cloth covered | Travel, board widths | Scorch |
|---|---:|---:|---:|---:|
| Original v1 | 6.52% | 6.98% | 0.0073 | 0% |
| Calibrated v2 | 30.34% | 38.40% | 0.9444 | 0% |

All three paired trials improved (v2: 32.14%, 31.36%, 27.54%). This is about
4.7× the smoothing with much more coverage. Coverage counts each garment cell
once after contact at pressure above 0.1; it does not claim the cell is smooth.
Travel records actual displacement after board clipping. Both are measurement
fields and never enter the controller.

Version-2 shuffled, disconnected, output-silenced and sensory-silent controls
use seed 61 only. Shuffled wiring smoothed 8.51%; the other three controls gave
zero travel, pressure coverage and smoothing. This small, tuned-adapter
comparison does not establish an advantage of biological wiring in general.
The real controller still has no coverage planner and may revisit an area or
miss parts of a garment. Some modeled firing rates exceed 300 Hz.

Full-mode material changes apply explicit, adjustable iron presets: cotton
170°C, silk 110°C and wool 150°C. The decoder still receives no fabric label.
These are settings for this toy cloth model, not real garment-care guidance.
The API uses the same presets when temperature is omitted; an explicitly
supplied temperature is preserved. The benchmark includes a silk and wool
smoke test at seed 61 with these settings.
Silk removed 34.29% and wool 28.21%, both with zero scorch in those single runs.

## Original version-1 causal controls

`uv run --extra gpu python -m ironing_fly.full_benchmark` reproduces
[the included short runs](../data/full_benchmark.json). Four seconds per run,
cotton shirt, 170°C, max stimulus 150 Hz, scale 2, cutoff 5. Real/shuffled/zero
use seeds 42, 43 and 44; the two extra interventions use seed 42 only.

| Condition | Runs | Mean wrinkles removed | Mean travel, board widths |
|---|---:|---:|---:|
| Real wiring | 3 | 2.14% | 0.0085 |
| Shuffled target partners | 3 | 1.48% | 0.4185 |
| Disconnected weights | 3 | 0% | 0 |
| Decoded output neurons silenced | 1 | 0% | 0 |
| No sensory input | 1 | 0% | 0 |

No run scorched. Disconnected and output-silenced runs retained sensory/network
activity but produced zero tool action. No sensory input produced no spikes.
Shuffling permutes target indices with a fixed seed while retaining source
weights and target endpoint counts; it can merge parallel pairs or create
self-connections. The map always shows original anatomy, not control rewiring.

The original controller mostly presses one small area. Some cells average around or
above 300 Hz, flagged by the interface. These results establish dependence on
neural activity under the stated equations; they do **not** show natural fly
behavior, effective ironing, physiological fidelity or a biological advantage.
The default scale was explored on seed 42; these are not held-out efficacy
trials. The previous 232-cell benchmark remains separate in the legacy UI.

## Runtime, recording and verification

- CuPy CUDA runs on this machine's RTX 3090 at roughly 0.37–0.43 biological
  seconds per wall second in these runs. UI refresh/serialization adds overhead.
  CPU fallback is available and explicitly identified in the interface.
- GPU uses float32, CPU float64. Both integrate the passive coupled exponential
  equations exactly between discrete events, with threshold checks and input
  pulses on the timestep grid. They are not bit-identical full-network models.
- All 121,992 neurons run. The raster/map and exported spike times are a fixed
  **573-cell sample**, enriched for sensory cells and including every decoded
  output neuron. The map displays its strongest 100 original edges. Neural
  output means use complete named groups, not just the visualization sample.
- Export schema 2 includes the motor-adapter and sensory-encoder versions, data provenance, backend, neural settings, sample
  IDs/spikes, per-step sensory channels, output rates, heading/actions and cloth
  metrics. Replay recomputes the closed loop and verifies these values on the
  recorded backend. Exports without an adapter-version field replay as version 1;
  old v1/v2 exports without an encoder version use the original encoder.
  Future library/hardware changes can break spike replay.
- Nineteen automated tests passed, including legacy behavior, exact passive
  integration, delayed excitation/inhibition, disconnection, output ablation,
  seeded chunk invariance, local-sense independence from the target oracle,
  full-mode API/export/replay, backwards-compatible version-1 replay, calibrated
  motor pushing, zero-output behavior, coverage metrics, material presets and a
  small CPU/GPU causal fixture. New checks cover the short retina's spatial
  boundary and independent replay of the previous profiles.
- A version-3 121,992-cell CUDA episode replayed 50 control ticks and **10,450 sampled
  spikes** exactly on this machine. This does not establish general CPU/GPU or
  cross-device equivalence.
- Frontend lint, TypeScript and production build passed. Browser automation is
  unavailable in this session; visual interaction has not been re-inspected.

The 3D fly remains illustrative. Cloth heat/flattening/scorch, axis-aligned iron
contact and board constraints remain heuristic. Muscles, compliant cloth,
learning, receptor-specific physiology and validated sensory calibration are
not implemented.
