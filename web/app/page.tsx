'use client';
import { useEffect, useRef, useState } from 'react';
import {
  Bug,
  Play,
  Pause,
  RotateCcw,
  Download,
  ArrowUpRight,
  Activity,
  Settings2,
  FlaskConical,
  ChevronRight,
  Box,
  Map,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import {
  api,
  initial,
  names,
  Choice,
  Range,
  ClothView,
  Raster,
  Network,
  type Circuit,
  type Frame,
  type Settings,
  type Benchmark,
  type Trial,
} from './lab';
import { Notes } from './notes';
import { SceneView } from './scene-view';

export default function Home() {
  const [circuit, setCircuit] = useState<Circuit | null>(null),
    [frame, setFrame] = useState<Frame | null>(null),
    [settings, setSettings] = useState<Settings>(initial),
    [running, setRunning] = useState(false),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState('Connecting to the simulation…'),
    [error, setError] = useState(''),
    [heatmap, setHeatmap] = useState(false),
    [show3d, setShow3d] = useState(true),
    [trial, setTrial] = useState<Trial | null>(null),
    [benchmark, setBenchmark] = useState<Benchmark | null>(null),
    [sessionId, setSessionId] = useState(''),
    [dirty, setDirty] = useState(false);
  const sid = useRef(''),
    runningRef = useRef(false),
    generation = useRef(0),
    keys = useRef(new Set<string>()),
    press = useRef(false),
    steam = useRef(false);
  const change = (k: keyof Settings, v: string | number) => {
    setSettings((s) => ({ ...s, [k]: v }));
    setDirty(true);
    setRunning(false);
    runningRef.current = false;
  };
  async function reset(s = settings) {
    runningRef.current = false;
    setRunning(false);
    const gen = ++generation.current;
    setBusy(true);
    setError('');
    setMessage('Preparing circuit and fitting readout if needed…');
    try {
      const result = await api<Frame & { id: string }>('session', s);
      if (gen !== generation.current) return;
      sid.current = result.id;
      setSessionId(result.id);
      setFrame(result);
      setDirty(false);
      setMessage('Ready to iron');
    } catch (e) {
      setError(String(e));
      setMessage('Simulation unavailable');
    } finally {
      if (gen === generation.current) setBusy(false);
    }
  }
  useEffect(() => {
    api<Circuit>('circuit')
      .then(setCircuit)
      .catch((e) => setError(String(e)));
    api<Benchmark>('benchmark')
      .then(setBenchmark)
      .catch(() => {});
    // Initialize from an external request after the effect has subscribed.
    const timer = setTimeout(() => {
      void reset(initial);
    }, 0);
    return () => {
      clearTimeout(timer);
    };
  }, []);
  useEffect(() => {
    runningRef.current = running;
    if (!running) return;
    let cancelled = false;
    const gen = generation.current;
    async function tick() {
      if (cancelled || !runningRef.current) return;
      try {
        const a = [
          Number(keys.current.has('ArrowRight')) -
            Number(keys.current.has('ArrowLeft')),
          Number(keys.current.has('ArrowDown')) -
            Number(keys.current.has('ArrowUp')),
          press.current ? 1 : 0,
          steam.current ? 1 : 0,
        ];
        const result = await api<Frame>(`session/${sid.current}/step`, {
          ticks: 5,
          manual: a,
        });
        if (gen !== generation.current) return;
        setFrame(result);
        if (!cancelled) setMessage('Experiment running');
        if (!cancelled && runningRef.current) setTimeout(tick, 35);
      } catch (e) {
        setError(String(e));
        setRunning(false);
        runningRef.current = false;
      }
    }
    void tick();
    return () => {
      cancelled = true;
    };
  }, [running]);
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (
        (e.target as HTMLElement).closest(
          'input,button,[role="slider"],[role="combobox"]',
        )
      )
        return;
      if (
        settings.controller === 'manual' &&
        ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)
      ) {
        e.preventDefault();
        keys.current.add(e.key);
      }
    };
    const up = (e: KeyboardEvent) => keys.current.delete(e.key);
    const blur = () => keys.current.clear();
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    window.addEventListener('blur', blur);
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
      window.removeEventListener('blur', blur);
    };
  }, [settings.controller]);
  async function runTrial() {
    setBusy(true);
    setError('');
    setMessage('Comparing DNa02 stimulation with baseline…');
    try {
      setTrial(await api<Trial>('neural-trial', settings));
      setMessage('Neural comparison complete');
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  const metrics = frame?.cloth,
    selectedControls = (benchmark?.controls || []).filter(
      (c) => c.fabric === settings.fabric,
    );
  const summary = ['real', 'shuffled', 'zero', 'random', 'expert'].map(
    (controller) => {
      const rows = selectedControls.filter((c) => c.controller === controller);
      return {
        controller,
        smooth:
          rows.reduce((a, b) => a + b.smooth_percent, 0) / (rows.length || 1),
        scorch:
          rows.reduce((a, b) => a + b.scorch_percent, 0) / (rows.length || 1),
      };
    },
  );
  const topMotors = circuit
    ? [...circuit.motors]
        .sort(
          (a, b) =>
            (frame?.neural.rates[b] || 0) - (frame?.neural.rates[a] || 0),
        )
        .slice(0, 4)
    : [];
  return (
    <main>
      <header className="topbar">
        <Link href="/" className="brand">
          <span className="brand-icon">
            <Bug size={24} />
          </span>
          ironing fly<span className="version">EXPERIMENT 001</span>
        </Link>
        <div className="connection">
          <span className={frame ? 'dot' : 'dot off'} />
          {frame ? 'BANC v888 · connected' : 'Connecting'}
          <a href="#assumptions" aria-label="Read experiment notes">
            <ArrowUpRight size={18} />
          </a>
        </div>
      </header>
      <div className="workspace">
        <section className="heading">
          <div>
            <div className="eyebrow">
              A VERY SMALL BRAIN. A VERY ORDINARY CHORE.
            </div>
            <h1>
              The laundry experiment<span>.</span>
            </h1>
            <p>Real fly wiring. A trained readout. One virtual iron.</p>
          </div>
          <a className="text-link" href="#assumptions">
            How this works <ArrowUpRight size={17} />
          </a>
        </section>
        <div className="lab-grid">
          <section className="experiment">
            <div className="panel-top">
              <div className="panel-title">
                <span className="dot" />
                IRONING BOARD{' '}
                <span className="tag">
                  {names[frame?.cloth.fabric || settings.fabric]}
                </span>
              </div>
              <div className="board-tools">
                <button
                  className="view-toggle"
                  aria-pressed={show3d}
                  onClick={() => setShow3d(!show3d)}
                >
                  {show3d ? <Map size={15} /> : <Box size={15} />}
                  {show3d ? '2D map' : '3D scene'}
                </button>
                <button
                  className={'view-toggle ' + (heatmap ? 'active' : '')}
                  onClick={() => setHeatmap(!heatmap)}
                  aria-pressed={heatmap}
                >
                  {heatmap ? 'Temperature map' : 'Wrinkle view'}{' '}
                  <Settings2 size={15} />
                </button>
              </div>
            </div>
            <div className="board">
              {show3d ? (
                <SceneView frame={frame} heatmap={heatmap} />
              ) : (
                <ClothView frame={frame} heatmap={heatmap} />
              )}
              {!frame && (
                <div className="board-loading">
                  {error
                    ? 'Start the local simulation API to connect.'
                    : 'Preparing the first experiment…'}
                </div>
              )}
              <div className="board-caption">
                <span>
                  <i className="target-dot" /> Selected wrinkle patch
                </span>
                <span>
                  {frame?.controller === 'manual'
                    ? 'YOU ARE AT THE CONTROLS'
                    : show3d
                      ? 'FLY ANIMATION IS ILLUSTRATIVE'
                      : 'FROZEN CIRCUIT → MOTOR READOUT'}
                </span>
              </div>
            </div>
            <div className="metrics">
              <div>
                <span>Wrinkles removed</span>
                <strong>
                  {(metrics?.smooth_percent || 0).toFixed(1)}
                  <small>%</small>
                </strong>
                <div className="meter">
                  <i style={{ width: `${metrics?.smooth_percent || 0}%` }} />
                </div>
              </div>
              <div>
                <span>Scorch damage</span>
                <strong
                  className={
                    (metrics?.scorch_percent || 0) > 0.1 ? 'warning' : ''
                  }
                >
                  {(metrics?.scorch_percent || 0).toFixed(2)}
                  <small>%</small>
                </strong>
                <span className="metric-note">Accumulated fabric damage</span>
              </div>
              <div>
                <span>Elapsed simulation</span>
                <strong>
                  {(metrics?.time || 0).toFixed(1)}
                  <small>s</small>
                </strong>
                <span className="metric-note">20 ms per control step</span>
              </div>
            </div>
            <div className="transport">
              <div className="transport-buttons">
                <Button
                  className="run-button"
                  disabled={busy || !frame || dirty}
                  onClick={() => {
                    setRunning(!running);
                    setMessage(running ? 'Paused' : 'Experiment running');
                  }}
                >
                  {running ? <Pause size={16} /> : <Play size={16} />}{' '}
                  {running ? 'Pause' : 'Run experiment'}
                </Button>
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={() => reset()}
                  title="Reset with current settings"
                >
                  <RotateCcw size={16} />
                  Reset
                </Button>
              </div>
              <output className="status">
                {busy
                  ? 'Working…'
                  : dirty
                    ? 'Reset to apply'
                    : running
                      ? 'Running'
                      : frame
                        ? 'Paused'
                        : 'Connecting'}
              </output>
              <a
                className={'export ' + (!frame ? 'disabled' : '')}
                href={frame ? `/api/session/${sessionId}/export` : undefined}
                download
              >
                <Download size={16} />
                <span>Export</span>
              </a>
            </div>
          </section>
          <aside className="control-panel">
            <div className="panel-top">
              <span className="panel-title">EXPERIMENT CONTROLS</span>
              <FlaskConical size={17} />
            </div>
            <div className="controls-body">
              <Choice
                label="Controller"
                value={settings.controller}
                values={[
                  'real',
                  'shuffled',
                  'zero',
                  'random',
                  'expert',
                  'manual',
                ]}
                onChange={(v) => change('controller', v)}
                disabled={busy}
              />
              <p className="control-note">
                {settings.controller === 'real'
                  ? 'Frozen BANC circuit + fitted linear motor readout.'
                  : settings.controller === 'shuffled'
                    ? 'Shuffled target partners; separately fitted readout.'
                    : settings.controller === 'manual'
                      ? 'Arrow keys move. Toggle pressure and steam below.'
                      : 'Comparison controller. Neural activity is measured separately.'}
              </p>
              <div className="pair">
                <Choice
                  label="Garment"
                  value={settings.garment}
                  values={['shirt', 'trousers', 'patch']}
                  onChange={(v) => change('garment', v)}
                  disabled={busy}
                />
                <Choice
                  label="Fabric"
                  value={settings.fabric}
                  values={['cotton', 'silk', 'wool']}
                  onChange={(v) => change('fabric', v)}
                  disabled={busy}
                />
              </div>
              <Range
                label="Iron temperature"
                value={settings.temperature}
                min={60}
                max={240}
                unit="°C"
                onChange={(v) => change('temperature', v)}
                disabled={busy}
              />
              <div className="fabric-note">
                {settings.fabric === 'silk'
                  ? 'Silk scorches above 120°C in this toy model.'
                  : settings.fabric === 'wool'
                    ? 'Wool smooths more effectively with steam.'
                    : 'Cotton is the most forgiving starting point.'}
              </div>
              <div className="divider" />
              <Range
                label="Input stimulation"
                value={settings.stimulus_hz}
                min={0}
                max={300}
                step={25}
                unit="Hz max"
                onChange={(v) => change('stimulus_hz', v)}
                disabled={busy}
              />
              <div className="pair compact">
                <Range
                  label="Weight scale"
                  value={settings.weight_scale}
                  min={0}
                  max={8}
                  step={0.5}
                  unit="×"
                  onChange={(v) => change('weight_scale', v)}
                  disabled={busy}
                />
                <Range
                  label="Connection cutoff"
                  value={settings.cutoff}
                  min={1}
                  max={30}
                  unit="syn."
                  onChange={(v) => change('cutoff', v)}
                  disabled={busy}
                />
              </div>
              <label className="seed">
                Random seed
                <input
                  aria-label="Random seed"
                  type="number"
                  min={0}
                  max={1000000}
                  value={settings.seed}
                  disabled={busy}
                  onChange={(e) =>
                    change(
                      'seed',
                      Math.max(0, Math.min(1000000, Number(e.target.value))),
                    )
                  }
                />
              </label>
              {settings.controller === 'manual' && (
                <div className="manual-controls">
                  <Button
                    variant="outline"
                    onClick={() => {
                      press.current = !press.current;
                      setMessage(press.current ? 'Pressure on' : 'Iron lifted');
                    }}
                  >
                    Toggle pressure
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      steam.current = !steam.current;
                      setMessage(steam.current ? 'Steam on' : 'Steam off');
                    }}
                  >
                    Toggle steam
                  </Button>
                  <div className="direction-pad">
                    {[
                      ['↑', 'ArrowUp'],
                      ['←', 'ArrowLeft'],
                      ['↓', 'ArrowDown'],
                      ['→', 'ArrowRight'],
                    ].map(([symbol, key]) => (
                      <Button
                        key={key}
                        variant="outline"
                        aria-label={`Move ${key}`}
                        onPointerDown={() => keys.current.add(key)}
                        onPointerUp={() => keys.current.delete(key)}
                        onPointerLeave={() => keys.current.delete(key)}
                      >
                        {symbol}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
              <button className="apply" disabled={busy} onClick={() => reset()}>
                {busy
                  ? 'Preparing experiment…'
                  : dirty
                    ? 'Apply settings & reset'
                    : 'New run, same seed'}
                <ChevronRight size={16} />
              </button>
              <output className="detail-status">{message}</output>
            </div>
          </aside>
        </div>
        {error && (
          <div role="alert" className="error">
            {error}
          </div>
        )}
        <section className="neural-grid">
          <div className="raster-panel">
            <div className="panel-top">
              <span className="panel-title">
                <Activity size={16} />
                LIVE NEURAL ACTIVITY
              </span>
              <span className="subtle">
                {circuit?.nodes.length || '—'} neurons · last 1,000 ms
              </span>
            </div>
            <Raster frame={frame} circuit={circuit} />
            <div className="raster-legend">
              <span>
                <i style={{ background: '#d3f087' }} />
                Descending inputs
              </span>
              <span>
                <i style={{ background: '#5d8b74' }} />
                VNC intermediates
              </span>
              <span>
                <i style={{ background: '#a5d9e8' }} />
                Motor outputs
              </span>
              <span className="raster-time">
                {(frame?.neural.time_ms || 0).toFixed(0)} ms
              </span>
            </div>
          </div>
          <div className="circuit-panel">
            <div className="panel-top">
              <span className="panel-title">CIRCUIT MAP</span>
              <span className="subtle">Schematic</span>
            </div>
            <Network circuit={circuit} frame={frame} />
            <div className="circuit-labels">
              <span>8 inputs</span>
              <span>160 VNC</span>
              <span>64 motors</span>
            </div>
          </div>
        </section>
        <section className="results-grid">
          <div>
            <div className="section-heading">
              <h2>Does the wiring help?</h2>
              <span className="tag">CONTROL EXPERIMENT</span>
            </div>
            <p className="section-copy">
              Same fabric, three held-out seeds, 12 seconds per run. Readouts
              fitted separately. These results use default settings and a
              T-shirt.
            </p>
            {selectedControls.length ? (
              <>
                <div className="comparison">
                  {summary.map((row) => (
                    <div key={row.controller} className="comparison-row">
                      <span>{names[row.controller]}</span>
                      <div className="comparison-track">
                        <i
                          style={{
                            width: `${row.smooth}%`,
                            background:
                              row.controller === 'real' ? '#d3f087' : '#6e8d79',
                          }}
                        />
                      </div>
                      <strong>{row.smooth.toFixed(1)}%</strong>
                      <small>{row.scorch.toFixed(2)}% scorch</small>
                    </div>
                  ))}
                </div>
                <p className="control-note">
                  Mean wrinkles removed; longer bars are better. A small
                  difference does not establish an advantage from biological
                  wiring.
                </p>
              </>
            ) : (
              <p className="empty">
                The reproducible comparison is being prepared. Live experiments
                are available above.
              </p>
            )}
          </div>
          <div>
            <div className="section-heading">
              <h2>Motor response</h2>
              <span className="tag">FILTERED SPIKES</span>
            </div>
            <div className="motor-list">
              {topMotors.map((i) => (
                <div key={i}>
                  <span title={circuit!.nodes[i].id}>
                    {circuit!.nodes[i].cell_type}
                    <small>
                      {circuit!.nodes[i].side} ·{' '}
                      {circuit!.nodes[i].body_part_effector ||
                        'identified motor'}
                    </small>
                  </span>
                  <strong>
                    {(frame?.neural.rates[i] || 0).toFixed(1)} <small>Hz</small>
                  </strong>
                </div>
              ))}
            </div>
            <Button
              variant="outline"
              className="trial-button"
              onClick={runTrial}
              disabled={busy || running}
            >
              <FlaskConical size={16} />
              Compare DNa02 with baseline
            </Button>
            {trial && (
              <div className="trial-result">
                <strong>DNa02 · {trial.stimulated.stimulus_hz} Hz input</strong>
                <span>
                  Mean motor firing:{' '}
                  {trial.baseline.diagnostics.motor_mean_hz.toFixed(2)} →{' '}
                  {trial.stimulated.diagnostics.motor_mean_hz.toFixed(2)} Hz
                </span>
                <button
                  onClick={() => {
                    const url = URL.createObjectURL(
                      new Blob([JSON.stringify(trial, null, 2)], {
                        type: 'application/json',
                      }),
                    );
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'dna02-trial.json';
                    a.click();
                    setTimeout(() => URL.revokeObjectURL(url), 1000);
                  }}
                >
                  Download trial and spike times <Download size={14} />
                </button>
              </div>
            )}
          </div>
        </section>
        <Notes circuit={circuit} />
        <footer>
          <span>
            <Bug size={16} />
            ironing fly
          </span>
          <span>
            Local experiment · no living fly · anatomy constrained, physiology
            assumed
          </span>
          <span>SEED {settings.seed}</span>
        </footer>
      </div>
    </main>
  );
}
