# First experiment report

## Circuit and configuration

Prepared from the public BANC v888 metadata and simple-v3 aggregated edge list, using the actual schema inspected at build time. The downloaded files contain **188,508 metadata rows** and **13,620,865 directed pairs**, with no duplicate pairs. Root IDs are strings. Missing annotations in the complete metadata: 69,760 cell types, 28,632 superclasses, 34,455 predicted neurotransmitters. The circuit filter requires proofread, appropriately classified neurons and excludes unresolved tracing problems/non-neurons.

The selected network contains **232 neurons, 3,788 connections and 59,959 synapses** before runtime filtering. It comprises bilateral DNa01/DNa02/DNp01/DNp09 inputs, 160 VNC interneurons and 64 identified VNC motor neurons reachable within two hops. Predicted transmitters: 106 GABA, 94 acetylcholine, 31 glutamate and one octopamine. Circuit selection, original file hashes and schemas are in `data/provenance.json`.

Default: 150 Hz maximum engineered input, synapse-count cutoff 5, weight scale 4, no background drive, neural timestep 0.5 ms, and 20 ms cloth/control steps. The reference 0.275 mV per-synapse scale produced little motor activity in an initial all-input probe; scale 4 is a disclosed exploratory choice, not a BANC physiological default.

## DNa02 stimulation

The separate experiment stimulates only the two DNa02 neurons for one second. At default weight/filter settings and seed 42:

| External input | Mean motor firing |
|---|---:|
| 0 Hz | 0.00 Hz |
| 75 Hz | 17.91 Hz |
| 150 Hz | 24.22 Hz |
| 250 Hz | 28.09 Hz |

The full sweep covers rates 0/75/150/250 Hz, thresholds 3/5/10 synapses, weight scales 1/2/4 and seeds 42/43/44: **108 trials**. Zero-input/no-background networks remain silent. All sweep states were finite and no trial exceeded the diagnostic high-rate threshold of 300 Hz; the maximum observed single-neuron rate was 181 Hz. These checks establish numerical behavior under these settings, not physiological validity. Silent responses at weak weights are valid results.

## Ironing controls

Five controllers, three fabrics, three held-out seeds (42/43/44): **45 trials**, each 12 simulated seconds on a T-shirt at 170°C. Real, shuffled and zero modes fit separate ridge readouts to the same seeded feature-probe training task. Below are mean percentages, with no claim of statistical significance:

| Controller | Cotton removed | Silk removed | Silk scorch | Wool removed |
|---|---:|---:|---:|---:|
| Real BANC circuit | 17.96% | 28.91% | 3.90% | 11.48% |
| Shuffled target partners | 23.37% | 31.97% | 1.63% | 24.11% |
| Zero connections | 11.59% | 13.23% | 5.21% | 8.83% |
| Random actions | 11.71% | 21.32% | 2.26% | 7.72% |
| Scripted expert | 34.39% | 23.57% | 0.94% | 29.42% |

Cotton and wool had zero measured scorch in these runs. Silk illustrates why wrinkle removal alone is not a sufficient score: unsafe pressure can improve smoothing while increasing damage. The expert is a simple heuristic and is not an optimal policy.

**This benchmark does not demonstrate an advantage from the biological wiring.** The single shuffled network outperformed the real circuit on smoothing and silk damage. Training-probe validation MSE was 0.1042 for real, 0.0457 for shuffled and 0.2518 for zero; this validation score is separate from the held-out cloth result. Multiple topology shuffles, more seeds, longer tasks and matched ablations would be needed for stronger conclusions.

The benchmark completed in approximately 84 seconds on the available machine. That includes the neural sweep and cloth episodes with already cached readouts; it is not a GPU or whole-brain performance claim. Full per-seed metrics, trial firing vectors and configurations are included in `data/benchmark.json` and reproducible via `uv run python -m ironing_fly.experiment`.

## Verification

- Nine automated tests cover analytic passive membrane decay, causal synaptic delay, inhibitory sign, lossless IDs, motor reachability, deterministic step chunking, frozen source data, shuffled outgoing-weight preservation, zeroed connectivity, cloth pressure/steam/heat/scorch behavior, API validation, missing sessions and JSON export/replay.
- A real-controller export replay verified 50 ticks, 1,529 exact spike events and all recorded cloth metrics. Export includes learned coefficients for inspection.
- The frontend passes TypeScript, application lint and a production build. Unmodified starter primitives are excluded from application lint.
- The local route and proxied API returned HTTP 200. API testing exercises changed settings, advancing an episode, baseline comparison and download serialization.
- A fresh `uv run python launch.py` started both servers. Through the live frontend proxy, a downloaded real-controller episode replayed 25 ticks and 637 spikes exactly; changing DNa02 input from 75 to 150 Hz changed mean motor firing from 17.91 to 24.22 Hz. All 45 benchmark rows were served.
- Updated frontend dependencies pass `npm audit` with zero reported vulnerabilities. The upstream test client emits two deprecation warnings; they do not fail the nine tests.
- Browser automation reported **no available browser**. Visual appearance, click/keyboard interactions and browser download behavior have not been verified in a browser; API-level success does not establish those.

## Limitations and next milestones

This is a selected BANC network in a heuristic height-field world. It is not a full 166,700-neuron MaleCNS simulation, an anatomical brain rendering, a fly body, a faithful deformable cloth simulation or evidence of a fly learning a human chore. The neural model differs from Shiu's validated FAFB implementation in integration, external drive, refractory/delay rounding and dataset/circuit boundaries. No biological validation has been performed.

The next substantial upgrades are a full-connectome backend with reference-equivalence tests, a measured sensory encoder, a proper deformable garment solver, ensembles of shuffled controls, and longer held-out garment tasks. CyberFly is a useful reference for backend validation and disclosed engineered body control; its Mac Metal kernel and MaleCNS IDs were not copied into this BANC implementation.
