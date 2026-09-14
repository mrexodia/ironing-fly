Here's everything, grouped. I've marked with ⚠️ the handful where I'm reconstructing a canonical project URL rather than quoting one that came back verified in the research — worth a click-check.

## Connectome data

**MaleCNS v1.0**
- Project site: https://male-cns.janelia.org
- neuPrint (query + token): https://neuprint.janelia.org
- Paper (Berg et al., *Cell* 2026): https://doi.org/10.1016/j.cell.2026.08.015
- Preprint: https://doi.org/10.1101/2025.10.09.680999
- Bulk data: `gs://flyem-male-cns/v1.0/` (Feather tables, SWC/precomputed skeletons, neo4j dump)

**Other datasets**
- FlyWire codex (female FAFB): https://codex.flywire.ai
- FlyWire paper (Dorkenwald et al., *Nature* 2024): https://doi.org/10.1038/s41586-024-07558-y
- Hemibrain: https://neuprint.janelia.org (dataset `hemibrain:v1.2.1`)
- Curated index of the whole ecosystem: https://github.com/cobanov/awesome-fly

## Data access / analysis tooling
- neuprint-python: https://github.com/connectome-neuprint/neuprint-python
- navis: https://github.com/navis-org/navis — docs https://navis-org.github.io/navis/
- fafbseg-py: https://github.com/navis-org/fafbseg-py ⚠️
- navis-flybrains (cross-template registration): https://github.com/navis-org/navis-flybrains ⚠️
- neuroglancer: https://github.com/google/neuroglancer

## Simulation code to copy from
- `philshiu/Drosophila_brain_model` (the peer-reviewed Brian2 whole-brain LIF — your legitimate base): https://github.com/philshiu/Drosophila_brain_model
- Shiu, Sterne et al., *Nature* 2024: https://doi.org/10.1038/s41586-024-07763-9
- `eonsystemspbc/fly-brain` (multi-backend benchmark harness): https://github.com/eonsystemspbc/fly-brain — readable overview: https://deepwiki.com/eonsystemspbc/fly-brain
- FlySweeper (166,700-neuron LIF, numba + WebGPU): https://github.com/ASHR12/FlySweeper
- `flybrain` on PyPI (the crypto-linked meme package — study, don't depend on): https://pypi.org/project/flybrain/0.1.0/
- DGX Spark benchmark writeup (self-published, not peer-reviewed): https://www.grizzlypeaksoftware.com/articles/p/i-ran-a-fruit-flys-entire-brain-on-my-dgx-spark-then-gave-it-a-body-nxqdy1xn

## Spiking-network simulators
- Brian2: https://github.com/brian-team/brian2 — https://briansimulator.org
- Brian2CUDA: https://github.com/brian-team/brian2cuda — paper: https://doi.org/10.3389/fninf.2022.883700
- GeNN / PyGeNN: https://github.com/genn-team/genn
- NEST: https://github.com/nest/nest-simulator
- Norse: https://github.com/norse/norse
- snnTorch: https://github.com/jeshraghian/snntorch
- BindsNET: https://github.com/BindsNET/bindsnet
- Nengo: https://github.com/nengo/nengo

## Vision model
- flyvis: https://github.com/TuragaLab/flyvis
- Lappalainen et al., *Nature* 2024: https://doi.org/10.1038/s41586-024-07939-3

## Embodied fly (if you want a body rather than an iron)
- FlyGym / NeuroMechFly v2: https://github.com/NeLy-EPFL/flygym
- Paper: https://doi.org/10.1038/s41592-024-02497-y

## Physics / cloth
- MuJoCo: https://github.com/google-deepmind/mujoco
- MuJoCo Warp: https://github.com/google-deepmind/mujoco_warp
- MJX docs: https://mujoco.readthedocs.io/en/stable/mjx.html
- Genesis: https://github.com/Genesis-Embodied-AI/Genesis
- Isaac Lab: https://github.com/isaac-sim/IsaacLab
- SOFA: https://www.sofa-framework.org
- DiffCloth: https://github.com/omegaiota/DiffCloth ⚠️

## Cloth-manipulation benchmarks (your ClothFlatten starting point)
- SoftGym: https://github.com/Xingyu-Lin/softgym
- FlingBot: https://github.com/columbia-ai-robotics/flingbot — https://flingbot.cs.columbia.edu ⚠️
- Cloth Funnels: https://github.com/columbia-ai-robotics/cloth-funnels — https://clothfunnels.cs.columbia.edu ⚠️
- deformable-ravens: https://github.com/DanielTakeshi/deformable-ravens ⚠️
- GarmentLab: https://github.com/GarmentLab/GarmentLab ⚠️
- Deep Fashion3D: https://github.com/GAP-LAB-CUHK-SZ/deepFashion3D ⚠️
- CLOTH3D: https://chalearnlap.cvc.uab.cat/dataset/38/description/ ⚠️

## Mushroom-body learning (for the dopamine-plasticity upgrade)
- Reinforcement prediction errors in the MB (*Nat. Commun.* 2021): https://doi.org/10.1038/s41467-021-22592-4 ⚠️
- MB compartment LDA model (bioRxiv 2022): https://ncbi.nlm.nih.gov/pmc/articles/PMC9660315

## The trend itself + the honesty controls
- awesome-fly (games, demos, tools): https://github.com/cobanov/awesome-fly
- `TerexitariusStomp/fly.ai`: https://github.com/TerexitariusStomp/fly.ai
- "Separating wiring-specific from statistical control of dynamics in a complete connectome": https://arxiv.org/abs/2606.17745
- Visual projection neuron convergence (*Nat. Commun.* 2025): https://www.nature.com/articles/s41467-025-56059-7

- https://github.com/nftechie/doomfly
- https://github.com/ornata/fly - mario 64
