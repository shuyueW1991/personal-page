#!/usr/bin/env python3
"""Figures for 12.md — optical power, focal length, and the paraxial refraction equation.

Figure 1: conjugates + focal points of a single spherical refracting surface (a),
          and the same numbers read as vergence bookkeeping (b).
Figure 2: local ray geometry at the hit point P (normal through C, angles u, u', alpha, i, i').

Numbers (arbitrary length units): n = 1.00, n' = 1.50, R = +4, s = -20.
    Phi = (n'-n)/R = 0.125,  s' = n'/(n/s + Phi) = +20,
    f' = n'/Phi = +12,       f  = -n/Phi = -8.
Run:  python3 images/make_figures_12.py
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
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

# ----------------------------------------------------------------------------- physics
n, n2 = 1.00, 1.50
R      = 4.0
s      = -20.0
Phi    = (n2 - n) / R
sp     = n2 / (n / s + Phi)          # +20
f      = -n / Phi                    # -8
fp     = n2 / Phi                    # +12
assert np.isclose(sp, 20.0) and np.isclose(f, -8.0) and np.isclose(fp, 12.0)


# ----------------------------------------------------------------------------- helpers
def head(ax, p, d, color, ms=13, z=6):
    p = np.asarray(p, float)
    d = np.asarray(d, float) / np.linalg.norm(d)
    ax.annotate("", xy=p + 0.30 * d, xytext=p - 0.30 * d,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=0,
                                mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=z)


def ray(ax, p0, p1, color, lw=2.0, head_frac=0.55, z=4):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=color, lw=lw, zorder=z,
            solid_capstyle="round")
    head(ax, p0 + head_frac * (p1 - p0), p1 - p0, color)


def dim(ax, x0, x1, y, label, ylab, color=DIM, fs=11.5, lw=0.9, tick=0.14, tc="#3c4043"):
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<|-|>", color=color, lw=lw,
                                shrinkA=0, shrinkB=0, mutation_scale=8), zorder=2)
    for x in (x0, x1):
        ax.plot([x, x], [y - tick, y + tick], color=color, lw=0.8, zorder=2)
    ax.text((x0 + x1) / 2, ylab, label, ha="center", va="center",
            fontsize=fs, color=tc)


# ----------------------------------------------------------------------------- figure 1
def figure1(path_svg):
    fig = plt.figure(figsize=(12.8, 6.3))
    gs = GridSpec(2, 1, height_ratios=[3.45, 0.95], hspace=0.20,
                  left=0.035, right=0.975, top=0.97, bottom=0.06)
    ax = fig.add_subplot(gs[0])
    ax.set_xlim(-23.8, 23.8)
    ax.set_ylim(-4.60, 6.15)
    ax.axis("off")

    ax.plot([-23.6, 23.6], [0, 0], color=DIM, lw=0.9, zorder=1)

    # spherical surface (schematic curvature)
    Rd = 5.0
    tmax = np.arcsin(3.15 / Rd)
    tt = np.linspace(-tmax, tmax, 400)
    ax.plot(Rd * (1 - np.cos(tt)), Rd * np.sin(tt), color=SURF, lw=3.4,
            solid_capstyle="round", zorder=5)

    def sx(yh):
        return Rd - np.sqrt(Rd ** 2 - yh ** 2)

    y1, y2 = 2.2, 2.9
    P1  = np.array([sx(y1), y1])
    P1b = np.array([sx(-y1), -y1])
    P2  = np.array([sx(y2), y2])

    for P in (P1, P1b):
        ray(ax, (s, 0), P, BLUE, lw=2.1, head_frac=0.62)
        ray(ax, P, (sp, 0), RED, lw=2.1, head_frac=0.45)
    ray(ax, (-23.6, y2), P2, TEAL, lw=1.9, head_frac=0.72)
    ray(ax, P2, (fp, 0), TEAL, lw=1.9, head_frac=0.55)

    ax.plot(s, 0, "o", ms=6.5, color=INK, zorder=8)
    ax.plot(sp, 0, "o", ms=6.5, color=INK, zorder=8)
    for x in (f, fp):
        ax.plot(x, 0, "o", ms=7.5, mfc="white", mec=INK, mew=1.5, zorder=8)

    ax.text(-21.9, 5.70, r"$n=1.00$  (air)", fontsize=13, color=INK, ha="left", va="center")
    ax.text(5.6, 5.70, r"$n'=1.50$  (glass)", fontsize=13, color=INK, ha="left", va="center")

    ax.annotate("", xy=(-19.8, 4.55), xytext=(-22.9, 4.55),
                arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.2,
                                mutation_scale=11, shrinkA=0, shrinkB=0))
    ax.text(-22.9, 4.82, "light", fontsize=11, color=GRAY, ha="left", va="center")
    ax.text(-18.3, 3.30, r"ray from infinity  ($s\to-\infty$)", fontsize=11,
            color=TEAL, ha="left", va="center")

    dim(ax, f, 0, 4.02, r"$f=-n/\Phi=-8$", 4.60)
    dim(ax, 0, fp, 4.02, r"$f'=+n'/\Phi=+12$", 4.60)
    dim(ax, s, 0, -3.72, r"$s=-20$", -4.18)
    dim(ax, 0, sp, -3.72, r"$s'=+20$", -4.18)

    ax.text(s, 0.62, r"$O$", fontsize=13, ha="center", va="center", color=INK)
    ax.text(sp, 0.62, r"$I$", fontsize=13, ha="center", va="center", color=INK)
    ax.text(f, -0.40, r"$F$", fontsize=13, ha="center", va="center", color=INK)
    ax.text(fp, -0.42, r"$F'$", fontsize=13, ha="center", va="center", color=INK)
    ax.text(-22.9, -0.55, "optical axis", fontsize=10, color=DIM, ha="left", va="center")
    ax.text(-23.6, 5.70, "(a)", fontsize=12.5, color="#9aa0a6", ha="left", va="center", weight="bold")

    # ---- vergence ledger
    axb = fig.add_subplot(gs[1])
    axb.set_xlim(-0.098, 0.112)
    axb.set_ylim(0.02, 1.10)
    axb.axis("off")

    v_in, v_out = n / s, n2 / sp
    yb = 0.50
    axb.plot([-0.088, 0.106], [yb, yb], color="#b8bcc2", lw=1.0, zorder=1)
    axb.plot([0, 0], [yb - 0.16, yb + 0.16], color="#9aa0a6", lw=1.0, zorder=1)
    axb.annotate("", xy=(v_out, yb), xytext=(v_in, yb),
                 arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=3.0,
                                 shrinkA=0, shrinkB=0, mutation_scale=16), zorder=3)
    axb.plot(v_in, yb, "o", ms=8, color=BLUE, zorder=4)
    axb.plot(v_out, yb, "o", ms=8, color=RED, zorder=4)

    axb.text(-0.097, 0.99, "(b)", fontsize=12.5, color="#9aa0a6",
             ha="left", va="center", weight="bold")
    axb.text(-0.079, 0.99, r"$n'/s' \;=\; n/s \;+\; \Phi$", fontsize=13.5, color=INK,
             ha="left", va="center")
    axb.text((v_in + v_out) / 2, 0.63, r"surface adds $\Phi=+0.125$", fontsize=11.5,
             color=TEAL, ha="center", va="bottom")
    axb.text(0.0, 0.34, r"$0$", fontsize=10.5, color=DIM, ha="center", va="center")
    axb.text(v_in, 0.29, r"$n/s=-0.050$", fontsize=11.5, color=BLUE, ha="center", va="center")
    axb.text(v_out, 0.29, r"$n'/s'=+0.075$", fontsize=11.5, color=RED, ha="center", va="center")
    axb.text(v_in, 0.13, "diverging", fontsize=10.5, color=GRAY, ha="center",
             va="center", style="italic")
    axb.text(v_out, 0.13, "converging", fontsize=10.5, color=GRAY, ha="center",
             va="center", style="italic")

    fig.savefig(path_svg, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


# ----------------------------------------------------------------------------- figure 2
def figure2(path_svg):
    R2, y2 = 4.0, 2.0
    xP = R2 - np.sqrt(R2 ** 2 - y2 ** 2)
    P  = np.array([xP, y2])
    C  = np.array([R2, 0.0])
    alpha = -np.degrees(np.arcsin(y2 / R2))     # -30 deg
    u  = 6.0
    i  = u - alpha                              # 36
    ip = i / 1.5                                # 24
    up = ip + alpha                             # -6

    fig, ax = plt.subplots(figsize=(10.4, 6.5))
    ax.set_xlim(-1.80, 4.72)
    ax.set_ylim(-0.60, 3.28)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.plot([-1.72, 4.70], [0, 0], color=DIM, lw=1.0, zorder=1)
    ax.text(-1.74, -0.29, "axis", fontsize=9.5, color=DIM, ha="left", va="center")

    # true circular arc, radius R2
    tt = np.radians(np.linspace(-7.5, 40.5, 300))
    ax.plot(R2 - R2 * np.cos(tt), R2 * np.sin(tt), color=SURF, lw=3.4, zorder=5,
            solid_capstyle="round")

    # normal: through P and C, extended past P; it is also the radius
    d = np.array([np.cos(np.radians(alpha)), np.sin(np.radians(alpha))])  # P -> C
    n_top = P - 1.62 * d
    ax.plot([n_top[0], C[0]], [n_top[1], C[1]], color=GRAY, lw=1.1, ls=(0, (5, 3)), zorder=2)

    ax.plot([xP, xP], [0, y2], color=DIM, lw=1.0, ls=(0, (2, 2)), zorder=1)
    ax.plot([xP - 0.09, xP, xP], [0.0, 0.0, 0.09], color=DIM, lw=0.9, zorder=1)
    ax.text(xP + 0.13, y2 / 2, r"$y$", fontsize=14, color=GRAY, ha="left", va="center")

    ax.plot([-1.72, 2.50], [y2, y2], color=DIM, lw=0.9, ls=(0, (4, 3)), zorder=1)

    def ray2(p0, p1, color, lw=2.4, head_at=0.55):
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=color, lw=lw, zorder=4,
                solid_capstyle="round")
        m = p0 + head_at * (p1 - p0)
        dd = (p1 - p0) / np.linalg.norm(p1 - p0)
        ax.annotate("", xy=m + 0.28 * dd, xytext=m - 0.28 * dd,
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=0,
                                    mutation_scale=13, shrinkA=0, shrinkB=0), zorder=6)

    p_start = np.array([-1.72, y2 - (xP + 1.72) * np.tan(np.radians(u))])
    p_end   = np.array([4.62,  y2 + (4.62 - xP) * np.tan(np.radians(up))])
    ray2(p_start, P, BLUE, head_at=0.60)
    ray2(P, p_end, RED, head_at=0.55)

    def angle_arc(center, r, a0, a1, color, lw=1.5, cw=False):
        # magnitude arc (matplotlib always sweeps theta1 -> theta2 with
        # increasing angle, CCW in the data plane) plus a direction arrow.
        # Angles are signed: positive (CCW = toward +y) angles get a CCW
        # arrow (u, i, and i' here), negative angles get a CW arrow (u', alpha).
        ax.add_patch(Arc(center, 2 * r, 2 * r, angle=0, theta1=min(a0, a1),
                         theta2=max(a0, a1), color=color, lw=lw, zorder=7))
        th = np.radians((a0 + a1) / 2)
        mid = np.array(center) + r * np.array([np.cos(th), np.sin(th)])
        tangent = np.array([-np.sin(th), np.cos(th)])   # CCW tangent in 1st quadrant
        if cw:
            tangent = -tangent
        ax.annotate("", xy=mid, xytext=mid - 0.34 * tangent,
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=0,
                                    mutation_scale=11, shrinkA=0, shrinkB=0), zorder=8)

    angle_arc(P, 0.95, 180, 180 + u, BLUE)
    angle_arc(P, 1.30, 150, 180 + u, BLUE)
    angle_arc(P, 0.85, -u, 0, RED, cw=True)
    angle_arc(P, 1.12, -30, -u, RED)
    angle_arc(C, 1.15, 150, 180, GRAY, cw=True)

    ax.plot(P[0], P[1], "o", ms=6.5, color=INK, mec="white", mew=1.4, zorder=9)

    # angle labels carry their signed values, so the sign convention
    # (positive = counterclockwise from +z toward +y) can be read off in place
    ax.text(-0.82, 1.70, r"$u=+6^{\circ}$", fontsize=11, color=BLUE, ha="center", va="center")
    ax.text(-1.14, 2.30, r"$i=36^{\circ}$", fontsize=14, color=BLUE, ha="center", va="center")
    ax.text(1.42, 1.64, r"$u'=-6^{\circ}$", fontsize=11, color=RED, ha="left", va="center")
    ax.text(1.95, 1.50, r"$i'=24^{\circ}$", fontsize=14, color=RED, ha="left", va="center")
    ax.text(3.40, 0.62, r"$\alpha=-30^{\circ}$", fontsize=14, color=GRAY, ha="center", va="center")

    # sign-convention indicator: +z and +y axes with the positive (counterclockwise) sense
    ox, oy, s = -1.48, 2.62, 0.34
    ax.annotate("", xy=(ox + s, oy), xytext=(ox, oy),
                arrowprops=dict(arrowstyle="-|>", color=DIM, lw=1.2,
                                mutation_scale=10, shrinkA=0, shrinkB=0), zorder=6)
    ax.annotate("", xy=(ox, oy + s), xytext=(ox, oy),
                arrowprops=dict(arrowstyle="-|>", color=DIM, lw=1.2,
                                mutation_scale=10, shrinkA=0, shrinkB=0), zorder=6)
    ax.text(ox + s + 0.05, oy, r"$+z$", fontsize=10, color=GRAY,
            ha="left", va="center", zorder=7)
    ax.text(ox + 0.05, oy + s + 0.02, r"$+y$", fontsize=10, color=GRAY,
            ha="left", va="bottom", zorder=7)
    ax.add_patch(Arc((ox, oy), 2 * 0.19, 2 * 0.19, theta1=3, theta2=87,
                     color=BLUE, lw=1.3, zorder=7))
    th = np.radians(45)
    mid = np.array([ox, oy]) + 0.19 * np.array([np.cos(th), np.sin(th)])
    ax.annotate("", xy=mid, xytext=mid - 0.11 * np.array([-np.sin(th), np.cos(th)]),
                arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=0,
                                mutation_scale=9, shrinkA=0, shrinkB=0), zorder=8)
    ax.text(ox, oy - 0.14, "positive", fontsize=9, color=GRAY,
            ha="center", va="top", zorder=7)

    ax.text(0.80, 2.20, r"$P$", fontsize=14, color=INK, ha="left", va="center")
    ax.text(4.12, -0.28, r"$C$", fontsize=14, color=INK, ha="center", va="center")
    ax.text(-0.19, -0.29, r"$V$", fontsize=13, color=INK, ha="center", va="center")

    ax.text(-1.66, 0.55, r"$n$", fontsize=13, color=GRAY, ha="left", va="center")
    ax.text(3.42, 1.22, r"$n'$", fontsize=13, color=GRAY, ha="left", va="center")

    ax.text(2.38, 3.14,
            r"$i \;=\; u-\alpha$" + "\n" +
            r"$i' \;=\; u'-\alpha$" + "\n" +
            r"$\alpha \;\approx\; -y/R$" + "\n" +
            r"$n\,i \;=\; n' i'$",
            fontsize=12.5, color=INK, ha="left", va="top", linespacing=1.6)

    fig.savefig(path_svg, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


if __name__ == "__main__":
    figure1("images/optical_power_conjugates.svg")
    figure2("images/optical_power_angles.svg")
    print("wrote images/optical_power_conjugates.svg")
    print("wrote images/optical_power_angles.svg")
