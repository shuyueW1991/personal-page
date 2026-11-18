#!/usr/bin/env python3
"""Figure 3 for 12.md — the sagitta of the spherical surface vs the vertex plane.

Shows schematically (angles/heights exaggerated) why the sagitta is O(y^2/R):
  - panel (a): the paraxial ray for an axial object at s, striking at height y;
    the straight ray crosses the vertex plane (z=0, dashed) at height y, while
    the actual spherical surface lies a sagitta delta behind it.
  - panel (b): the right-triangle construction delta = R - sqrt(R^2-y^2)
    ~ y^2/(2R), using exact circle geometry.

Run:  python3 images/make_figure_sagitta.py
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc

plt.rcParams.update({
    "font.family": "STIXGeneral",
    "mathtext.fontset": "stix",
    "font.size": 12,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

INK, GRAY, DIM = "#1d1d1f", "#5f6368", "#8a8f98"
SURF, BLUE, RED, TEAL = "#1f3b57", "#1f6feb", "#c0392b", "#0f7b6c"

# ----------------------------------------------------------------- data (arbitrary units)
R = 5.0                        # schematic radius of curvature
y = 0.9                        # ray height at the surface (small, paraxial)
delta = R - np.sqrt(R * R - y * y)      # exact sagitta ~ 0.08 << y  (invisible at full scale)
s = -14.0                      # object distance (signed, z = s < 0)


def head(ax, p, d, color, ms=12, z=6):
    p = np.asarray(p, float); d = np.asarray(d, float) / np.linalg.norm(d)
    ax.annotate("", xy=p + 0.30 * d, xytext=p - 0.30 * d,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=0,
                                mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=z)


def ray(ax, p0, p1, color, lw=1.6, head_frac=0.5, z=4):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=color, lw=lw, zorder=z,
            solid_capstyle="round")
    head(ax, p0 + head_frac * (p1 - p0), p1 - p0, color, ms=12, z=z + 1)


def dim(ax, x0, x1, y, label, ylab, color=GRAY, fs=10.5, lw=0.9, tick=0.30, tc=INK):
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<|-|>", color=color, lw=lw,
                                shrinkA=0, shrinkB=0, mutation_scale=8), zorder=2)
    for x in (x0, x1):
        ax.plot([x, x], [y - tick, y + tick], color=color, lw=0.8, zorder=2)
    ax.text((x0 + x1) / 2, ylab, label, ha="center", va="center",
            fontsize=fs, color=tc)


fig = plt.figure(figsize=(11.0, 4.6))
gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 0.62, 0.70],
                      left=0.03, right=0.985, top=0.94, bottom=0.10, wspace=0.12)

# ------------------------------------------------------------------- (a) paraxial ray (full aperture)
axa = fig.add_subplot(gs[0])
axa.set_xlim(-14.5, 4.6)
axa.set_ylim(-1.9, 3.1)
axa.set_aspect("equal")
axa.axis("off")

# optical axis
axa.plot([-14.3, 4.5], [0, 0], color=DIM, lw=1.0, zorder=1)
axa.text(4.35, -0.34, "axis  $z$", fontsize=10, color=DIM, ha="right", va="center")

# spherical surface (vertex at origin, center of curvature at x=R)
tt = np.linspace(-0.34, 0.36, 300)
axa.plot(R * (1 - np.cos(tt)), R * np.sin(tt), color=SURF, lw=3.2, zorder=5,
         solid_capstyle="round")
axa.plot(R, 0, "o", ms=4.5, color=INK, zorder=6)
axa.text(R + 0.12, 0.16, r"$C$", fontsize=12, color=INK, ha="left", va="center")

# vertex plane (dashed, z=0) and its crossing point
axa.plot([0, 0], [-1.7, 2.9], color=GRAY, lw=1.0, ls=(0, (2, 2)), zorder=1)
axa.plot(0, 0, "o", ms=4, color=INK, zorder=6)
axa.text(-0.12, -0.24, r"$V$", fontsize=12, color=INK, ha="right", va="center")

# the paraxial ray, object at s to the left of the vertex plane
p0 = np.array([s, 0.0])
pP = np.array([delta, y])        # ray meets the (curved) sphere here
ray(axa, p0, pP, BLUE, lw=1.8, head_frac=0.5, z=4)

axa.text(s, -0.40, r"$O\,(z=s)$", fontsize=11, color=INK, ha="center", va="center")
# heavy dot at the vertex-plane crossing (the straight ray at height y)
axa.plot(0.0, y, "+", ms=12, mew=1.6, color=BLUE, zorder=6)
axa.text(3.30, 2.62, r"$n$", fontsize=13, color=GRAY, ha="left", va="center")
axa.text(-14.5, 2.78, "(a)", fontsize=12, color="#9aa0a6", ha="left", va="top", weight="bold")

# ------------------------------------------------- (b) zoomed vertex: vertex plane vs surface
axb = fig.add_subplot(gs[1])
axb.set_xlim(-0.32, 0.62)
axb.set_ylim(-0.30, 1.45)
axb.set_aspect("equal")
axb.axis("off")

tt = np.linspace(-0.34, 0.36, 300)
axb.plot(R * (1 - np.cos(tt)), R * np.sin(tt), color=SURF, lw=3.0, zorder=5,
         solid_capstyle="round")
axb.plot([0, 0], [-0.25, 1.40], color=GRAY, lw=1.0, ls=(0, (2, 2)), zorder=1)
axb.plot([-0.28, 0.58], [0, 0], color=DIM, lw=1.0, zorder=1)
axb.plot(0, 0, "o", ms=4, color=INK, zorder=6)
axb.text(-0.30, -0.22, r"$V$", fontsize=11, color=INK, ha="left", va="center")

# the sagitta gap at height y  (visible at this scale)
dim(axb, 0, delta, y - 0.30, r"$\delta$", y - 0.58, color=RED, fs=12)
axb.text(delta, y + 0.10, r"$P$", fontsize=11, color=INK, ha="center", va="bottom")
axb.text(0.02, y + 0.10, r"$y$", fontsize=10, color=RED, ha="left", va="bottom")
axb.text(0.46, 0.16, "vertex plane", fontsize=9.5, color=GRAY, ha="center", va="bottom")
axb.text(-0.30, 1.30, "(b)", fontsize=12, color="#9aa0a6", ha="left", va="top", weight="bold")
axb.text(-0.30, 1.02, r"zoom: surface is $\delta$ behind the plane", fontsize=9.5,
         color="#9aa0a6", ha="left", va="top")

# ------------------------------------------------- (c) sagitta right triangle (exact circle)
axc = fig.add_subplot(gs[2])
axc.set_xlim(-5.6, 1.0)
axc.set_ylim(-1.4, 2.0)
axc.set_aspect("equal")
axc.axis("off")

tt = np.linspace(-0.34, 0.36, 300)
axc.plot(R * (1 - np.cos(tt)), R * np.sin(tt), color=SURF, lw=3.0, zorder=5,
         solid_capstyle="round")
V = np.array([0.0, 0.0]); C = np.array([R, 0.0]); P = np.array([delta, y])
axc.plot([C[0], P[0]], [C[1], P[1]], color="#5f6368", lw=1.2, zorder=3)
axc.plot([V[0], P[0]], [V[1], P[1]], color="#c0392b", lw=1.2, ls=(0, (1.2, 1.6)), zorder=3)
axc.plot([V[0], C[0]], [V[1], C[1]], color=GRAY, lw=1.0, zorder=3)
axc.plot([0, 0], [-1.2, 1.6], color=GRAY, lw=0.9, ls=(0, (2, 2)), zorder=1)
axc.plot([-5.6, 0.9], [0, 0], color=DIM, lw=1.0, zorder=1)

axc.plot(*C, "o", ms=4.5, color=INK, zorder=6)
axc.text(C[0] + 0.12, 0.16, r"$C$", fontsize=11, color=INK, ha="left", va="center")
axc.text(V[0] - 0.12, -0.20, r"$V$", fontsize=11, color=INK, ha="right", va="center")
axc.text(P[0] - 0.10, P[1] + 0.14, r"$P$", fontsize=11, color=INK, ha="center", va="center")

axc.text((V[0] + C[0]) / 2, -0.08, r"$R-\delta$", fontsize=11, color=GRAY,
         ha="center", va="top")
axc.text(C[0] - 0.12, (C[1] + P[1]) / 2, r"$R$", fontsize=11, color="#5f6368",
         ha="right", va="center", rotation=90)
axc.text((V[0] + delta) / 2, (V[1] + y) / 2 + 0.08, r"$y$", fontsize=11, color=RED,
         ha="center", va="center")
axc.text(delta + 0.04, y - 0.42, r"$\delta = R-\sqrt{R^2-y^2}$", fontsize=10,
         color=RED, ha="left", va="center")
axc.text(-5.6, 1.85, "(c)", fontsize=12, color="#9aa0a6", ha="left", va="top", weight="bold")
axc.text(-5.6, 1.52,
         r"$(R-\delta)^2+y^2=R^2\ \Rightarrow\ \delta\approx y^2/2R$",
         fontsize=9.5, color="#9aa0a6", ha="left", va="top")

fig.savefig("images/sagitta.svg", bbox_inches="tight", pad_inches=0.06)
plt.close(fig)
print("wrote images/sagitta.svg")