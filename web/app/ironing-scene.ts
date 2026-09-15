import * as T from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import type { Frame } from './lab';

// A presentation layer only. Coordinates below map the unchanged unit board to
// a tabletop. Fly poses, wings and steam are illustrations, not a body model.
const BOARD_Y = 1.65;
const CLOTH_Y = BOARD_Y + 0.125;
const WIDTH = 5.25;
const DEPTH = 3.5;
type Point = [number, number, number];

export function createIroningScene(
  host: HTMLDivElement,
  onFailure: () => void,
) {
  const scene = new T.Scene();
  scene.background = new T.Color('#dce8de');
  scene.fog = new T.Fog('#dce8de', 18, 35);
  const renderer = new T.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFShadowMap;
  renderer.outputColorSpace = T.SRGBColorSpace;
  renderer.toneMapping = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  renderer.domElement.setAttribute(
    'aria-label',
    '3D ironing scene. A cartoon fly pushes the iron over the live garment. Drag to orbit, scroll to zoom, or use the camera buttons.',
  );
  renderer.domElement.tabIndex = 0;
  host.appendChild(renderer.domElement);

  const camera = new T.PerspectiveCamera(36, 1, 0.1, 60);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.09;
  controls.enablePan = false;
  controls.minDistance = 5.5;
  controls.maxDistance = 16;
  controls.minPolarAngle = 0.12;
  controls.maxPolarAngle = Math.PI / 2 - 0.06;
  controls.target.set(0, 1.35, 0);
  function home() {
    camera.position.set(5.7, 6.8, -7.8);
    controls.target.set(0, 1.35, 0);
    controls.update();
  }
  home();
  scene.add(new T.HemisphereLight('#f6fffa', '#8c9d89', 2.6));
  const sun = new T.DirectionalLight('#fff2d7', 4.2);
  sun.position.set(-3, 8, 5);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.left = sun.shadow.camera.bottom = -5;
  sun.shadow.camera.right = sun.shadow.camera.top = 5;
  sun.shadow.normalBias = 0.025;
  sun.shadow.bias = -0.00015;
  scene.add(sun);
  const rim = new T.DirectionalLight('#d5faff', 2);
  rim.position.set(4, 5, -4);
  scene.add(rim);

  function material(color: string, roughness = 0.65, metalness = 0) {
    return new T.MeshStandardMaterial({ color, roughness, metalness });
  }
  const dark = material('#35443c');
  const green = material('#468b79');
  const cream = material('#f9edcf');
  const metal = material('#aabeb7', 0.26, 0.65);
  const copper = material('#bd6d53', 0.35, 0.2);
  function mesh(
    geometry: T.BufferGeometry,
    mat: T.Material,
    parent: T.Object3D,
    at: Point = [0, 0, 0],
  ) {
    const object = new T.Mesh(geometry, mat);
    object.position.set(...at);
    object.castShadow = true;
    object.receiveShadow = true;
    parent.add(object);
    return object;
  }
  function ball(parent: T.Object3D, mat: T.Material, at: Point, scale: Point) {
    const object = mesh(new T.SphereGeometry(1, 24, 16), mat, parent, at);
    object.scale.set(...scale);
    return object;
  }
  function bar(
    parent: T.Object3D,
    mat: T.Material,
    from: Point,
    to: Point,
    radius = 0.055,
  ) {
    const a = new T.Vector3(...from),
      b = new T.Vector3(...to);
    const object = mesh(
      new T.CylinderGeometry(radius, radius, a.distanceTo(b), 12),
      mat,
      parent,
    );
    object.position.copy(a).lerp(b, 0.5);
    object.quaternion.setFromUnitVectors(
      new T.Vector3(0, 1, 0),
      b.sub(a).normalize(),
    );
    return object;
  }
  function tube(
    parent: T.Object3D,
    mat: T.Material,
    points: Point[],
    radius = 0.025,
  ) {
    return mesh(
      new T.TubeGeometry(
        new T.CatmullRomCurve3(points.map((p) => new T.Vector3(...p))),
        24,
        radius,
        8,
        false,
      ),
      mat,
      parent,
    );
  }

  // Rounded padded board, a piped edge, and crossed folding legs.
  mesh(new RoundedBoxGeometry(6.25, 0.18, 4.25, 5, 0.085), green, scene, [
    0,
    BOARD_Y,
    0,
  ]);
  mesh(new RoundedBoxGeometry(6.3, 0.055, 4.3, 5, 0.027), cream, scene, [
    0,
    BOARD_Y - 0.055,
    0,
  ]);
  const padding = material('#8fbead', 0.96);
  mesh(new RoundedBoxGeometry(6.12, 0.08, 4.12, 5, 0.035), padding, scene, [
    0,
    BOARD_Y + 0.07,
    0,
  ]);
  for (const z of [-1.12, 1.12]) {
    bar(scene, cream, [-1.8, 0.14, z], [1.55, BOARD_Y - 0.13, z], 0.095);
    bar(scene, cream, [1.8, 0.14, z], [-1.55, BOARD_Y - 0.13, z], 0.095);
    ball(scene, copper, [0, 0.83, z + Math.sign(z) * 0.09], [0.13, 0.13, 0.08]);
  }
  for (const x of [-1.8, 1.8]) {
    bar(scene, cream, [x, 0.14, -1.4], [x, 0.14, 1.4], 0.095);
    for (const z of [-1.42, 1.42])
      ball(scene, green, [x, 0.14, z], [0.13, 0.13, 0.19]);
  }
  const floor = mesh(
    new T.PlaneGeometry(200, 200),
    material('#dce8de', 1),
    scene,
    [0, -0.07, 0],
  );
  floor.rotation.x = -Math.PI / 2;
  floor.castShadow = false;
  const rug = mesh(
    new T.CylinderGeometry(4.5, 4.55, 0.065, 96),
    material('#c0d3bf', 1),
    scene,
    [0, -0.018, 0],
  );
  rug.scale.z = 0.78;

  // Cloth vertices come directly from the backend's mask and wrinkle field.
  const clothGeometry = new T.BufferGeometry();
  const cloth = mesh(
    clothGeometry,
    new T.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.94,
      side: T.DoubleSide,
    }),
    scene,
  );
  cloth.castShadow = false;
  cloth.frustumCulled = false;
  let topologyKey = '';
  const color = new T.Color(),
    hot = new T.Color('#ee6542'),
    cold = new T.Color('#62b7c4'),
    burn = new T.Color('#563a28');
  function updateCloth(s: Frame['cloth'], heatmap: boolean) {
    const topology = `${s.n}:${s.garment}:${s.mask.join('')}`;
    if (topology !== topologyKey) {
      topologyKey = topology;
      clothGeometry.setAttribute(
        'position',
        new T.BufferAttribute(new Float32Array(s.n * s.n * 3), 3).setUsage(
          T.DynamicDrawUsage,
        ),
      );
      clothGeometry.setAttribute(
        'color',
        new T.BufferAttribute(new Float32Array(s.n * s.n * 3), 3).setUsage(
          T.DynamicDrawUsage,
        ),
      );
      const triangles: number[] = [];
      for (let row = 0; row < s.n - 1; row++)
        for (let col = 0; col < s.n - 1; col++) {
          const a = row * s.n + col,
            b = a + 1,
            c = a + s.n,
            d = c + 1;
          if (s.mask[a] && s.mask[b] && s.mask[c]) triangles.push(a, c, b);
          if (s.mask[b] && s.mask[c] && s.mask[d]) triangles.push(b, c, d);
        }
      clothGeometry.setIndex(triangles);
    }
    const positions = clothGeometry.getAttribute('position'),
      colors = clothGeometry.getAttribute('color');
    for (let i = 0; i < s.n * s.n; i++) {
      const x = i % s.n,
        z = Math.floor(i / s.n);
      positions.setXYZ(
        i,
        (x / (s.n - 1) - 0.5) * WIDTH,
        CLOTH_Y + s.wrinkle[i] * 0.19,
        (z / (s.n - 1) - 0.5) * DEPTH,
      );
      if (heatmap)
        color
          .copy(cold)
          .lerp(hot, T.MathUtils.clamp((s.heat[i] - 22) / 190, 0, 1));
      else
        color
          .set(
            s.fabric === 'silk'
              ? '#e6b6bd'
              : s.fabric === 'wool'
                ? '#d2c29c'
                : '#fff3d7',
          )
          .multiplyScalar(1 - s.wrinkle[i] * 0.14)
          .lerp(burn, s.scorch[i]);
      colors.setXYZ(i, color.r, color.g, color.b);
    }
    positions.needsUpdate = colors.needsUpdate = true;
    clothGeometry.computeVertexNormals();
    clothGeometry.computeBoundingSphere();
  }

  const iron = new T.Group();
  scene.add(iron);
  // The sole matches the simulation's elliptical 0.075 × 0.105 footprint.
  ball(iron, metal, [0, 0.018, 0], [0.075 * WIDTH, 0.047, 0.105 * DEPTH]);
  ball(iron, cream, [0, 0.12, 0.025], [0.34, 0.15, 0.32]);
  tube(
    iron,
    green,
    [
      [0, 0.16, -0.16],
      [0, 0.34, -0.12],
      [0, 0.36, 0.16],
      [0, 0.16, 0.23],
    ],
    0.052,
  );
  const lampMaterial = new T.MeshStandardMaterial({
    color: '#ffb560',
    emissive: '#ff951c',
    emissiveIntensity: 0.3,
  });
  ball(iron, lampMaterial, [0.17, 0.24, 0.1], [0.037, 0.021, 0.037]);

  // Six-limbed toy fly: two hands on the handle and four feet trailing behind.
  const fly = new T.Group();
  scene.add(fly);
  const bodyMaterial = material('#527065', 0.52);
  ball(fly, dark, [0, 0.42, 0.15], [0.25, 0.3, 0.33]);
  ball(fly, bodyMaterial, [0, 0.55, -0.07], [0.27, 0.29, 0.24]);
  const head = new T.Group();
  head.position.set(0, 0.77, -0.2);
  fly.add(head);
  ball(head, bodyMaterial, [0, 0, 0], [0.32, 0.29, 0.27]);
  const eyeMaterial = material('#bb6354', 0.33);
  const white = material('#fffbea', 0.22);
  for (const side of [-1, 1]) {
    ball(head, eyeMaterial, [side * 0.19, 0.045, -0.18], [0.17, 0.2, 0.12]);
    ball(head, dark, [side * 0.16, 0.035, -0.285], [0.085, 0.12, 0.041]);
    ball(
      head,
      white,
      [side * 0.16 - 0.022, 0.09, -0.32],
      [0.029, 0.037, 0.012],
    );
    ball(
      head,
      white,
      [side * 0.16 + 0.025, 0.005, -0.324],
      [0.011, 0.014, 0.007],
    );
    tube(
      head,
      dark,
      [
        [side * 0.1, 0.23, 0],
        [side * 0.18, 0.37, -0.03],
        [side * 0.25, 0.41, -0.09],
      ],
      0.018,
    );
    ball(head, dark, [side * 0.25, 0.41, -0.09], [0.035, 0.035, 0.035]);
  }
  tube(
    head,
    dark,
    [
      [-0.07, -0.12, -0.247],
      [0, -0.15, -0.262],
      [0.07, -0.12, -0.247],
    ],
    0.014,
  );
  // Little cream bib/apron and a pocket.
  ball(fly, cream, [0, 0.4, -0.22], [0.205, 0.24, 0.042]);
  mesh(
    new RoundedBoxGeometry(0.13, 0.095, 0.024, 2, 0.01),
    green,
    fly,
    [0, 0.35, -0.26],
  );
  tube(
    fly,
    cream,
    [
      [-0.18, 0.63, -0.18],
      [0, 0.55, -0.3],
      [0.18, 0.63, -0.18],
    ],
    0.025,
  );
  const wings: T.Group[] = [];
  const wingMaterial = new T.MeshPhysicalMaterial({
    color: '#eefeff',
    transparent: true,
    opacity: 0.66,
    roughness: 0.18,
    metalness: 0.05,
    side: T.DoubleSide,
    depthWrite: false,
  });
  for (const side of [-1, 1]) {
    const wing = new T.Group();
    wing.position.set(side * 0.13, 0.65, 0.04);
    fly.add(wing);
    const w = ball(
      wing,
      wingMaterial,
      [side * 0.32, 0.12, 0.18],
      [0.39, 0.023, 0.23],
    );
    w.rotation.z = side * 0.23;
    w.rotation.y = side * -0.4;
    w.castShadow = false;
    tube(
      wing,
      material('#b0d7d0', 0.45),
      [
        [0, 0, 0],
        [side * 0.25, 0.1, 0.12],
        [side * 0.58, 0.18, 0.16],
      ],
      0.008,
    );
    wings.push(wing);
  }
  const walkingLegs: T.Group[] = [];
  for (const side of [-1, 1]) {
    tube(
      fly,
      dark,
      [
        [side * 0.21, 0.54, -0.1],
        [side * 0.35, 0.35, -0.32],
        [side * 0.16, 0.31, -0.63],
      ],
      0.026,
    );
    ball(fly, cream, [side * 0.16, 0.31, -0.63], [0.057, 0.046, 0.05]);
    for (const [z, rear] of [
      [0.02, false],
      [0.29, true],
    ] as const) {
      const leg = new T.Group();
      leg.position.set(side * 0.17, 0.35, z);
      fly.add(leg);
      tube(
        leg,
        dark,
        [
          [0, 0, 0],
          [side * 0.22, -0.16, rear ? 0.15 : -0.1],
          [side * 0.28, -0.34, rear ? 0.25 : -0.15],
        ],
        0.023,
      );
      ball(
        leg,
        dark,
        [side * 0.29, -0.34, rear ? 0.21 : -0.19],
        [0.075, 0.029, 0.105],
      );
      walkingLegs.push(leg);
    }
  }
  const marker = mesh(
    new T.TorusGeometry(0.095, 0.009, 6, 36),
    material('#db9456', 0.7),
    scene,
  );
  marker.rotation.x = Math.PI / 2;
  marker.castShadow = false;
  const steam: T.Mesh<T.SphereGeometry, T.MeshStandardMaterial>[] = [];
  for (let i = 0; i < 7; i++) {
    const puff = new T.Mesh(
      new T.SphereGeometry(0.065, 10, 8),
      new T.MeshStandardMaterial({
        color: '#ffffff',
        transparent: true,
        opacity: 0,
        depthWrite: false,
      }),
    );
    scene.add(puff);
    steam.push(puff);
  }

  let current: Frame | null = null;
  let snapped = false;
  let lastTime = -1;
  const ironTarget = new T.Vector3(),
    flyTarget = new T.Vector3();
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let disposed = false;
  function update(frame: Frame, heatmap: boolean) {
    current = frame;
    const s = frame.cloth;
    updateCloth(s, heatmap);
    const col = Math.round(s.iron[0] * (s.n - 1)),
      row = Math.round(s.iron[1] * (s.n - 1));
    const height = s.wrinkle[row * s.n + col] * 0.19;
    ironTarget.set(
      (s.iron[0] - 0.5) * WIDTH,
      CLOTH_Y + height + 0.04 + (1 - s.pressure) * 0.14,
      (s.iron[1] - 0.5) * DEPTH,
    );
    flyTarget.copy(ironTarget).add(new T.Vector3(0, -0.01, 0.7));
    if (!snapped || s.time < lastTime) {
      iron.position.copy(ironTarget);
      fly.position.copy(flyTarget);
      snapped = true;
    }
    lastTime = s.time;
    marker.position.set(
      (s.target[0] - 0.5) * WIDTH,
      CLOTH_Y + 0.16,
      (s.target[1] - 0.5) * DEPTH,
    );
    lampMaterial.emissiveIntensity = s.pressure * 0.8;
    for (let i = 0; i < walkingLegs.length; i++)
      walkingLegs[i].rotation.x = reduceMotion.matches
        ? 0
        : Math.sin(s.time * 17 + i * Math.PI) *
          0.13 *
          Math.min(1, Math.hypot(frame.action[0], frame.action[1]) * 3);
    wings.forEach((wing, i) => {
      wing.rotation.z =
        (i === 0 ? -1 : 1) *
        (0.1 + (reduceMotion.matches ? 0 : Math.sin(s.time * 23) * 0.035));
    });
    // An occasional blink is tied to simulation time, so pausing freezes it.
    const blink = s.time % 4.8 > 4.65;
    head.scale.y = blink ? 0.93 : 1;
  }
  let previous = 0;
  renderer.setAnimationLoop((now) => {
    if (disposed || document.hidden || now - previous < 1000 / 40) return;
    const elapsed = previous ? Math.min((now - previous) / 1000, 0.1) : 0.025;
    previous = now;
    const blend = reduceMotion.matches ? 1 : 1 - Math.exp(-elapsed * 20);
    iron.position.lerp(ironTarget, blend);
    fly.position.lerp(flyTarget, blend);
    if (current)
      steam.forEach((puff, i) => {
        const phase = (current!.cloth.time * 0.9 + i / 7) % 1;
        puff.visible =
          current!.cloth.steam > 0.05 && current!.cloth.pressure > 0.1;
        puff.position
          .copy(iron.position)
          .add(
            new T.Vector3(
              Math.sin(i * 2.7 + phase * 2) * 0.16,
              0.16 + phase * 0.7,
              -0.2,
            ),
          );
        puff.scale.setScalar(0.6 + phase * 1.8);
        puff.material.opacity = (1 - phase) * 0.24 * current!.cloth.steam;
      });
    controls.update();
    renderer.render(scene, camera);
  });
  function resize() {
    const width = Math.max(1, host.clientWidth),
      height = Math.max(1, host.clientHeight);
    camera.aspect = width / height;
    // Maintain the whole board in portrait view without affecting orbit distance.
    camera.fov = width < height ? 48 : 36;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }
  const observer = new ResizeObserver(resize);
  observer.observe(host);
  resize();
  function lost(event: Event) {
    event.preventDefault();
    onFailure();
  }
  renderer.domElement.addEventListener('webglcontextlost', lost);
  function orbit(amount: number) {
    const offset = camera.position.clone().sub(controls.target);
    offset.applyAxisAngle(new T.Vector3(0, 1, 0), amount);
    camera.position.copy(controls.target).add(offset);
    controls.update();
  }
  function zoom(factor: number) {
    const offset = camera.position.clone().sub(controls.target);
    offset.setLength(
      T.MathUtils.clamp(
        offset.length() * factor,
        controls.minDistance,
        controls.maxDistance,
      ),
    );
    camera.position.copy(controls.target).add(offset);
    controls.update();
  }
  function keydown(e: KeyboardEvent) {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      e.stopPropagation();
      orbit(e.key === 'ArrowLeft' ? -0.18 : 0.18);
    }
    if (e.key === '+' || e.key === '=') {
      e.preventDefault();
      zoom(0.85);
    }
    if (e.key === '-') {
      e.preventDefault();
      zoom(1.15);
    }
    if (e.key === 'Home') {
      e.preventDefault();
      home();
    }
  }
  renderer.domElement.addEventListener('keydown', keydown);
  return {
    update,
    home,
    orbit,
    zoom,
    dispose() {
      disposed = true;
      renderer.setAnimationLoop(null);
      observer.disconnect();
      controls.dispose();
      renderer.domElement.removeEventListener('webglcontextlost', lost);
      renderer.domElement.removeEventListener('keydown', keydown);
      const geometries = new Set<T.BufferGeometry>(),
        materials = new Set<T.Material>();
      scene.traverse((o) => {
        if (o instanceof T.Mesh) {
          geometries.add(o.geometry);
          (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) =>
            materials.add(m),
          );
        }
      });
      geometries.forEach((g) => g.dispose());
      materials.forEach((m) => m.dispose());
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}
