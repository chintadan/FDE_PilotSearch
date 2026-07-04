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
# Add confidence overlay
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

class Visualizer:
    def __init__(self, w_width, w_height, drones, link_range, live, save_gif, fps, gif_path="run.gif"):
        self.link_range = link_range
        self.live = live # Toggle live view
        self.save_gif = save_gif
        self.gif_path = gif_path
        self.fps = fps
        self.frames = []          # captured for GIF export

        if not self.live:
            plt.switch_backend("Agg")     # no window, capture-only
        else:
            plt.ion()

        self.fig, self.ax = plt.subplots(figsize=(7, 7))

        # stable color per drone
        cmap = plt.get_cmap("tab10")
        self.colors = {d.id: cmap(i % 10) for i, d in enumerate(drones)}

        # confidence overlay styling
        self.conf_cmap = plt.get_cmap("plasma")
        self.conf_norm = Normalize(vmin=0.0, vmax=1.0)
        # confirmation threshold (read from the model so they stay in sync)
        self.threshold = getattr(drones[0].model, "CONFIRM_THRESHOLD", 0.9)

        # one persistent colorbar
        sm = ScalarMappable(cmap=self.conf_cmap, norm=self.conf_norm)
        sm.set_array([])
        self.fig.colorbar(sm, ax=self.ax, fraction=0.046, pad=0.04,
                        label="aggregate detection confidence")

    # ------------------------------------------------------------------
    def update(self, w_width, w_height, pilot_loc, drones, t):
        ax = self.ax
        ax.clear()
        ax.set_xlim(-0.5, w_width - 0.5)
        ax.set_ylim(-0.5, w_height - 0.5)
        ax.set_aspect("equal")
        # integer grid ticks + labels (thinned so they don't crowd on big grids)
        step_x = max(1, w_width // 12)
        step_y = max(1, w_height // 12)
        ax.set_xticks(range(0, w_width, step_x))
        ax.set_yticks(range(0, w_height, step_y))
        ax.set_xlabel(f"X (0–{w_width - 1})")
        ax.set_ylabel(f"Y (0–{w_height - 1})")
        ax.tick_params(labelsize=8)

        w, h = w_width, w_height

        # --- coverage (light grey) ---
        cover = np.zeros((h, w))
        for d in drones:
            for (x, y) in d.model.searched:
                if 0 <= x < w and 0 <= y < h:
                    cover[y][x] = 1
        ax.imshow(cover, cmap="Greys", alpha=0.12, origin="lower",
                extent=[-0.5, w - 0.5, -0.5, h - 0.5], vmin=0, vmax=1, zorder=1)

        # --- CONFIDENCE OVERLAY (new) ---
        conf = np.zeros((h, w))
        for d in drones:
            for cell, obsmap in d.model.detections.items():
                prod = 1.0
                for c in obsmap.values():
                    prod *= (1.0 - c)
                agg = 1.0 - prod
                x, y = cell
                if 0 <= x < w and 0 <= y < h:
                    conf[y][x] = max(conf[y][x], agg)   # best evidence any drone has

        masked = np.ma.masked_where(conf <= 0.0, conf)  # only show cells with evidence
        ax.imshow(masked, cmap=self.conf_cmap, norm=self.conf_norm, origin="lower",
                extent=[-0.5, w - 0.5, -0.5, h - 0.5], alpha=0.75, zorder=2)

        # annotate cells with meaningful evidence; ring cells past threshold
        ys, xs = np.where(conf > 0.05)
        for y, x in zip(ys, xs):
            val = conf[y][x]
            ax.text(x, y, f"{val:.2f}", ha="center", va="center",
                    fontsize=6, color="black", zorder=6)
            if val >= self.threshold:
                ax.scatter([x], [y], s=420, facecolors="none",
                        edgecolors="lime", linewidths=2.2, zorder=6)
        # --- END confidence overlay ---

        # --- sync links (dashed green) ---
        found_any = False
        for a, b in combinations(drones, 2):
            if not (getattr(a, "alive", True) and getattr(b, "alive", True)):
                continue
            if max(abs(a.pos[0] - b.pos[0]), abs(a.pos[1] - b.pos[1])) <= self.link_range:
                ax.plot([a.pos[0], b.pos[0]], [a.pos[1], b.pos[1]],
                        color="tab:green", lw=1.5, ls="--", alpha=0.5, zorder=3)

        # --- drones (trail + marker; star if informed) ---
        for d in drones:
            c = self.colors[d.id]
            if getattr(d, "trail", None):
                ax.plot([p[0] for p in d.trail], [p[1] for p in d.trail],
                        color=c, lw=1, alpha=0.3, zorder=4)
            knows = d.model.pilot_found is not None
            found_any = found_any or knows
            ax.scatter([d.pos[0]], [d.pos[1]], s=180, color=c, edgecolors="black",
                    marker="*" if knows else "o", zorder=5)
            ax.annotate(str(d.id), (d.pos[0], d.pos[1]), color="white",
                        ha="center", va="center", fontsize=8, zorder=7)

        # --- pilot (hollow until found) ---
        px, py = pilot_loc
        ax.scatter([px], [py], s=260, marker="X",
                color="red" if found_any else "none",
                edgecolors="red", linewidths=2, zorder=5)
        
        # in update(), after plotting the pilot: --AI-gen for visualizing convergence
        from matplotlib.patches import Rectangle
        r = getattr(drones[0].sens, "radius", 1)
        ax.add_patch(Rectangle((px - r - 0.5, py - r - 0.5),
                            2*r + 1, 2*r + 1,
                            fill=False, edgecolor="red", ls=":",
                            lw=1.5, alpha=0.7, zorder=3))


        # --- title ---
        n_know = sum(1 for d in drones if d.model.pilot_found is not None)
        ax.set_title(f"t={t}   informed: {n_know}/{len(drones)}"
                    f"   (thr={self.threshold})"
                    + ("   PILOT FOUND" if found_any else ""))

        self.fig.canvas.draw()
        # Run if live
        if self.live:
            self.fig.canvas.flush_events() # live window updates
            plt.pause(0.001)

        if self.save_gif:
            buf = self.fig.canvas.buffer_rgba()
            img = np.frombuffer(buf, dtype=np.uint8)
            ww, hh = self.fig.canvas.get_width_height()
            self.frames.append(img.reshape((hh, ww, 4)).copy())

    # ------------------------------------------------------------------
    def finish(self):
        if self.save_gif and self.frames:
            try:
                import imageio.v2 as imageio
                imageio.mimsave(self.gif_path, self.frames[::2], fps=self.fps//2)
                print(f"saved {self.gif_path} ({len(self.frames)} frames)")
            except ImportError:
                print("install imageio to export GIF:  pip install imageio")
        if self.live: #Toggle for live
            plt.ioff()
            plt.show()
