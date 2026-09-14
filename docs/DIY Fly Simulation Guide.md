# DIY Fly Simulation Guide :)&nbsp; Agent instructions at the end

1. Simulate your fly 🪰

Start with BANC: a female fly connectome with \~158,000 neurons in the v888 Codex release. The first brain and CNS connectome, published in Nature this June.

Here’s a path from the wiring diagram to your first experiment.&nbsp;

[Explore BANC](https://codex.flywire.ai/)

2. &nbsp;Get the data.

Start with two BANC v888 files: neuron metadata and the aggregated edge list—who connects to whom, with how many synapses.

Use matching versions and preserve neuron IDs exactly. Public compiled downloads need no CAVE login.

[Files \+ loading examples](https://github.com/sjcabs/fly_connectome_data_tutorial/blob/main/data/dataset_documentation/banc_data.md)

3. &nbsp;Pick your tools.

Python: pip install banc  
[Python package](https://github.com/jasper-tms/the-BANC-fly-connectome)

R: bancr  
[R package](https://natverse.org/bancr/)

[Python \+ R tutorial](https://github.com/sjcabs/fly_connectome_data_tutorial)

Using a coding agent? Give it these docs and ask it to inspect the data schema before building.

4. &nbsp;Choose a model.

Shiu et al. used a leaky integrate-and-fire model of the FAFB brain to make experimentally tested predictions.x

Their code is a starting point. Adapting it to BANC requires new validation.

[Paper](https://www.nature.com/articles/s41586-024-07763-9) · [Original code](https://github.com/philshiu/Drosophila_brain_model)

5. &nbsp;First experiment: choose a descending neuron type and trace its VNC circuit to identified motor neurons.

Compare simulated activity with and without stimulation. Sweep input rates and connection thresholds.

Which responses survive changes in your assumptions?

&nbsp;

&nbsp;

&nbsp;

Share your code, assumptions and BANC version\!

[Bates, Phelps, Kim et al., Nature 2026](https://www.nature.com/articles/s41586-026-10735-w)

&nbsp;

&nbsp;

&nbsp;

&nbsp;

&nbsp;

Build with BANC: an Astra starter guide 🪰

Use Astra to turn a real fly wiring diagram into an interactive neural simulation. You describe what you want to explore; Astra handles the code, dependencies, data loading, tests and interface.

Start a coding session with Astra selected, then paste the instructions below.

—— BEGIN AGENT INSTRUCTIONS ——

You are building an interactive, connectome-based simulation using BANC, a female Drosophila brain-and-nerve-cord dataset.

The user should not need to write code or manually prepare data. Take ownership of implementation, troubleshoot errors and deliver a working local preview. Make reasonable choices and proceed; ask only when a missing credential or consequential user decision genuinely blocks progress.

Your first goal:

Build a reproducible experiment that stimulates an identified descending neuron type, simulates activity through its connected ventral nerve cord circuitry, and measures responses in identified motor neurons.

Start with a tractable circuit and a working experiment. Expand after that works. Treat this as a model constrained by anatomical data, with explicit assumptions about physiology.

Read these sources first

BANC data files, schemas and loading examples:  
[Dataset documentation](https://github.com/sjcabs/fly_connectome_data_tutorial/blob/main/data/dataset_documentation/banc_data.md)

Python and R connectome tutorial:  
[Tutorial repository](https://github.com/sjcabs/fly_connectome_data_tutorial)

BANC Python tools:  
[Python repository](https://github.com/jasper-tms/the-BANC-fly-connectome)

BANC R tools and public data access:  
[bancr documentation](https://natverse.org/bancr/)

Interactive dataset explorer:  
[FlyWire Codex](https://codex.flywire.ai/)

BANC publication:  
[Bates, Phelps, Kim et al., Nature 2026](https://www.nature.com/articles/s41586-026-10735-w)

Simulation precedent:  
[Shiu et al., Nature 2024](https://www.nature.com/articles/s41586-024-07763-9)

Original simulation implementation:  
[Shiu model repository](https://github.com/philshiu/Drosophila_brain_model)

The Shiu implementation uses FAFB data. Inspect its equations, parameters and validation before adapting it to BANC. Do not assume that changing the connectivity file produces a validated BANC model.

1. Load and inspect the real data

Prefer public compiled downloads for the initial build. Interactive Codex browsing requires Google sign-in; live CAVE access has separate authentication requirements.

Documented BANC v888 data location:

gs://lee-lab\_brain-and-nerve-cord-fly-connectome/compiled\_data/banc\_888/

Initial files:

• banc\_888\_meta.feather  
• banc\_888\_edgelist\_simple\_v3.feather

Verify current availability and schemas against the documentation before using them. Use the aggregated edge list initially; download individual synapses or neuron meshes only if needed.

Inspect actual columns, ID types, missing annotations, duplicate records and connection-count semantics. Preserve root IDs losslessly, including across JavaScript boundaries. Do not assume every metadata row represents a neuron suitable for the model.

Record the materialization, file versions, download sources and filtering choices. Cache downloads. Keep metadata and connectivity compatible.

If access fails, diagnose the documented public route. Never silently substitute FAFB, MaleCNS or synthetic data.

2. Choose a useful first circuit

Find descending neuron types with usable annotations and connectivity to identified VNC motor pathways.

Select one that supports a manageable first experiment. Explain the selection briefly. Derive IDs and motor targets from the data; do not invent them or transfer IDs from another dataset.

Retain relevant intermediate neurons and recurrent connections within the selected network. Document the circuit boundary and omitted inputs. Check that the selected network includes paths from stimulated neurons to the chosen outputs.

3. Implement the simulation

Use a transparent leaky integrate-and-fire implementation, drawing on the Shiu model where appropriate. Select a backend suited to the available hardware and explain the choice briefly.

Make these assumptions explicit and configurable:

• Mapping from synapse counts to model weights.  
• Neurotransmitter-to-effect rules and handling of unknown or modulatory transmitters.  
• Membrane and synaptic time constants.  
• Firing thresholds, resets, delays and refractory periods.  
• Background activity and stimulation protocol.  
• Connection filtering and circuit boundaries.

Neurotransmitter predictions alone do not establish receptor-specific effects. Synapse counts alone do not establish physiological weights.

Treat stimulation rates and synapse-count cutoffs as parameters to investigate, not established BANC defaults.

4. Run a meaningful first experiment

Compare an unstimulated baseline with stimulation of the chosen descending neuron type.

Measure:

• Spike timing across the selected network.  
• Motor-neuron firing rates and changes from baseline.  
• Responses across several stimulation strengths.  
• Sensitivity to connection filtering and weight scaling.

Use reproducible random seeds. Check for silent networks, runaway activity and numerical instability. Explain what the checks establish and what remains unvalidated.

Do not claim that motor-neuron firing demonstrates walking or flying. Movement requires additional muscle, body and sensory-feedback models.

5. Build an interface people can explore

Create a clear, inviting interface with:

• The selected circuit and identifiable input/output neurons.  
• Run, pause and reset controls.  
• Stimulation controls with units.  
• A spike raster and motor-output comparison.  
• A concise explanation of what the experiment asks.  
• Accessible assumptions and data provenance.  
• Export of results and experiment settings.

Show actual simulation outputs. If a graph layout is schematic, label it as schematic. Use anatomical geometry only when retrieved from the dataset.

Keep technical setup out of the user’s workflow. The user should be able to open the preview, change a stimulus and see what changes.

6. Deliver and verify

Run the application and verify the complete interaction from changing a stimulus to viewing and exporting results.

Deliver:

• A working local preview.  
• Source code and dependency instructions.  
• A reproducible experiment configuration.  
• A short README with sources, assumptions and limitations.  
• A brief report of the selected circuit, observed model behavior and verification performed.

Do not stop after proposing a plan. Build the smallest complete experiment, verify it and show it to the user. If blocked, identify the exact blocker and finish all useful work that remains possible.

—— END AGENT INSTRUCTIONS ——

&nbsp;