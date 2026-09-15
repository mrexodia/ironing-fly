'use client';
import { useEffect, useRef, useState } from 'react';
import {
  RotateCcw,
  Minus,
  Plus,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ClothView, type Frame } from './lab';
import type { createIroningScene } from './ironing-scene';

export function SceneView({
  frame,
  heatmap,
}: {
  frame: Frame | null;
  heatmap: boolean;
}) {
  const host = useRef<HTMLDivElement>(null);
  const scene = useRef<ReturnType<typeof createIroningScene> | null>(null);
  const latest = useRef({ frame, heatmap });
  const [failed, setFailed] = useState(false);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    latest.current = { frame, heatmap };
    if (frame) scene.current?.update(frame, heatmap);
  }, [frame, heatmap]);
  useEffect(() => {
    let cancelled = false;
    const element = host.current;
    if (!element) return;
    void import('./ironing-scene')
      .then(({ createIroningScene }) => {
        if (cancelled) return;
        try {
          scene.current = createIroningScene(element, () => setFailed(true));
          if (latest.current.frame)
            scene.current.update(latest.current.frame, latest.current.heatmap);
          setReady(true);
        } catch {
          setFailed(true);
        }
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
      scene.current?.dispose();
      scene.current = null;
    };
  }, []);
  useEffect(() => {
    if (failed) {
      scene.current?.dispose();
      scene.current = null;
    }
  }, [failed]);
  return (
    <div className="scene-view">
      <div ref={host} className="scene-host" hidden={failed} />
      {failed ? (
        <>
          <ClothView frame={frame} heatmap={heatmap} />
          <div className="scene-fallback" role="alert">
            3D is unavailable in this browser. The live 2D map is still running.
          </div>
        </>
      ) : (
        <>
          {!ready && (
            <div className="scene-loading">
              Setting up the little laundry room…
            </div>
          )}
          <div className="scene-label">
            <span className="scene-kicker">THE LITTLE LAUNDRY</span>
            <span>3D view · 2D simulation</span>
          </div>
          <div className="camera-controls" aria-label="3D camera controls">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Rotate camera left"
              onClick={() => scene.current?.orbit(-0.3)}
            >
              <ChevronLeft size={16} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Rotate camera right"
              onClick={() => scene.current?.orbit(0.3)}
            >
              <ChevronRight size={16} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Zoom out"
              onClick={() => scene.current?.zoom(1.15)}
            >
              <Minus size={16} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Zoom in"
              onClick={() => scene.current?.zoom(0.85)}
            >
              <Plus size={16} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Reset camera"
              onClick={() => scene.current?.home()}
            >
              <RotateCcw size={14} />
            </Button>
          </div>
          <span className="camera-hint">Drag to orbit · scroll to zoom</span>
        </>
      )}
    </div>
  );
}
