"""Near-flat height-field ironing toy, NOT a deformable cloth/body solver.

Fields are dimensionless wrinkle amplitude, degrees Celsius and scorch [0,1].
The iron moves on a unit board; each control tick advances 20 ms.
"""
import numpy as np

FABRICS = {
    'cotton': {'scorch_c': 190, 'soften_c': 70, 'flatten': 1.8, 'heat': 2.4, 'steam_need': 0.0},
    'silk': {'scorch_c': 120, 'soften_c': 45, 'flatten': 2.6, 'heat': 4.0, 'steam_need': 0.0},
    'wool': {'scorch_c': 160, 'soften_c': 60, 'flatten': 1.4, 'heat': 2.0, 'steam_need': 0.8},
}

class Cloth:
    def __init__(self, seed=42, fabric='cotton', garment='shirt', temperature=170, select_target=True):
        self.seed, self.fabric, self.garment = seed, fabric, garment
        self.iron_temperature = temperature
        self.n = 40
        self.x, self.y = np.meshgrid(np.linspace(0, 1, self.n), np.linspace(0, 1, self.n))
        x, y = self.x, self.y
        if garment == 'shirt':
            self.mask = (((x > .27) & (x < .73) & (y > .2) & (y < .9)) |
                         ((x > .09) & (x < .91) & (y > .22) & (y < .43)))
            self.mask &= ~((abs(x - .5) < .10) & (y < .26))
        elif garment == 'trousers':
            self.mask = ((x > .27) & (x < .73) & (y > .13) & (y < .9)) & ~((abs(x - .5) < .045) & (y > .42))
        else:
            self.mask = (x > .18) & (x < .82) & (y > .18) & (y < .82)
        rng = np.random.default_rng(seed)
        z = np.zeros_like(x)
        for _ in range(9):
            angle, phase = rng.uniform(0, 2 * np.pi, 2)
            z += (np.sin((x * np.cos(angle) + y * np.sin(angle)) * rng.uniform(12, 35) + phase) ** 16) * rng.uniform(.08, .24)
        self.wrinkle = np.clip(z, 0, 1) * self.mask
        self.initial = float(self.wrinkle.sum())
        self.heat = np.full_like(x, 22.)
        self.scorch = np.zeros_like(x)
        self.position = np.array([.5, .5])
        self.pressed = np.zeros_like(self.mask)
        self.travel = 0.
        self.pressure, self.steam, self.time, self.reward = 0., 0., 0., 0.
        self.target = np.array([.5, .5])
        if select_target:
            self.choose_target()

    def choose_target(self):
        # Explicit engineered observation: locate an unflattened patch, with a
        # travel penalty. This is not a simulated fly visual pathway.
        dist = np.hypot(self.x - self.position[0], self.y - self.position[1])
        priority = self.wrinkle / (0.2 + dist) * (1 - self.scorch)
        i, j = np.unravel_index(np.argmax(priority), priority.shape)
        self.target = np.array([self.x[i, j], self.y[i, j]])

    def features(self):
        self.choose_target()
        delta = np.clip((self.target - self.position) * 3, -1, 1)
        i, j = np.clip(np.rint(self.position[::-1] * (self.n - 1)), 0, self.n - 1).astype(int)
        hot = float(np.clip((self.heat[i, j] - FABRICS[self.fabric]['scorch_c'] + 20) / 30, 0, 1))
        return np.array([max(delta[0], 0), max(-delta[0], 0), max(delta[1], 0), max(-delta[1], 0),
                         1. - hot, hot, float(self.fabric == 'wool'), float(self.mask[i, j])])

    @staticmethod
    def expert(features):
        a = features
        return np.array([a[0] - a[1], a[2] - a[3], a[4] * a[7], a[6]])

    def step(self, action, dt=.02):
        action = np.asarray(action)
        if action.shape != (4,) or not np.isfinite(action).all():
            raise ValueError('Expected four finite actions')
        vx, vy = np.clip(action[:2], -1, 1)
        self.pressure, self.steam = np.clip(action[2:], 0, 1)
        previous_position = self.position.copy()
        self.position = np.clip(self.position + np.array([vx, vy]) * .30 * dt, .04, .96)
        self.travel += float(np.linalg.norm(self.position - previous_position))
        contact = (((self.x - self.position[0]) / .075) ** 2 + ((self.y - self.position[1]) / .105) ** 2 < 1) & self.mask
        self.pressed |= contact & (self.pressure > .1)
        material = FABRICS[self.fabric]
        # No wrap-around diffusion at garment boundaries.
        flux = np.zeros_like(self.heat)
        for axis in (0, 1):
            neighbor = np.roll(self.heat, 1, axis)
            valid = self.mask & np.roll(self.mask, 1, axis)
            if axis == 0: valid[0, :] = False
            else: valid[:, 0] = False
            flow = (neighbor - self.heat) * valid
            flux += flow - np.roll(flow, -1, axis)
        self.heat += dt * (material['heat'] * contact * self.pressure * (self.iron_temperature - self.heat) + .2 * flux - .35 * (self.heat - 22))
        self.heat[~self.mask] = 22
        old_wrinkle, old_scorch = self.wrinkle.sum(), self.scorch.sum()
        softness = np.clip((self.heat - material['soften_c']) / 60, 0, 1)
        steam_factor = 1 - material['steam_need'] + material['steam_need'] * self.steam
        self.wrinkle *= np.exp(-dt * contact * self.pressure * material['flatten'] * softness * steam_factor)
        self.scorch = np.clip(self.scorch + dt * np.maximum(self.heat - material['scorch_c'], 0) * .004 * self.mask, 0, 1)
        off = float(not self.mask[tuple(np.clip(np.rint(self.position[::-1] * (self.n - 1)), 0, self.n - 1).astype(int))])
        self.reward = float((old_wrinkle - self.wrinkle.sum()) / self.initial * 100 - (self.scorch.sum() - old_scorch) / self.mask.sum() * 200 - dt * (.01 + .1 * off))
        self.time += dt

    def metrics(self):
        return {'coverage_percent': float(100 * self.pressed.sum() / self.mask.sum()),
                'travel': self.travel,
                'smooth_percent': float(100 * (1 - self.wrinkle.sum() / self.initial)),
                'scorch_percent': float(100 * self.scorch.sum() / self.mask.sum()),
                'max_temperature_c': float(self.heat.max()), 'reward': self.reward}

    def snapshot(self):
        return {'time': round(self.time, 3), 'fabric': self.fabric, 'garment': self.garment,
                'n': self.n, 'mask': self.mask.astype(int).ravel().tolist(),
                'wrinkle': self.wrinkle.round(4).ravel().tolist(), 'heat': self.heat.round(1).ravel().tolist(),
                'scorch': self.scorch.round(4).ravel().tolist(), 'iron': self.position.tolist(),
                'target': self.target.tolist(), 'pressure': float(self.pressure), 'steam': float(self.steam), **self.metrics()}
