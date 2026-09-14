'use client';
import { useEffect, useRef } from 'react';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
export type Neuron = {
  id: string;
  cell_type: string;
  super_class: string;
  side: string;
  body_part_effector: string;
};
export type Circuit = {
  nodes: Neuron[];
  edges: number[][];
  inputs: number[];
  motors: number[];
  provenance: {
    selection: string;
    counts: { edges: number; synapses: number };
  };
};
export type Frame = {
  cloth: {
    time: number;
    fabric: string;
    garment: string;
    n: number;
    mask: number[];
    wrinkle: number[];
    heat: number[];
    scorch: number[];
    iron: number[];
    target: number[];
    pressure: number;
    steam: number;
    smooth_percent: number;
    scorch_percent: number;
  };
  neural: {
    time_ms: number;
    spikes: number[][];
    rates: number[];
    diagnostics: { motor_mean_hz: number; silent: boolean; high_rate: boolean };
  };
  controller: string;
  action: number[];
  readout: unknown;
};
export type Control = {
  fabric: string;
  controller: string;
  smooth_percent: number;
  scorch_percent: number;
};
export type Benchmark = { controls: Control[] };
export type Trial = {
  baseline: { diagnostics: { motor_mean_hz: number } };
  stimulated: { stimulus_hz: number; diagnostics: { motor_mean_hz: number } };
};
export type Settings = {
  seed: number;
  fabric: string;
  garment: string;
  temperature: number;
  controller: string;
  stimulus_hz: number;
  weight_scale: number;
  cutoff: number;
  background_hz: number;
};
export const initial: Settings = {
  seed: 42,
  fabric: 'cotton',
  garment: 'shirt',
  temperature: 170,
  controller: 'real',
  stimulus_hz: 150,
  weight_scale: 4,
  cutoff: 5,
  background_hz: 0,
};
export const names: Record<string, string> = {
  real: 'Fly connectome',
  shuffled: 'Shuffled wiring',
  zero: 'Zero connections',
  random: 'Random actions',
  expert: 'Scripted expert',
  manual: 'Human control',
  cotton: 'Cotton',
  silk: 'Silk',
  wool: 'Wool',
  shirt: 'T-shirt',
  trousers: 'Trousers',
  patch: 'Cloth patch',
};
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(
    '/api/' + path,
    body === undefined
      ? {}
      : {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        },
  );
  if (!r.ok) {
    const e = await r.text();
    throw Error(e.length < 300 ? e : `Request failed (${r.status})`);
  }
  return r.json() as Promise<T>;
}
export function Choice({
  label,
  value,
  values,
  onChange,
  disabled = false,
}: {
  label: string;
  value: string;
  values: string[];
  onChange: (v: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <Select
        value={value}
        onValueChange={(v) => v && onChange(v)}
        disabled={disabled}
      >
        <SelectTrigger className="choice" aria-label={label}>
          <SelectValue>{names[value] || value}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          {values.map((v) => (
            <SelectItem key={v} value={v}>
              {names[v] || v}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}
export function Range({
  label,
  value,
  min,
  max,
  step = 1,
  unit,
  onChange,
  disabled = false,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  unit: string;
  onChange: (v: number) => void;
  disabled?: boolean;
}) {
  return (
    <div className="range">
      <div>
        <span>{label}</span>
        <strong>
          {value}
          <small> {unit}</small>
        </strong>
      </div>
      <Slider
        aria-label={label}
        value={[value]}
        min={min}
        max={max}
        step={step}
        onValueChange={(v) => onChange(Array.isArray(v) ? v[0] : v)}
        disabled={disabled}
      />
    </div>
  );
}
export function ClothView({
  frame,
  heatmap,
}: {
  frame: Frame | null;
  heatmap: boolean;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !frame) return;
    const c = canvas.getContext('2d')!,
      s = frame.cloth;
    canvas.width = 900;
    canvas.height = 690;
    c.fillStyle = '#191f1c';
    c.fillRect(0, 0, 900, 690);
    const ox = 130,
      oy = 28,
      size = 640,
      cell = size / (s.n - 1);
    c.strokeStyle = '#2a322d';
    for (let x = 0; x < 900; x += 30) {
      c.beginPath();
      c.moveTo(x, 0);
      c.lineTo(x, 690);
      c.stroke();
    }
    for (let y = 0; y < 690; y += 30) {
      c.beginPath();
      c.moveTo(0, y);
      c.lineTo(900, y);
      c.stroke();
    }
    c.fillStyle = '#111713';
    c.beginPath();
    c.roundRect(ox + 30, oy + 18, size - 60, size - 35, 48);
    c.fill();
    for (let i = 0; i < s.n; i++)
      for (let j = 0; j < s.n; j++) {
        const k = i * s.n + j;
        if (!s.mask[k]) continue;
        const z = s.wrinkle[k],
          burn = s.scorch[k],
          t = (s.heat[k] - 22) / 190;
        let r = 166 - z * 90,
          g = 191 - z * 100,
          b = 169 - z * 95;
        if (heatmap) {
          r = 50 + 205 * t;
          g = 110 + 65 * t;
          b = 120 - 85 * t;
        } else {
          r = r * (1 - burn) + 55 * burn;
          g = g * (1 - burn) + 30 * burn;
          b = b * (1 - burn) + 15 * burn;
        }
        c.fillStyle = `rgb(${r},${g},${b})`;
        c.fillRect(
          ox + j * cell - cell / 2,
          oy + i * cell - cell / 2,
          cell + 0.5,
          cell + 0.5,
        );
        if (!heatmap && z > 0.17) {
          c.strokeStyle = `rgba(222,235,215,${Math.min(0.42, z * 0.5)})`;
          c.beginPath();
          c.moveTo(ox + j * cell - cell / 2, oy + i * cell - cell / 2);
          c.lineTo(ox + (j + 1) * cell - cell / 2, oy + i * cell - cell / 2);
          c.stroke();
        }
      }
    // This ellipse is the simulated iron's exact contact footprint.
    const ix = ox + s.iron[0] * size,
      iy = oy + s.iron[1] * size;
    c.save();
    c.translate(ix, iy);
    c.shadowColor = '#0009';
    c.shadowBlur = 24;
    c.shadowOffsetY = 10;
    c.fillStyle = s.pressure > 0.1 ? '#dce5d4' : '#919c91';
    c.beginPath();
    c.ellipse(0, 0, 0.075 * size, 0.105 * size, 0, 0, Math.PI * 2);
    c.fill();
    c.shadowBlur = 0;
    c.shadowOffsetY = 0;
    c.strokeStyle = '#0b120d';
    c.lineWidth = 3;
    c.stroke();
    c.fillStyle = '#35433b';
    c.beginPath();
    c.roundRect(-13, -30, 26, 55, 12);
    c.fill();
    c.fillStyle = s.pressure > 0.1 ? '#d3f087' : '#637568';
    c.beginPath();
    c.arc(0, 39, 4, 0, Math.PI * 2);
    c.fill();
    c.restore();
    c.strokeStyle = '#d3f087';
    c.lineWidth = 1.5;
    const tx = ox + s.target[0] * size,
      ty = oy + s.target[1] * size;
    c.beginPath();
    c.arc(tx, ty, 8, 0, Math.PI * 2);
    c.moveTo(tx - 14, ty);
    c.lineTo(tx + 14, ty);
    c.moveTo(tx, ty - 14);
    c.lineTo(tx, ty + 14);
    c.stroke();
    c.fillStyle = '#a0ada4';
    c.font = '13px monospace';
    c.fillText('01 / NEAR-FLAT GARMENT MODEL', 24, 32);
    c.fillText('1.0 × 1.0  VIRTUAL BOARD', 24, 668);
  }, [frame, heatmap]);
  return (
    <canvas
      ref={ref}
      className="cloth-canvas"
      aria-label="Live cloth: dark folds are wrinkles, ellipse is iron contact, cross is selected wrinkle patch."
    />
  );
}
export function Raster({
  frame,
  circuit,
}: {
  frame: Frame | null;
  circuit: Circuit | null;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !circuit) return;
    const c = canvas.getContext('2d')!;
    canvas.width = 1000;
    canvas.height = 200;
    c.fillStyle = '#111713';
    c.fillRect(0, 0, 1000, 200);
    c.strokeStyle = '#28322b';
    for (let i = 0; i <= 10; i++) {
      c.beginPath();
      c.moveTo(i * 100, 0);
      c.lineTo(i * 100, 200);
      c.stroke();
    }
    if (!frame) return;
    const start = Math.max(1000, frame.neural.time_ms) - 1000;
    for (const [t, i] of frame.neural.spikes) {
      if (t < start) continue;
      c.fillStyle = circuit.inputs.includes(i)
        ? '#d3f087'
        : circuit.motors.includes(i)
          ? '#a5d9e8'
          : '#5d8b74';
      c.fillRect(t - start, (i / circuit.nodes.length) * 190 + 5, 2, 2);
    }
  }, [frame, circuit]);
  return (
    <canvas
      ref={ref}
      className="raster"
      aria-label="Measured spikes over the last second: yellow descending, green intermediate, blue motor."
    />
  );
}
export function Network({
  circuit,
  frame,
}: {
  circuit: Circuit | null;
  frame: Frame | null;
}) {
  if (!circuit) return null;
  const cols = [
    circuit.inputs,
    Array.from({ length: 160 }, (_, i) => i + 8),
    circuit.motors,
  ];
  const pos = (i: number) => {
    const col = i < 8 ? 0 : i < 168 ? 1 : 2;
    return [
      35 + col * 125,
      12 + (cols[col].indexOf(i) / (cols[col].length - 1)) * 150,
    ];
  };
  // SVG is the semantic graphic itself; wrapping it in img would remove tooltips.
  /* eslint-disable jsx-a11y/prefer-tag-over-role */
  return (
    <svg
      viewBox="0 0 320 180"
      className="network"
      role="img"
      aria-label="Schematic BANC circuit, strongest 100 connections"
    >
      <g>
        {[...circuit.edges]
          .sort((a, b) => b[2] - a[2])
          .slice(0, 100)
          .map(([a, b, count], i) => {
            const [x, y] = pos(a),
              [xx, yy] = pos(b);
            return (
              <path
                key={i}
                d={`M${x},${y} Q160,${(y + yy) / 2} ${xx},${yy}`}
                fill="none"
                stroke="#55745e"
                strokeWidth={Math.min(2, count / 150)}
                opacity=".35"
              />
            );
          })}
      </g>
      {circuit.nodes.map((n, i) => {
        const [x, y] = pos(i),
          r = frame?.neural.rates[i] || 0;
        return (
          <circle
            key={n.id}
            cx={x}
            cy={y}
            r={i < 8 ? 3 : r > 5 ? 2 : 1}
            fill={i < 8 ? '#d3f087' : i >= 168 ? '#a5d9e8' : '#6a9c7f'}
            opacity={r > 5 ? 1 : 0.4}
          >
            <title>
              {n.cell_type || n.super_class} · {n.side} · {n.id} ·{' '}
              {r.toFixed(1)} Hz
            </title>
          </circle>
        );
      })}
    </svg>
  );
}
