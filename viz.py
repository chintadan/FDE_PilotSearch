"""
Author: Nikhil Chintada

viz.py — Matplotlib visualizer for the drone search sim.

Added to enhance visualization of sim, AI-generated w/ author edits

Usage:
    viz = Visualizer(world, drones, link_range, save_gif=True)
    ... in the loop, after act():   viz.update(world, drones, t)
    ... after the loop:             viz.finish()   # shows/saves
"""

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
import numpy as np
from itertools import combinations


class Visualizer:
    def __init__(self, w_width, w_height, drones, link_range, save_gif, fps, gif_path="run.gif"):
        self.link_range = link_range
        self.save_gif = save_gif
        self.gif_path = gif_path
        self.fps = fps
        self.frames = []          # captured for GIF export

        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(7, 7))

        # stable color per drone
        cmap = plt.get_cmap("tab10")
        self.colors = {d.id: cmap(i % 10) for i, d in enumerate(drones)}

    # ------------------------------------------------------------------
    def update(self, w_width, w_height, pilot_loc, drones, t):
        ax = self.ax
        ax.clear()
        ax.set_xlim(-0.5, w_width - 0.5)
        ax.set_ylim(-0.5, w_height - 0.5)
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])

        # --- coverage: union of searched cells (light shading) ---
        cover = np.zeros((w_height, w_width))
        for d in drones:
            for (x, y) in d.model.searched:            # <-- adjust attr if needed
                if 0 <= x < w_width and 0 <= y < w_height:
                    cover[y][x] = 1
        ax.imshow(cover, cmap="Greys", alpha=0.15, origin="lower",
                  extent=[-0.5, w_width - 0.5, -0.5, w_height - 0.5],
                  vmin=0, vmax=1)

        # --- sync links: dashed line between in-range peers ---
        found_any = False
        for a, b in combinations(drones, 2):
            if not (getattr(a, "alive", True) and getattr(b, "alive", True)):
                continue
            dx = abs(a.pos[0] - b.pos[0]); dy = abs(a.pos[1] - b.pos[1])
            if max(dx, dy) <= self.link_range:
                ax.plot([a.pos[0], b.pos[0]], [a.pos[1], b.pos[1]],
                        color="tab:green", lw=1.5, ls="--", alpha=0.6, zorder=1)

        # --- per-drone trail + marker ---
        for d in drones:
            c = self.colors[d.id]
            if getattr(d, "trail", None):
                tx = [p[0] for p in d.trail]
                ty = [p[1] for p in d.trail]
                ax.plot(tx, ty, color=c, lw=1, alpha=0.35, zorder=2)

            knows = d.model.pilot_found is not None    # <-- adjust attr if needed
            found_any = found_any or knows
            ax.scatter([d.pos[0]], [d.pos[1]], s=180,
                       color=c, edgecolors="black",
                       marker="*" if knows else "o", zorder=4)
            ax.annotate(str(d.id), (d.pos[0], d.pos[1]),
                        color="white", ha="center", va="center",
                        fontsize=8, zorder=5)

        # --- pilot: red X (hollow until found by someone) ---
        px, py = pilot_loc
        ax.scatter([px], [py], s=260, marker="X",
                   color="red" if found_any else "none",
                   edgecolors="red", linewidths=2, zorder=3)

        # --- status title ---
        n_know = sum(1 for d in drones if d.model.pilot_found is not None)
        ax.set_title(f"t={t} Drones Informed: {n_know}/{len(drones)}"
                     + ("   PILOT FOUND" if found_any else ""))

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

        if self.save_gif:
            buf = self.fig.canvas.buffer_rgba()          # works on Qt5Agg + Agg
            img = np.frombuffer(buf, dtype=np.uint8)
            w, h = self.fig.canvas.get_width_height()
            img = img.reshape((h, w, 4))                  # RGBA
            self.frames.append(img.copy())

    # ------------------------------------------------------------------
    def finish(self):
        plt.ioff()
        if self.save_gif and self.frames:
            try:
                import imageio
                imageio.mimsave(self.gif_path, self.frames[::2], fps=self.fps//2)
                print(f"saved {self.gif_path} ({len(self.frames)} frames)")
            except ImportError:
                print("install imageio to export GIF:  pip install imageio")
        plt.show()
