# -*- coding: utf-8 -*-
"""生成《节点与主平面》(nodal-points) 的示意图（仅 SVG）。

与 /Users/Admin/Desktop/fff.webp 相对应。绿色实线为穿过前节点 N、后节点 N'
的光线：在前主平面 P 处高度为 +y_P，穿过 N，折点落在 P' 处高度为 -y_{P'}，
两段与光轴夹角相等 (α = α')；由主平面单位横向放大率 (y_P = y_{P'}) 可得
z_PN = z'_PN = (n'-n) f_E。
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Arc
from matplotlib.path import Path as MP

cjk_candidates = ["PingFang SC", "Hiragino Sans GB", "Heiti SC", "Songti SC",
                  "Arial Unicode MS", "STHeiti", "STSong", "Noto Sans CJK SC"]
installed = {nf.name for nf in font_manager.fontManager.ttflist}
chosen = [c for c in cjk_candidates if c in installed] or ["DejaVu Sans"]
plt.rcParams["font.family"] = chosen + ["sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

OUT_SVG = "nodal_points.svg"

BLUE = "#1f6fb2"
GREEN = "#2e7d32"
RED = "#c0392b"
INK = "#20364d"
GRAY = "#555555"
GRAY2 = "#8a8f98"

# ---------------- 几何参数 ----------------
m = 0.4                      # |tan α| = |tan α'|
xN, xNp = 2.5, 7.5           # 前、后节点在光轴上的位置
xP, xPp = 0.0, 5.0           # 前、后主平面位置
zPN, zPNp = xN - xP, xNp - xPp   # 2.5, 2.5
yP = m * zPN                # 1.0（主平面处高度）
xV, yV = (xN + xNp) / 2, None   # 折点：yV = -m*(xV-xN) = -1.0
yV = -m * (xV - xN)

fig, ax = plt.subplots(figsize=(14.5, 6.6))
ax.set_aspect("equal")
ax.set_xlim(-4.9, 10.9)
ax.set_ylim(-3.4, 3.7)
ax.axis("off")

# ---------------- 光轴 ----------------
ax.annotate("", xy=(10.35, 0), xytext=(-4.55, 0),
            arrowprops=dict(arrowstyle="-|>", lw=1.0, color="0.4",
                            ls=(0, (6, 3))))
ax.text(-4.6, -0.42, "光轴", fontsize=10, color=GRAY2)

# ---------------- 系统（双凸透镜），位于两主平面之间 ----------------
xc_l, xc_r, yt, yb = 1.7, 4.3, 2.55, -2.55
verts = [(xc_l, yb), (xc_l - 0.75, 0.0), (xc_l, yt), (xc_l, yt),
         (xc_r, yt), (xc_r + 0.75, 0.0), (xc_r, yb), (xc_r, yb)]
codes = [MP.MOVETO, MP.CURVE3, MP.CURVE3, MP.CURVE3,
         MP.LINETO, MP.CURVE3, MP.CURVE3, MP.CURVE3]
patch = __import__("matplotlib.patches", fromlist=["PathPatch"]).PathPatch(
    MP(verts, codes), facecolor="#eef2f7", edgecolor=INK, lw=1.6, zorder=1)
ax.add_patch(patch)

# ---------------- 主平面 P, P'（虚线） ----------------
for x, lab in ((xP, r"$P$"), (xPp, r"$P'$")):
    ax.plot([x, x], [-2.35, 2.35], color=GRAY2, lw=1.1,
            ls=(0, (5, 3)), zorder=2)
    ax.text(x, 2.92, lab, fontsize=14, ha="center", color="0.15")

# ---------------- 介质标注 n, n'（与公式中的 n'-n 呼应） ----------------
ax.text(0.7, 2.12, r"$n$", fontsize=12, ha="center", color=GRAY)
ax.text(xPp + 0.9, 2.12, r"$n'$", fontsize=12, ha="center", color=GRAY)

# ---------------- 节点 N, N' ----------------
for x, lab in ((xN, r"$N$"), (xNp, r"$N'$")):
    ax.plot([x], [0], marker="o", ms=8, mfc=RED, mec="none", zorder=5)
    ax.text(x, -0.98, lab, fontsize=13, ha="center")

# ---------------- 绿色实线：贯穿 N 与 N' 的光线 ----------------
pts = [(-4.7, -m * (-4.7 - xN)), (xN, 0), (xV, yV), (xNp, 0), (10.25, m * (10.25 - xNp))]
ax.plot([p[0] for p in pts], [p[1] for p in pts], color=GREEN, lw=2.2,
        solid_capstyle="round", zorder=3)
for (xx, yy) in ((-1.5, -m * (-1.5 - xN)), (8.6, m * (8.6 - xNp))):
    ax.plot([xx], [yy], marker=">", ms=11, color=GREEN, zorder=4)

# ---------------- 高度 y_P, y_{P'} ----------------
ax.annotate("", xy=(xP, yP), xytext=(xP, 0),
            arrowprops=dict(arrowstyle="<->", lw=1.5, color=BLUE))
ax.text(0.12, 0.32, r"$y_P$", fontsize=13, ha="left", color=BLUE)
ax.annotate("", xy=(xPp, -yP), xytext=(xPp, 0),
            arrowprops=dict(arrowstyle="<->", lw=1.5, color=BLUE))
ax.text(xPp + 0.12, -0.72, r"$y_{P'}$", fontsize=13, ha="left", color=BLUE)

# ---------------- 距离 z_PN（左、轴下方）, z'_PN（右、轴上方） ----------------
ax.annotate("", xy=(xP, -0.35), xytext=(xN, -0.35),
            arrowprops=dict(arrowstyle="<->", lw=1.5, color="#4a4a4a"))
ax.text((xP + xN) / 2, -0.78, r"$z_{PN}$", fontsize=13, ha="center",
        color="#4a4a4a")
ax.annotate("", xy=(xPp, 0.35), xytext=(xNp, 0.35),
            arrowprops=dict(arrowstyle="<->", lw=1.5, color="#4a4a4a"))
ax.text((xPp + xNp) / 2, 0.78, r"$z'_{PN}$", fontsize=13, ha="center",
        color="#4a4a4a")

# ---------------- 夹角 α, α' ----------------
ang = 21.8                     # arctan(m) 度
ax.add_patch(Arc((xN, 0), width=0.7, height=0.7, theta1=-ang, theta2=0,
                 color=GREEN, lw=1.4, zorder=4))
ax.text(xN + 0.55, -0.22, r"$\alpha$", fontsize=13, color=GREEN)
ax.add_patch(Arc((xNp, 0), width=0.7, height=0.7, theta1=0, theta2=ang,
                 color=GREEN, lw=1.4, zorder=4))
ax.text(xNp + 0.55, 0.10, r"$\alpha'$", fontsize=13, color=GREEN)

# ---------------- 定性标注（置于光线未经过的空白区） ----------------
ax.text(-4.7, 3.32, r"主平面 $m=1$：$y_P = y_{P'}$",
        fontsize=11, color=GRAY, va="center")
ax.text(10.35, 3.32, r"节点 $m_\alpha=1$：$\alpha = \alpha'$",
        fontsize=11, color=GRAY, va="center", ha="right")

# ---------------- 结论公式 ----------------
ax.text(3.0, -2.98, r"$z_{PN} = z'_{PN} = (n'-n)\,f_E$",
        fontsize=16, color=RED, ha="center")

fig.savefig(OUT_SVG, bbox_inches="tight", facecolor="white")
print("written:", OUT_SVG)