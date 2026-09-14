# Implementation decisions

## Deliver the BANC starting experiment and an ironing loop

The repository's DIY guide explicitly asks for a tractable descending-to-motor BANC experiment; the research document proposes a much larger MaleCNS/GPU/cloth project. This implementation follows the former data/model scope and connects it to the latter's simplest near-flat ironing world. There is no silent dataset substitution and no whole-brain claim.

The model runs on the CPU because 232 neurons and a sparse 3,788-edge network are small enough for interactive local use. Each control step is exactly 20 ms: observe the cloth, inject rates, perform 40 neural steps, decode motor spike traces, then advance the cloth. Wall time and simulated time are different.

## Data selection

The current public metadata uses `ventral_nerve_cord_intrinsic`, not the tutorial's generic `intrinsic`. `proofread` is the string `TRUE`/`FALSE`. IDs arrive as strings. Status flags are not simply good/bad: `TRACING_ISSUE_RESOLVED` is accepted, unresolved issues excluded.

Select the bilateral DNa01, DNa02, DNp01 and DNp09 pairs; rank their directly connected proofread VNC interneurons by summed synapse counts and keep 160. Rank identified VNC motor targets reachable from these inputs/intermediates and keep 64. The extraction cutoff is five synapses. Then retain all induced edges, including weaker and recurrent edges, so the simulation cutoff can vary. Lowering the simulation cutoff does not expand the circuit boundary.

Every selected motor neuron has a one- or two-hop path from the inputs at the extraction threshold. Larger simulation thresholds can remove some paths. Connectivity is anatomically constrained, while weight, transmitter-effect and cell-dynamics assumptions remain unvalidated.

## Encoding and learned controller

Input ordering is the metadata sort by `(cell_type, side)`: DNa01 L/R, DNa02 L/R, DNp01 L/R, DNp09 L/R. The eight artificial features are positive/negative horizontal displacement, positive/negative vertical displacement, safe/hot local contact, wool indicator and cloth-contact indicator. Maximum external drive is the configurable Hz value; external Poisson events jump voltage by 16 mV, subject to the common refractory rule.

The wrinkle target is computed explicitly from the height field with a distance penalty. This engineered preprocessing performs substantial work. It should never be described as visual processing discovered in the connectome.

Training uses 420 seeded random feature probes, each held for 200 ms, with the first 100 ms discarded. The final 20% of probes select ridge strength among 1/10/100/1000. Normalization and coefficient fitting use only the first 80%. Actions are scripted labels (target-direction movement, safe contact pressure, wool steam). Validation is not a task-test score. The 12-second held-out cloth episodes use seeds 42/43/44, distinct from training seeds 731/991.

All 64 motor traces are the only readout features. No direct observation-to-action bypass is used in real/shuffled/zero modes. These controls each fit a readout to their own neural response. The zero control learns a constant intercept. The random and expert modes execute their own actions; their neural panels record a parallel real-circuit response, not a causal source of those actions.

The shuffled control permutes target stubs with seed 2026: outgoing weights and target edge counts are preserved before sparse aggregation. Source/target partners change; duplicate pairs and autapses can arise. This is one shuffle, not an ensemble or a significance test.

## Cloth and visualization

The garment mask and wrinkle amplitude live on a 40 × 40 board. Heat flows only between valid cloth cells; ambient cooling and contact heating apply at 20 ms. Pressure progressively reduces wrinkles at softened contact cells. Scorch accumulates above fabric-specific thresholds. Steam increases wool smoothing. There is no folding, stretch, draping, moisture transport, muscle simulation or validated thermodynamics.

The visible iron ellipse is the exact contact region. The cross marks the engineered wrinkle target. The raster displays all recorded spikes in the last simulated second; exports retain the complete spike history. The circuit schematic displays the strongest 100 original anatomical edges and is labeled as such. Node positions are not anatomy, and the schematic does not change to depict shuffled connections.

## What the supplied CyberFly repository contributes

Reviewed [CyberFly](https://github.com/PtPavloTkachenko/fly-brain-spectacles), `docs/DECISIONS.md`, and `brain_server/protocol.py`. It separates senses, neural measurements and engineered body state, calibrates response floors, documents landing/gait/flight controllers, and tests its optimized backend against a reference. Its Metal backend targets Apple hardware and its neuron IDs belong to MaleCNS. Neither is a drop-in replacement for this Windows/BANC experiment.

Adopted the separation of neural vs world measurements, deterministic control-step boundary, explicit engineered behavior, and independently testable simulation core. No CyberFly code, trained artifacts or root IDs are used. A later full MaleCNS backend could use its CPU/Metal design as a reference, with data-version checks and output-equality tests before optimization. Its introductory 25.6M figure refers to directed connections in the graph; it should not be reused as a count of individual synapses.

## Operation

The API binds only localhost, validates inputs, bounds request steps and episode duration, and keeps at most 16 sessions. A cached/default model starts immediately; new neural settings require fitting. Bundled default readouts are keyed by the entire extracted circuit and neural configuration. Local model caches and raw downloads are ignored by Git.

The Sites skills were used for the frontend scaffold, UI primitives, local preview and production-build workflow. The guide's requested deliverable is a local preview: there is no hosting deployment or external publication. Browser automation reported no available browser, so visual interaction QA remains unverified; HTTP/API, model tests, type checks, lint and production build are the available verification.

Generated Shadcn primitives and the generated mobile hook are excluded from application lint because the starter's own rules report errors in those unmodified files. Application code remains typechecked and linted. The scientific code uses synthetic two-neuron networks only in unit tests; the delivered simulation always loads the identified BANC circuit.
