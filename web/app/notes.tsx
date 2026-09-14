import { ChevronRight } from 'lucide-react';
import type { Circuit } from './lab';
export function Notes({ circuit }: { circuit: Circuit | null }) {
  return (
    <section id="assumptions" className="notes">
      <div className="section-heading">
        <h2>What this experiment actually does</h2>
        <span className="tag">OPEN NOTEBOOK</span>
      </div>
      <p>
        A small, real BANC circuit acts as a frozen spiking reservoir.
        Hand-designed wrinkle and heat features stimulate eight descending
        neurons. A fitted linear readout turns 64 motor-neuron spike traces into
        iron movement, pressure and steam. The fly did not learn to iron.
      </p>
      <div className="notes-grid">
        <details>
          <summary>
            Data & circuit boundary <ChevronRight size={16} />
          </summary>
          <p>{circuit?.provenance.selection}</p>
          <p>
            {circuit?.provenance.counts.edges.toLocaleString()} retained
            connections, {circuit?.provenance.counts.synapses.toLocaleString()}{' '}
            synapses. Root IDs stay as strings. The map shows the original
            circuit&apos;s 100 strongest edges; positions are schematic,
            including when a control is running.
          </p>
          <a href="/api/circuit" target="_blank" rel="noreferrer">
            Full circuit, IDs, file hashes and provenance ↗
          </a>
        </details>
        <details>
          <summary>
            Neural assumptions <ChevronRight size={16} />
          </summary>
          <p>
            LIF: 0.5 ms step, 20 ms membrane constant, 5 ms synaptic decay, −52
            mV rest/reset, −45 mV threshold, 2.5 ms refractory, 2 ms delay.
            Weight = synapse count × 0.275 mV × scale. Acetylcholine excites;
            GABA, glutamate and histamine inhibit. Unknown and modulatory
            transmitters contribute zero fast current. Receptor-specific effects
            are not established by these labels.
          </p>
          <p>
            No background drive by default. Spikes are filtered over 100 ms.
            DNa01, DNa02, DNp01 and DNp09 receive deliberately assigned
            engineered channels. This is not a validated sensory pathway.
          </p>
        </details>
        <details>
          <summary>
            Ironing & training limitations <ChevronRight size={16} />
          </summary>
          <p>
            The cloth is a 40 × 40 height field with heuristic heat diffusion,
            flattening and scorch. It does not simulate folding, fabric
            mechanics, muscles or a fly body. Temperature thresholds are
            fictional parameters, not garment-care advice.
          </p>
          <p>
            Only the ridge readout is trained, using 420 artificial feature
            probes with scripted targets. A 100 ms washout precedes each sample.
            A validation split selects regularization; controls use separate
            task seeds. No recurrent weights are learned.
          </p>
        </details>
      </div>
      <div className="sources">
        <span>BUILT ON</span>
        <a
          href="https://www.nature.com/articles/s41586-026-10735-w"
          target="_blank"
          rel="noreferrer"
        >
          BANC · Bates, Phelps, Kim, Yang et al. ↗
        </a>
        <a
          href="https://github.com/philshiu/Drosophila_brain_model"
          target="_blank"
          rel="noreferrer"
        >
          LIF precedent · Shiu et al. ↗
        </a>
        <a
          href="https://github.com/sjcabs/fly_connectome_data_tutorial"
          target="_blank"
          rel="noreferrer"
        >
          BANC data tutorial ↗
        </a>
        <a
          href="https://github.com/PtPavloTkachenko/fly-brain-spectacles"
          target="_blank"
          rel="noreferrer"
        >
          Related work · CyberFly ↗
        </a>
      </div>
    </section>
  );
}
