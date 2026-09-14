# Fly-Brain-Irons-a-Shirt: A Full Technical Project Plan for a Connectome-in-the-Loop Cloth-Ironing Meme Demo

## TL;DR
- **The project is buildable on your 2×RTX 3090 desktop, and the DGX Spark is not needed.** The whole-brain connectome LIF simulation fits in ~0.2–0.4 GB of GPU memory and one GPU can run it while the other runs a MuJoCo/MJX cloth sim; the real bottleneck is timestep choice, not hardware. At a faithful dt=0.1 ms the connectome runs several times slower than real-time single-trial; at a coarse dt (10–20 ms) it runs faster than real-time.
- **Your premise is mostly correct but needs three corrections:** (1) the connectome is real — **MaleCNS v1.0**, 166,700 neurons, with exactly **25,582,938 directed connections / 124,177,617 synapses** in the graph most tools use (the "~125 million" press figure is the raw synapse count, not the edge count); the data v1.0 was released **June 8, 2026** and the *Cell* paper published **September 3, 2026** under CC-BY 4.0; (2) a PyPI package literally called **`flybrain`** exists and does exactly what you described, but it is a hobbyist/meme package tied to a crypto token, not a scientific tool — use it for inspiration, build on `philshiu/Drosophila_brain_model` + Brian2/GeNN for legitimacy; (3) the honest framing is essential because published controls show shuffled/random wiring often performs as well as the real connectome on these reservoir tasks.
- **Recommended stack:** MaleCNS v1.0 connectome (via neuprint-python/navis) → LIF network in Brian2/GeNN or a PyTorch sparse-CSR rate model → ridge-regression readout on descending-neuron traces → MuJoCo 3.x + MJX/MuJoCo-Warp cloth (or SoftGym for a faster start) → live raster + brain render overlay. Frame it explicitly as "a frozen fly connectome as a reservoir, with a trained linear readout," never "the fly learned to iron."

## Key Findings

### The connectome is real; correct the numbers
- **MaleCNS v1.0** — Berg S, Beckett IR, Costa M, et al. (2026), "Sexual dimorphism in the complete Drosophila male central nervous system connectome," *Cell* 189(18):5504–5526.e15, doi:10.1016/j.cell.2026.08.015 (bioRxiv preprint 2025.10.09.680999). It is the first complete adult male CNS connectome (central brain + optic lobes + ventral nerve cord with intact neck connective). A collaboration of HHMI Janelia FlyEM, University of Cambridge (Dept. of Zoology), MRC LMB, and Google Research.
- **Data release vs paper:** the project dates **v1.0 data to June 8, 2026** and the **Cell paper to September 3, 2026** (per the cobanov/awesome-fly index). Treat "September 3, 2026" as the publication date, not the data-release date.
- **Neuron count: 166,700 — accurate.** Berg et al. state: "we identified, proofread and annotated 166,700 neurons (including sensory axons)… forming 11,710 cell types"; proofreading is estimated at ~44 person-years (the bioRxiv preprint reports the near-final 166,691 neurons / 11,691 types).
- **Connections vs synapses — the number to get right:** the graph tools actually use has **25,582,938 directed connections** built from **124,177,617 synapses** among the 166,700 neurons (confirmed by both the `flybrain` package and the FlySweeper repo, which cite "Berg et al., Cell 2026, CC BY 4.0: 166,700 neurons, 25,582,938 directed connections, 124,177,617 synapses"). The full connection-weights table (`connectome-weights-male-cns-v1.0-minconf-0.5.feather`) is 1.1 GB. Say "~25.6M directed edges / ~124M synapses" and be explicit about which you mean.
- **License: CC-BY 4.0.** Cite Berg et al. (2026). Download via `neuprint-python` (`dataset='male-cns:v1.0'`, token from neuprint.janelia.org), `navis`, or bulk `gs://flyem-male-cns/v1.0/…` Google Storage buckets (Feather annotation/connectivity tables; SWC/precomputed skeletons; neo4j dump). Project site: male-cns.janelia.org.
- **Other datasets for comparison:** FlyWire (female FAFB) contains **139,255 neurons and 54.5 million synapses** (Dorkenwald et al., *Nature* 634:124–138, 2024); the **hemibrain** covers ~20,000 uncropped neurons and ~14 million synapses (Scheffer et al. 2020; figures per Dorkenwald et al. 2024, doi:10.1038/s41586-024-07558-y). A complete **female** CNS (brain+VNC, "BANC") was also reported in the same era. **MANC** is the male VNC.

