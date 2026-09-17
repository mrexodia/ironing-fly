'use client';
import { useEffect, useState } from 'react';
import { api, names, type Frame } from './lab';

type Result = {
  condition: string;
  seed: number;
  seconds?: number;
  fabric?: string;
  smooth_percent: number;
  scorch_percent: number;
  coverage_percent?: number;
  travel: number;
  network_spikes: number;
};
type Comparison = {
  seconds: number;
  rows: Result[];
  labels?: Record<string, string>;
  evaluation_seeds?: number[];
  extended_rows?: Result[];
  causal_controls?: Result[];
};

export function ConnectomePanel({ frame }: { frame: Frame }) {
  const [comparison, setComparison] = useState<Comparison | null>(null);
  useEffect(() => {
    api<Comparison>('full-benchmark')
      .then(setComparison)
      .catch(() => {});
  }, []);
  const d = frame.neural.diagnostics;
  const retina = frame.senses?.retina || [];
  return (
    <section className="connectome-panel">
      <div className="section-heading">
        <h2>Inside the connectome</h2>
        <span className="tag">NO TRAINED READOUT</span>
      </div>
      <p className="section-copy">
        {frame.model?.neurons.toLocaleString()} neurons ·{' '}
        {frame.model?.edges.toLocaleString()} connections pass the cutoff ·{' '}
        {d.device || d.backend || 'Preparing'} ·{' '}
        {(d.sim_seconds_per_wall_second || 0).toFixed(2)}× real time
      </p>
      {d.backend_note && <p className="control-note">{d.backend_note}</p>}
      {d.high_rate && (
        <p className="control-note warning">
          Some cells exceed 300 Hz averaged over this run. The chosen gains are
          exploratory, not physiological calibration.
        </p>
      )}
      <div className="senses-grid">
        <div>
          <h3>What it sees</h3>
          <div
            className="retina"
            aria-label="16 by 8 local luminance retina, forward at the bottom"
          >
            {Array.from({ length: 128 }, (_, i) => (
              <span
                key={i}
                style={{
                  background: `rgb(${Math.round((retina[i] || 0) * 255)} ${Math.round((retina[i] || 0) * 255)} ${Math.round((retina[i] || 0) * 255)})`,
                }}
              />
            ))}
          </div>
          <p className="control-note">
            Local view ahead of the iron; farther away is at the bottom. Edge
            contrast and image change stimulate visual neurons. No fabric label
            or best-wrinkle coordinates. Lookahead:{' '}
            {frame.senses?.lookahead_board_widths ??
              (frame.model?.decoder_version === 3 ? 0.25 : 0.45)}{' '}
            board widths.
          </p>
          <p className="control-note">
            Contact {(frame.senses?.contact || 0).toFixed(2)} · local
            temperature {(frame.senses?.local_temperature_c || 22).toFixed(1)}°C
          </p>
        </div>
        <div>
          <h3>Neural output → iron</h3>
          <div className="population-grid">
            <span>Population</span>
            <span>Left Hz</span>
            <span>Right Hz</span>
            {[
              'DNa02',
              'DNp66',
              'DNp03',
              'DNp09',
              'MDN',
              'DNp01',
              'front_motor',
            ].map((name) => (
              <Population
                key={name}
                name={name}
                rates={frame.populations_hz || {}}
              />
            ))}
          </div>
          <p className="control-note">
            {frame.model?.decoder_version === 3
              ? 'Coverage push: shorter visual lookahead and stronger pushing from leg-motor spikes. Descending neurons still steer and modulate movement.'
              : frame.model?.decoder_version === 2
                ? 'Calibrated adapter: leg-motor spikes provide pushing, pressure and steam; descending neurons steer and modulate movement.'
                : 'Original adapter: descending neurons provide all movement; leg-motor spikes provide weak pressure and steam.'}{' '}
            Silent outputs produce zero action.{' '}
            {(d.network_spikes || 0).toLocaleString()} network spikes so far.
          </p>
        </div>
        <div>
          <h3>Measured ironing performance</h3>
          <p className="control-note">
            Disconnect or shuffle the wiring, or silence output neurons in the
            controls above. Reset to compare the same seed. Neural causation
            does not establish useful ironing.
          </p>
          {comparison?.rows?.length ? (
            <>
              <table className="connectome-results">
                <caption>
                  Recorded cotton-shirt trials · {comparison.seconds}s · scale 2
                  · 150 Hz · cutoff 5
                </caption>
                <thead>
                  <tr>
                    <th>Condition</th>
                    <th>Smoothed</th>
                    <th>Covered</th>
                    <th>Scorch</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    'before',
                    'real',
                    'shuffled',
                    'zero',
                    'ablated',
                    'silent',
                  ].map((condition) => {
                    const rows = comparison.rows.filter(
                      (r) =>
                        r.condition === condition &&
                        (!r.fabric || r.fabric === 'cotton'),
                    );
                    if (!rows.length) return null;
                    return (
                      <tr key={condition}>
                        <td>
                          {comparison.labels?.[condition] ||
                            (condition === 'real'
                              ? 'Calibrated adapter'
                              : names[condition]) ||
                            (condition === 'ablated'
                              ? 'Outputs silenced'
                              : 'No sensory input')}
                          <small> n={rows.length}</small>
                        </td>
                        <td>
                          {(
                            rows.reduce((n, r) => n + r.smooth_percent, 0) /
                            rows.length
                          ).toFixed(2)}
                          %
                        </td>
                        <td>
                          {(
                            rows.reduce(
                              (n, r) => n + (r.coverage_percent || 0),
                              0,
                            ) / rows.length
                          ).toFixed(1)}
                          %
                        </td>
                        <td>
                          {(
                            rows.reduce((n, r) => n + r.scorch_percent, 0) /
                            rows.length
                          ).toFixed(1)}
                          %
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <p className="control-note">
                Profiles use matched seeds{' '}
                {comparison.evaluation_seeds?.join(', ') || '61, 62, 63'},
                separate from tuning seed 42. Other checks use seed{' '}
                {comparison.evaluation_seeds?.[0] || 61}. Covered means touched
                with pressure above 0.1. These results measure the adapter
                change, not a biological advantage. Values do not update with
                live settings.
              </p>
              {comparison.extended_rows?.length ? (
                <p className="control-note">
                  Longer run ({comparison.extended_rows[0].seconds}s, one
                  matched seed):{' '}
                  {comparison.extended_rows
                    .map(
                      (r) =>
                        `${comparison.labels?.[r.condition] || r.condition} ${r.smooth_percent.toFixed(1)}% smoothed`,
                    )
                    .join(' → ')}
                  .
                </p>
              ) : null}
              {comparison.causal_controls?.length ? (
                <p className="control-note">
                  {comparison.causal_controls[0].seconds}s causal checks:{' '}
                  {comparison.causal_controls
                    .map(
                      (r) =>
                        `${r.condition === 'ablated' ? 'outputs silenced' : r.condition === 'silent' ? 'no sensory input' : 'disconnected'}: ${r.travel.toFixed(3)} travel, ${r.smooth_percent.toFixed(1)}% smoothed`,
                    )
                    .join('; ')}
                  .
                </p>
              ) : null}
            </>
          ) : (
            <p className="control-note">
              The full-mode comparison has not been generated yet.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

function Population({
  name,
  rates,
}: {
  name: string;
  rates: Record<string, number>;
}) {
  return (
    <>
      <span>{name === 'front_motor' ? 'Front-leg motor' : name}</span>
      <strong>{(rates[`${name}_left`] || 0).toFixed(1)}</strong>
      <strong>{(rates[`${name}_right`] || 0).toFixed(1)}</strong>
    </>
  );
}