### The `flybrain` PyPI package: real, but a meme/crypto artifact
- `pip install flybrain` (v0.1.0, released Sep 13, 2026, MIT code) genuinely wraps MaleCNS v1.0 as a **166,700-neuron LIF spiking network** with CPU (numba) and GPU (CuPy/CUDA 12) backends, sensory injection (`Eyes`, `FeatureDetectors` driving visual projection neurons), descending-neuron readout, and a reservoir-computing readout module (`Trace`, `run`, `Readout`, ridge/logistic PCA). It matches your described pattern (frozen connectome + sensory injection + reservoir readout) almost exactly.
- **BUT:** it is authored by "alextitonis," tied to a `$FLYAI` crypto token on Robinhood Chain, and hosted at flyaiworld.com. This is a meme/promotional project, not a maintained scientific package. Its neuron model follows "Fly64" by Jessica Paquette. **Recommendation:** study/borrow its API design, but for a "technically legitimate" demo, build your core on the peer-reviewed `philshiu/Drosophila_brain_model` (Brian2) and/or `eonsystemspbc/fly-brain` (multi-backend benchmark harness), and cite the actual *Cell*/*Nature* papers. Do not depend on a crypto-linked package for reproducibility. (A related tool, `github.com/ASHR12/FlySweeper`, runs the same 166,700-neuron LIF sim at 1.3 ms per 20-ms brain step in Python/numba, or 0.88 ms/step in-browser on WebGPU — a useful independent corroboration of the coarse-dt performance.)

### The "fly brain plays X" trend: what actually happened
- **DOOMFLY** — Alex Wormuth (a software engineer) posted on X (Sept 6, viral demo Sept 9, 2026) "training a fly brain to play Doom using the full MaleCNS v1.0 connectome. Each Doom frame stimulates sensory neurons. Neural activity is mapped to game controls. Damage triggers a stimulus to two PPL101 dopamine cells as reinforcement." Source code public. This is exactly the template for your project — including the biologically-motivated dopamine reward you asked about.
- **Mario 64** — Jessica Paquette (@barrelshifter) posted footage + GitHub code, explicitly noting it was "100% vibe coded with GPT Astra… just for fun" (Mario running into walls).
- **Minecraft, Beat Saber, Bad Apple, YMCA-poses-to-tones, a "crypto day trader"** — all reported by mainstream tech press (Gizmodo, Tom's Hardware, PC Gamer, TechSpot, HotHardware, TheGamer). These are real posts but overwhelmingly low-rigor stunts. The press uniformly notes the honest caveat: a connectome is a static wiring map, not a living simulation, and "the fly learned to play X" is not what is happening.
- **Fly Language Model (FLM)** — a more rigorous variant wired the full MaleCNS into a frozen 1.2B LLM as a reservoir; its own authors' controls (randomized wiring, zeroed weights, relabeled nodes) showed **the wiring did not help** beyond the trained adapter. This is the single most important cautionary precedent for your honesty section.
- A curated index exists: **github.com/cobanov/awesome-fly** (lists MaleCNS, FlyWire, brain sims, embodied models, games, tools).

### Reward biology checks out
- **Dopaminergic PPL1 and PAM clusters gate plasticity at Kenyon-cell→MBON synapses in the mushroom body** — this is textbook, well-published *Drosophila* associative-learning circuitry. PPL1 DANs largely convey aversive/punishment signals; PAM DANs largely convey reward. Coincident KC activity + DAN dopamine induces (predominantly) long-term depression at KC→MBON synapses, biasing behavior via MBONs. Modeling implementations exist (e.g., "Learning with reinforcement prediction errors in a model of the Drosophila mushroom body," *Nat. Commun.* 2021; an LDA model of MB compartments, bioRxiv 2022; KC→MBON LTD imaging, eNeuro 2023).
- **Courtship-song neurons are real and usable as a trigger:** P1/pC1 (decision to sing), **pIP10** (descending command neuron linking brain to thoracic song center), and thoracic CPG elements **dPR1, TN1A, vPR6, vMS11** (pulse/sine song). Optogenetic pIP10 activation drives pulse song (von Philipsborn et al., *Neuron* 2011; Nature Neuroscience 2024). Using pIP10/dPR1 firing as a "gag trigger" (e.g., the fly "sings" when it scorches silk) is biologically grounded and funny.

### Motor and sensory wiring is well-characterized
- **Descending neurons for locomotion:** DNa02 (high-gain ipsilateral steering), DNa01 (low-gain steering), DNg13, DNb05/DNb06, DNp09 ("broadcaster," forward walking + ipsiversive steering, and male courtship steering), MDN/moonwalker (backward walking), DNa03 (broadcaster). These map cleanly onto iron actions (turn/translate/reverse). Sources: Rayshubskiy/Wilson lab steering work (eLife 2024/*Cell* 2024), Bidaye et al. 2020 (DNp09), moonwalker DN literature.
- **Visual system:** photoreceptors R1–R8 → lamina (L1–L5) → medulla (Mi, Tm, T4/T5 motion detectors) → lobula/lobula plate → **lobula columnar (LC) feature detectors** projecting to optic glomeruli: LC4/LPLC2/LC6/LC16 (looming), LC11 (small moving objects), LC10 group (mate tracking). ~700–800 ommatidia/eye, ~5° acceptance angle, high temporal resolution. The **flyvis** package (Lappalainen et al., *Nature* 2024, doi:10.1038/s41586-024-07939-3, TuragaLab/flyvis) is the gold-standard connectome-constrained visual model and gives you a ready hex-lattice retina encoder.

### Simulator performance: the decisive variable is timestep, not the GPU
- **Faithful Shiu et al. model** (Brian2, dt=0.1 ms, ~140k neurons/~50M synapses; Shiu, Sterne et al., *Nature* 2024, doi:10.1038/s41586-024-07763-9): the authors used **Brian2 (CPU C++ codegen)**; no GPU runtime published. The `eonsystemspbc/fly-brain` harness re-implements it across Brian2, Brian2CUDA, PyTorch (sparse CSR), NEST GPU, and GeNN/PyGeNN, all at dt=0.1 ms.
- **Measured (illustrative, DGX Spark GB10, 138,639 neurons, dt=0.1 ms, single trial):** Brian2 CPU ≈ 0.55× real-time; Brian2CUDA ≈ 0.13×; PyTorch ≈ 0.08×. The GPU is **launch/latency-bound** — each 0.1 ms step is one small sparse mat-vec (cuSPARSE csrmv ≈ 0.86 ms/step, ~84% of GPU time). GPUs only win via **trial batching**. (These figures are from a self-published blog, not peer review — verify on your own hardware.)
- **flybrain (MaleCNS, 166,700 neurons, coarse dt=20 ms):** 1.4 ms/step on an RTX 4060 laptop ≈ **~14× real-time**; 8.9–15 ms/step on a 24-thread CPU ≈ 1.3–2.2× real-time. Connectome fits in ~210 MB GPU memory; `batch=8` runs 8 flies at ~1.2 ms/fly/step. The independent FlySweeper implementation corroborates: 1.3 ms per 20-ms brain step in Python/numba, 0.88 ms/step in-browser on WebGPU.
- **Brian2CUDA benchmarks** (Alevi et al., *Front. Neuroinform.* 2022, doi:10.3389/fninf.2022.883700): for LIF networks with N>10^5, Brian2CUDA gives nearly 3 orders of magnitude speedup over single-threaded Brian C++; RTX 2080 Ti (11 GB) held ~8.6×10^5 LIF neurons. Consumer GPUs perform comparably to A100 **in single precision** (float32 essential — consumer cards are ~32× slower in double precision). Heterogeneous synaptic delays cost ~1 order of magnitude.
- **Memory of the connectivity matrix:** CSR with 50M synapses ≈ 200 MB (float32 values) + 200 MB (int32 col indices) + negligible row pointer ≈ **~400 MB**; empirically the ~25.6M-edge MaleCNS matrix is ~205–210 MB and the ~15M-edge FlyWire matrix ~289 MB on disk. **All fit trivially in a single 24 GB RTX 3090.**
- **No published RTX 3090 fly-brain LIF number exists** (triangulated from 4060 laptop, 2080 Ti, 4070, GB10). A 3090 (GA102, ~35 FP32 TFLOPS) should land between the 4060 laptop and 4070/2080 Ti; memory is a non-issue.

## Details

### A. Cloth / ironing simulation environment

**The landscape and speed/realism tradeoff:**
- **MuJoCo 3.x** has native deformable/`flex` support (thin-shell cloth). **MuJoCo Warp (MJWarp)** and **MJX** are GPU backends; MuJoCo 3.5's Newton solver adds a **Vertex Block Descent (VBD) solver for thin deformables (cloth)**. Per the NVIDIA Technical Blog, MuJoCo Warp is "up to 152x faster for locomotion and 313x faster for manipulation than MJX on GeForce RTX 4090" (and 252×/475× on the RTX PRO 6000 Blackwell). This is the best-supported, best-documented, most future-proof path.
- **NVIDIA Isaac Sim / Isaac Lab** — mature cloth support (now via Newton/MJWarp backend), but heavy install and USD overhead; overkill for a meme demo unless you want photorealism.
- **Genesis** — advertises up to 43M FPS (rigid, RTX 4090); PBD/FEM cloth supported; extremely fast but younger/less stable, and cloth is not its headline benchmark. A good "stretch" option.
- **SoftGym** (Xingyu-Lin/softgym, built on NVIDIA FleX) — **the fastest path to a working cloth demo.** It ships `ClothFlatten`, `ClothFold`, `ClothDrop` environments with a Gym API, a particle grid, and — critically — a built-in **`_set_to_flatten()` maximum-flatten-area** metric that is essentially a ready-made wrinkle/coverage score. Downside: old CUDA/Ubuntu build (Docker image provided).
- **PyBullet** — NeuroMechFly v1 used it; MuJoCo has since superseded it for this niche.
- **SOFA, DiffCloth, Blender cloth** — SOFA is FEM-accurate but slow; DiffCloth is differentiable (nice for the flatten objective) but niche; Blender is offline-only (great for the final beauty-render montage, not the loop).

**Reusable cloth-manipulation codebases:** SoftGym (ClothFlatten/Fold), **FlingBot** (Ha & Song — dynamic unfolding; coverage metric; ~47 ms/action), **Cloth Funnels** (canonicalized alignment; ~186 ms/action), **GarmentLab** (Isaac-based, 11 garment categories, 20 tasks), DeformableRavens, garment datasets **CLOTH3D** and **Deep Fashion3D**. Garment-smoothing papers use coverage/IoU as the smoothness metric — directly reusable as a wrinkle score.

**Recommendation:** Start on **SoftGym `ClothFlatten`** (fastest to a shareable artifact; the flatten-area metric is your wrinkle score) and, if you want a nicer-looking final video, port to **MuJoCo 3.x flex + MJX/MJWarp** on GPU 0. Prioritize a legible top-down "wrinkle heatmap" over photorealism.

**Modeling heat / scorch / fabric type / pressure (simple + visually legible):**
- Represent cloth as an N×N particle grid with a per-particle **temperature field** `T[i]` and **scorch field** `S[i] ∈ [0,1]`.
- Iron carries position, a contact mask, a press-pressure scalar `p`, and a temperature setting `T_iron`.
- Heat diffusion per step: `T += α·(contact_mask·(T_iron − T)) + κ·laplacian(T) − λ·(T − T_ambient)`.
- Scorch accumulates when temperature × dwell time exceeds a fabric-specific threshold: `S += max(0, T − T_scorch[fabric])·dt·p·c_fabric`, clamped to 1. Render scorch as a brown→black colormap.
- Fabric type = a parameter triple `(T_scorch, wrinkle_stiffness, heat_capacity)`: cotton (high `T_scorch`, forgiving), silk (low `T_scorch`, scorches instantly — the comedy fabric), wool (needs steam/moisture, medium).
- Wrinkle representation: per-particle deviation from the flat rest plane; **wrinkle score = mean absolute z-deviation (or 1 − coverage_area/flat_area)**. Press pressure flattens local wrinkles proportional to `p` but raises scorch risk — the core risk/reward tension.

### B. Sensory encoding

**The retinotopic downsampling problem:** a rendered scene is e.g. 512×512 RGB; the fly has ~700–800 ommatidia/eye on a hex lattice with ~5° acceptance angles (very low spatial resolution, high temporal). You must downsample dramatically. Three legitimate options:

1. **Full visual pathway (most legitimate, slower):** use **flyvis** (TuragaLab) to map the frame onto a hexagonal photoreceptor lattice (R1–R8) and run the connectome-constrained optic-lobe model to get LC-neuron activations, then inject those into the MaleCNS central brain. Heavy but the "real" answer. Note flyvis models the *female* optic lobe.
2. **Direct LC/PN injection (recommended for the demo):** skip the optic lobe. Compute a handful of hand-designed features from the frame (looming/edge/centroid/wrinkle-density) and inject them as input currents directly into **LC feature-detector neurons** (LC4/LPLC2 for looming edges, LC11 for small features) or visual projection neurons. This is what the game demos effectively did and is defensible: "we drive the fly's own feature-detector neuron types."
3. **Auxiliary channels:** map the wrinkle score / temperature to **mechanosensory or gustatory** input, or map a "scorch event" to a nociceptive-style stimulus onto PPL1 (this doubles as your punishment signal).

**Concrete encoder skeleton (frame → input currents):**
```python
import numpy as np

class HexEncoder:
    """Downsample an RGB frame to a hex ommatidial lattice, then to LC-cell currents."""
    def __init__(self, brain, n_omma=721, gain=0.8):
        self.centers = self._hex_lattice(n_omma)      # (721,2) in [0,1]^2
        self.lc4 = brain.cells(["LC4","LPLC2"])        # looming/edge detectors
        self.lc11 = brain.cells(["LC11"])              # small-object detectors
        self.gain = gain

    def _hex_lattice(self, n):
        s = int(np.ceil(np.sqrt(n)))
        xs, ys = np.meshgrid(np.linspace(0,1,s), np.linspace(0,1,s))
        ys[:, 1::2] += (1/s)/2                          # offset alternate rows -> hex
        pts = np.stack([xs.ravel(), ys.ravel()], 1)[:n]
        return pts

    def sample(self, frame):
        H, W, _ = frame.shape
        gray = frame.mean(-1) / 255.0
        idx = (self.centers * [W-1, H-1]).astype(int)
        omma = gray[idx[:,1], idx[:,0]]                # (721,) luminance per ommatidium
        return omma

    def to_currents(self, frame, prev_omma=None):
        omma = self.sample(frame)
        motion = np.abs(omma - prev_omma) if prev_omma is not None else np.zeros_like(omma)
        edge = np.abs(np.gradient(omma))               # crude spatial edge energy
        loom = motion.mean()                           # expansion proxy
        inject = [(self.lc4,  self.gain*loom),
                  (self.lc11, self.gain*edge.mean())]
        return inject, omma
```

### C. Motor readout

**Biological vs arbitrary mapping — recommendation:** use a **biologically-motivated mapping for the punchline, learned readout for the actual control.** That is, read out from the *real descending-neuron populations* so you can honestly say "the iron's turns are driven by the fly's steering DNs," but let a trained linear layer decide the weighting.

**DN → action map (biologically motivated):**
- DNa02_L / DNa02_R differential firing → iron rotate/steer left/right (real steering DNs).
- DNp09 / bolt PN population rate → forward translation ("press forward").
- MDN (moonwalker) rate → back-off / lift-and-reposition.
- Wing/leg-power DN populations → press-harder vs lift (press pressure axis).
- Optional gag: pIP10/dPR1 firing → the fly "sings" (sound cue) when it scorches silk.

**Reservoir-computing readout (the actual controller):**
- Collect spike traces (or low-pass-filtered rates) from a chosen output population (all ~1,300 descending neurons, or a curated subset).
- Low-pass filter spikes with an exponential kernel (τ ≈ 50–200 ms) to get continuous "rate" features `r(t)`.
- **Washout:** discard the first ~200–500 ms of each episode (transient).
- **Readout:** ridge regression (linear) or logistic regression mapping `r(t)` → action logits. `action = W_out · r(t) + b`.
- **Regularization:** ridge λ chosen by cross-validation (typical 1e-2 to 1e2). Keep readout dimensionality low (PCA to 50–200 components) to avoid overfitting.
- **Sampling rate:** decode at physics/render rate (30–60 Hz), i.e., every ~16–33 ms of biological time, aggregating spikes in that window.

```python
from sklearn.linear_model import Ridge
from sklearn.decomposition import PCA
import numpy as np

class ReservoirReadout:
    def __init__(self, n_pca=128, alpha=10.0, tau=0.1, dt=0.02):
        self.pca = PCA(n_components=n_pca)
        self.reg = Ridge(alpha=alpha)
        self.decay = np.exp(-dt / tau)
        self.state = None

    def filter(self, spikes):                 # spikes: (n_out,) binary
        self.state = (self.decay * self.state + spikes) if self.state is not None else spikes.astype(float)
        return self.state

    def fit(self, traces, actions):           # traces: (T, n_out), actions: (T, n_act)
        X = self.pca.fit_transform(traces)
        self.reg.fit(X, actions)

    def predict(self, trace):
        return self.reg.predict(self.pca.transform(trace[None]))[0]
```

### D. Learning scheme

**Two realistic options (do #1 first, #2 as the "biologically legit" upgrade):**

**Option 1 — train only the linear/ridge readout (reservoir computing).** The connectome is frozen; you fit `W_out` on descending-neuron traces against target actions (from a scripted expert or reward-weighted regression). This is what all the viral demos and the ESA/Costi et al. (*Biomimetics* 2025) and FLM works actually do. Fast, honest, and the connectome genuinely participates as a nonlinear temporal filter.

**Option 2 — dopamine-gated plasticity restricted to KC→MBON synapses.** Keep the whole connectome frozen *except* KC→MBON weights. Stimulate PPL1 (punishment: scorch/burn) and PAM (reward: wrinkle reduction) DANs based on the reward signal. Plasticity rule (three-factor, DAN-gated LTD, per published MB models):
```
Δw_KC→MBON = −η · KC_active · DAN_active        # co-active KC + punishment DAN → depression
w ← clip(w · (1 − decay) + Δw, w_min, w_max)
```
Hyperparameters from the literature: sparse KC coding (~5% active), one DAN per MB compartment, DAN-induced plasticity one-sided and independent of MBON activity. Published precedent: *Nat. Commun.* 2021 (reinforcement prediction errors in MB), the MB LDA model (bioRxiv 2022), and the KC→MBON LTD literature (eNeuro 2023). This is the version you can defensibly title "the fly learns via its own dopamine rule."

**Why full backprop through the connectome is off the table:** if you backprop and update the recurrent connectome weights, you are no longer running "the fly" — you have initialized an RNN with fly connectivity and then overwritten it into an arbitrary trained network. It stops being a connectome demo and becomes "an RNN we happened to seed from a fly." Restricting learning to the readout (Option 1) or to the biologically plastic KC→MBON synapses (Option 2) preserves the claim "this is the fly's wiring."

**Concrete ironing reward function:**
```
r = w1·Δwrinkle_reduction          # + for flattening (primary)
  − w2·burn_increment              # − for scorch (per-fabric weighted; silk heavy)
  − w3·time_penalty                # − per step (encourages efficiency)
  − w4·edge_seam_violation         # − for ironing over buttons/seams/edges badly
  − w5·off_cloth_penalty           # − for ironing the empty board
```
Map `+r` spikes to PAM DANs, `−r` spikes to PPL1 DANs. Fabric-specific: silk multiplies `w2` heavily (scorches fast); wool requires a "steam" action before pressing or wrinkle reduction is capped.

### E. Engineering and performance

**Two-process architecture (recommended):**
- **Process A (GPU 0): neural sim.** Brian2/GeNN or PyTorch sparse-CSR LIF/rate network. Exposes `step(inject) -> spikes`.
- **Process B (GPU 1): physics + render.** MuJoCo/MJX cloth on GPU 1; renders frames; computes wrinkle/burn/reward.
- **Message passing:** shared-memory ring buffer or ZeroMQ/`multiprocessing.Queue`. Physics sends frames+reward; neural sends descending-neuron rates. Only small vectors cross per tick, so PCIe traffic is negligible.

**Timestep reconciliation (the crux):**
- Neural dt: 0.1 ms (faithful) up to 10–20 ms (coarse/fast).
- Physics dt: 1–10 ms.
- Render/decode: 30–60 fps (~16–33 ms).
- **Recommended: locked-step at the decode boundary.** Each 20–33 ms "control tick": (1) render frame, (2) encode → inject, (3) advance neural sim N sub-steps to cover the tick, (4) read descending rates, (5) decode action, (6) advance physics to next tick. Deterministic and easy to debug. Asynchronous (free-running neural sim) is more "alive" for the video but harder to make reproducible — offer it as a visual mode only.
- **Speed decision:** for a real-time-feeling demo, run the neural sim at **coarse dt (10–20 ms)** so it keeps up (flybrain/FlySweeper-style ~14× real-time on a single GPU). Reserve dt=0.1 ms faithful mode for offline "hero" renders where you can run slower than real-time and speed up the video in post.

**Throughput estimate on 2×RTX 3090 (single fly, honest):**
- Faithful dt=0.1 ms, ~166k neurons/~25.6M edges: expect ~0.8–1.5 ms wall per sparse mat-vec step → ~0.07–0.13 sim-s per wall-s (**~8–14× slower than real-time**, single trial), matching the GB10/eonsystems results. Batch many flies to amortize.
- Coarse dt=20 ms: ~1–1.5 ms/step → **~13–20× real-time**, comfortably interactive.
- Memory: connectivity ~0.2–0.4 GB; trivial on 24 GB. The 3090's strong FP32 (use float32!) is well-matched.

**Sparse formats:** CSR for the connectivity (cuSPARSE csrmv, or `torch.sparse_csr_tensor`). Event-driven (spike-list) propagation as in GeNN/Brian2CUDA is more efficient at low firing rates than dense clock-driven; but a dense-ish rate model in PyTorch is simplest to couple to the readout and still fits.

**Use both GPUs:** GPU 0 = neural sim, GPU 1 = physics+render.

**Checkpointing / determinism / logging:** seed everything (numpy, torch, Brian2 `seed()`, MJX PRNG key). Checkpoint neural state (membrane potentials, plastic weights), physics state (particle positions/velocities, temperature/scorch fields), and readout weights. Log per-tick: frame hash, injected currents, spike counts per population, action, reward, wrinkle/burn scores → enables **reproducible funny failures** (re-run a catastrophic silk-scorch exactly).

### F. The demo itself

**Visualization:**
- **Split screen:** left = ironing sim (top-down cloth with wrinkle heatmap + scorch marks + iron); right = live neural activity.
- **Brain view options:** live **spike raster** (matplotlib/`FuncAnimation`) of key populations (LC4, DNa02_L/R, PPL1, PAM, pIP10); a 3D **navis/neuroglancer** render of the MaleCNS with firing neurons lit up; embed FlyWire/MaleCNS neuroglancer scenes. Highlight PPL1 lighting up red the instant the iron scorches the silk blouse.
- **Slow-mo replays** of catastrophic failures (the "silk incident"), a **best-run montage**, and a **leaderboard**: fly-reservoir wrinkle score vs (a) random-action baseline, (b) shuffled-connectome baseline, (c) a human playing with keyboard controls.
- Tools: **navis** (3D neurons, Blender bridge, GPLv3), **neuroglancer** (EM/segmentation), matplotlib (rasters), Blender (final beauty render of the cloth).

**Framing / titling / distribution:** These go viral on X, Reddit (r/programming, r/neuro), Hacker News, and YouTube. Title ideas: "I connected a real fruit-fly brain to a virtual iron," "166,700 neurons vs one silk blouse." What makes them land: a real dataset + a mundane absurd task + honest self-deprecation + a spectacular failure clip.

**Honesty in presentation (mandatory):**
- Caption explicitly: **"This is the fly's *wiring diagram* run as a frozen reservoir. A small linear readout is trained on its activity. The fly did not 'learn to iron' — and there is no living fly and nothing that suffers."**
- Pre-empt the two neuroscientist criticisms: (1) **a connectome is not a functioning brain** — no neuron dynamics, neuromodulation, or plasticity are measured, only wiring; single-neuron/synapse parameters are guessed. (2) **the readout may be doing all the work / the connectome may be an arbitrary reservoir.** Cite the ESA reservoir study (shuffled weights ≈ randomized topology in performance) and the FLM controls (randomized wiring did not hurt). **Run the shuffled-connectome control yourself and show it in the video** — that is what elevates this from meme to "honest meme."

### G. Milestones

| # | Milestone | Deliverable | Est. (1 person) | Kill criterion / off-ramp |
|---|-----------|-------------|-----------------|---------------------------|
| 0 | Environment + data | MaleCNS v1.0 loaded via neuprint-python/navis; connectivity matrix in CSR; DN/LC/KC/MBON/PPL1/PAM cell lists resolved | 2–4 days | If neuprint access blocked, use bulk Feather download from gs:// bucket |
| 1 | Connectome spikes | LIF network runs in Brian2/PyTorch; inject test current, get plausible spike raster; benchmark steps/s on one 3090 | 3–5 days | If dt=0.1 ms too slow, switch to coarse dt or rate model — decide here |
| 2 | Sensory encoder | Frame → hex lattice → LC currents; unit-tested | 2–3 days | Fall back to direct feature→LC injection (skip flyvis) |
| 3 | **MVP shareable artifact:** trivial closed loop | Fly-reservoir + ridge readout balances **CartPole** (or flattens an already-near-flat cloth). Post this early. | 3–5 days | If readout ≤ chance AND shuffled control matches, pivot framing to "honest null result" — still shareable |
| 4 | Cloth sim + wrinkle score | SoftGym ClothFlatten (or MuJoCo flex) with wrinkle/coverage metric, heat/scorch/fabric/pressure model | 1 week | If MuJoCo flex unstable, stay on SoftGym |
| 5 | Full closed loop | Two-process arch; DN→iron-action mapping; reward→PPL1/PAM; readout trained | 1–1.5 weeks | If instability, lock-step + smaller output population |
| 6 | Learning upgrade (optional) | KC→MBON dopamine plasticity (Option 2) | 1 week | Skip if Option 1 already entertaining; it's a "nice to have" |
| 7 | Controls + honesty | Shuffled-connectome baseline, random baseline, human baseline, leaderboard | 3–5 days | Non-negotiable — do not ship without the shuffled control |
| 8 | Viz + video | Split-screen raster/brain render, slow-mo failures, montage, captions | 1 week | — |

**Minimum-viable path:** Milestones 0→1→2→3 (≈2–3 weeks) produces a shareable "fly connectome balances CartPole / flattens cloth" clip. Everything after is polish and comedy.

### H. Risks, ethics, honest expectations

**Technical risks:** cloth solver blow-ups (mitigate: cap timestep, clamp velocities, use SoftGym's stable FleX defaults first); neural sim too slow at dt=0.1 ms (mitigate: coarse dt or rate model, decided at Milestone 1); readout learns nothing above chance (likely for hard control — mitigate by using a scripted expert for supervised readout, or accept a low-skill-but-funny controller).

**Scientific-honesty risks:** overclaiming ("the fly learned to iron"); the readout doing all the work; the connectome functioning as an effectively random reservoir. **Controls are the antidote:** shuffled-weight and randomized-topology reservoirs (ESA/Costi et al. 2025 found shuffling weights ≈ randomizing topology), zeroed-weight and relabeled-node controls (FLM), and "Separating wiring-specific from statistical control of dynamics in a complete connectome" (arXiv 2606.17745) finding that coarse statistics set the dynamical regime while precise wiring sets where activity travels. Report your shuffled-connectome number prominently. (Note: some recent work — e.g., bioRxiv 2026.03.30.715411 — argues non-random brain wiring *does* help under high sparsity; the literature is genuinely mixed, which is itself worth stating honestly.)

**Ethics / no-suffering framing:** a connectome is a static anatomical map; there is no living fly and no evidence of anything resembling experience — say so, as the press did.

**Data licensing/attribution:** MaleCNS v1.0 is **CC-BY 4.0** — cite Berg et al. (2026), *Cell*, and credit FlyEM (HHMI Janelia), University of Cambridge, MRC LMB, and Google Research. FlyWire/hemibrain have their own citation guidelines (Dorkenwald et al., Schlegel et al., Scheffer et al.). flyvis → cite Lappalainen et al. 2024. NeuroMechFly v2/FlyGym → cite Lobato-Rios/Wang et al. 2024 (Nature Methods, s41592-024-02497-y). Respect each package's license (navis GPLv3, fafbseg GPLv3, MuJoCo Apache-2.0).

## Recommendations
1. **Build now on the desktop; skip the DGX Spark.** 2×RTX 3090 is sufficient: GPU 0 neural sim (~0.4 GB), GPU 1 cloth+render. The Spark's GB10 GPU was actually *slower* than a good multicore CPU for the single-trial dt=0.1 ms case, so it buys you nothing here.
2. **Stack:** neuprint-python + navis (data) → PyTorch sparse-CSR rate model *or* Brian2/GeNN LIF (start with whichever you know; PyTorch is easier to couple to the readout) → sklearn Ridge readout → SoftGym ClothFlatten (MVP) then MuJoCo 3.x flex + MJX (hero renders). Study `flybrain`/`philshiu/Drosophila_brain_model`/`eonsystemspbc/fly-brain`/`FlySweeper` but base the legitimate core on the peer-reviewed repos.
3. **Decide timestep at Milestone 1** using your own 3090 benchmark: if you need real-time feel, use coarse dt (10–20 ms); if you want faithful dynamics, run slower-than-real-time offline and speed up in post.
4. **Ship the CartPole/near-flat-cloth MVP within 3 weeks** to get early signal and shareable content; expand to full ironing after.
5. **Never ship without the shuffled-connectome control.** Benchmarks that would change the plan: if real-vs-shuffled Δ is ~0, pivot the framing to "an honest null result about connectome reservoirs" (still a great video); if the readout is at chance even with an expert, simplify the task (flatten one fold, not full ironing).
6. **Caption for honesty every time:** "frozen fly wiring + trained linear readout; the fly did not learn to iron; no living fly, nothing suffers."

## Caveats
- The "~125 million synapses" press figure and the "25,582,938 directed connections" graph figure are different things (the graph is built from 124,177,617 synapses); be explicit about which you use. Neuron count 166,700 is firm. Data v1.0 released June 8, 2026; *Cell* paper published Sept 3, 2026.
- No published RTX 3090 fly-brain LIF benchmark exists; my throughput numbers are triangulated from RTX 4060 laptop, RTX 2080 Ti, RTX 4070, and GB10 (DGX Spark) data, and the DGX Spark figures come from a self-published blog, not peer review — treat as illustrative, verify on your own hardware at Milestone 1.
- The `flybrain` PyPI package is real and functional but is a crypto-token-linked meme project; do not treat it as a maintained scientific dependency.
- flyvis models the *female* optic lobe; MaleCNS is male — cross-space mapping (navis-flybrains) introduces approximation. For a meme demo this is acceptable but worth a caption footnote.
- Whether the connectome contributes anything beyond a random reservoir is genuinely unresolved and the published evidence is mixed (leaning toward "not much" for these reservoir/readout tasks, but with dissenting results under high-sparsity regimes) — this ambiguity is a feature (honest finding) not a bug, but do not overclaim.