# -*- coding: utf-8 -*-
"""生成《13 物置于前焦点时的横向放大率》的示意图（仅 SVG）。

布局要点（基于 bbox 度量反复校正，保证文字不交叠、不越界）：
  - (a) "物置于前焦平面"说明位于左上角高处；顶部两行说明在右上方分层；
        h'=m*h->inf 放在右侧中部、光线之上。
  - (b) 图例在左上角，分支去向标注在左下/右上，x=0 标注贴近渐近线顶部。
"""
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib import font_manager

cjk_candidates = ["PingFang SC", "Hiragino Sans GB", "Heiti SC", "Songti SC",
                  "Arial Unicode MS", "STHeiti", "STSong", "Noto Sans CJK SC"]
installed = {nf.name for nf in font_manager.fontManager.ttflist}
chosen = [c for c in cjk_candidates if c in installed] or ["DejaVu Sans"]
plt.rcParams["font.family"] = chosen + ["sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

OUT_SVG = "front_focal_magnification.svg"

f = 2.2
h = 1.2
slope = h / f

BLUE = "#1f6fb2"
GREEN = "#2e7d32"
RED = "#c0392b"
INK = "#20364d"
GRAY = "#555555"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.0))
fig.subplots_adjust(wspace=0.45)

# ================================================================ 图 1 (a)
ax = ax1
ax.set_aspect("equal")
ax.set_xlim(-5.8, 6.3)
ax.set_ylim(-3.2, 3.6)
ax.axis("off")

# 主光轴
ax.plot([-5.5, 5.85], [0, 0], color="black", lw=1.0, zorder=1)
ax.annotate("", xy=(5.80, 0), xytext=(5.45, 0),
            arrowprops=dict(arrowstyle="-|>", lw=1.0, color="black"))
ax.text(5.85, 0.12, r"$x$", fontsize=12)

# 薄透镜
lens = Ellipse((0, 0), 0.20, 2.6, facecolor="#eef2f7",
               edgecolor=INK, lw=1.4, zorder=2)
ax.add_patch(lens)
ax.plot([0, 0], [-1.28, 1.28], color=INK, lw=0.8, zorder=3)

# 焦点与光心
ax.plot([-f], [0], marker="o", ms=4, mfc=RED, mec="none", zorder=4)
ax.plot([f], [0], marker="o", ms=4, mfc=RED, mec="none", zorder=4)
ax.text(-f - 0.18, -0.55, r"$F$", fontsize=13, ha="center")
ax.text(f + 0.18, -0.55, r"$F'$", fontsize=13, ha="center")
ax.text(0.20, -0.55, r"$O$", fontsize=12)

# 物体
ax.annotate("", xy=(-f, h - 0.04), xytext=(-f, 0.06),
            arrowprops=dict(arrowstyle="-|>", lw=2.2, color=RED))
ax.text(-f - 0.30, h / 2, r"$h$", fontsize=13, ha="center", color=RED)

# "物置于前焦平面"说明：左上角高处，避开物体、h 标注与光线
ax.text(-5.0, 2.4, "物置于前焦平面\n（牛顿坐标 $x=0$）",
        fontsize=9.5, ha="left", color=GRAY, va="center")

# 光线 1（蓝）：平行入射 → 过 F'
ax.plot([-f, 0], [h, h], color=BLUE, lw=1.6, zorder=3)
ax.plot([0, f], [h, 0], color=BLUE, lw=1.6, zorder=3)
x1 = 5.6
ax.plot([f, x1], [0, -slope * (x1 - f)], color=BLUE, lw=1.6, zorder=3)
ax.plot([-1.1], [h], marker=">", ms=9, color=BLUE)
ax.plot([3.2], [-slope * (3.2 - f)], marker=">", ms=9, color=BLUE)

# 光线 2（绿）：过光心
x2 = 5.4
ax.plot([-f, 0], [h, 0], color=GREEN, lw=1.6, zorder=3)
ax.plot([0, x2], [0, -slope * x2], color=GREEN, lw=1.6, zorder=3)
ax.plot([-1.0], [h - slope * 1.0], marker=">", ms=9, color=GREEN)
ax.plot([2.6], [-slope * 2.6], marker=">", ms=9, color=GREEN)

# 平行标记
for xk in (4.2,):
    y1 = -slope * (xk - f)
    y2 = -slope * xk
    for (y0, cc) in ((y1, BLUE), (y2, GREEN)):
        ax.plot([xk, xk], [y0 - 0.07, y0 + 0.07], color=cc, lw=1.6, zorder=4)

# 焦距标注
for (x0, x1_, y0, yl) in [(-f, 0, -1.05, -1.42), (0, f, -1.70, -2.05)]:
    for xx in (x0, x1_):
        ax.plot([xx, xx], [y0 - 0.12, y0 + 0.12], color="0.3", lw=0.8)
    ax.plot([x0, x1_], [y0, y0], color="0.3", lw=0.8)
    ax.text((x0 + x1_) / 2, yl, r"$f$", fontsize=12, ha="center")

# 物距标注：s = -f（物恰在前焦点，物距等于焦距）
y_s = -2.42
ax.plot([-f, 0], [y_s, y_s], color="0.45", lw=0.8)
for xx in (-f, 0):
    ax.plot([xx, xx], [y_s - 0.12, y_s + 0.12], color="0.45", lw=0.8)
ax.text(-f / 2, y_s - 0.42, r"$s=-f$（物距）",
        fontsize=10, ha="center", color="0.4")

# 像距标注：s' 指向右方无穷远
ax.annotate("", xy=(5.15, 0.60), xytext=(3.70, 0.60),
            arrowprops=dict(arrowstyle="-|>", lw=1.0, color="0.45"))
ax.text(4.42, 0.98, r"$s'$（像距）", fontsize=10, ha="center", color="0.4")

# 顶部说明：右上区域，两行上下错开
ax.text(2.6, 3.2, "出射光线相互平行",
        fontsize=9.5, ha="center", color=GRAY)
ax.text(2.6, 2.65, r"$\Rightarrow$ 像在无穷远（像距 $s'=\infty$）",
        fontsize=9.5, ha="center", color=GRAY)
# h' 发散结论：右侧中部、位于两出射光线之上
ax.text(3.55, 1.6, r"$h'=m\,h\to\infty$", fontsize=11, color=RED)

ax.set_title("(a) 物置于前焦点 $F$：像在无穷远", fontsize=12)

# ================================================================ 图 2 (b)
ax = ax2
xneg = np.linspace(-3.1, -0.24, 400)
xpos = np.linspace(0.24, 3.1, 400)
ax.plot(xneg, f / xneg, color=BLUE, lw=1.8)
ax.plot(xpos, f / xpos, color=GREEN, lw=1.8)
ax.axvline(0, color=RED, lw=1.1, ls="--")
ax.axhline(0, color="black", lw=0.8)
ax.set_xlim(-3.2, 3.2)
ax.set_ylim(-6.8, 6.8)
ax.set_xticks([-2, -1, 0, 1, 2])
ax.set_yticks([-6, -3, 0, 3, 6])
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.set_xlabel(r"$x = s + f$（物相对前焦点的带符号距离）", fontsize=11)
ax.set_ylabel(r"$m = f\,/\,x$", fontsize=12)

# 标注：内移且避开陡峭渐近区域与左上图例
ax.text(-0.45, 3.6, r"$x=0$", fontsize=10, color=RED, ha="center")
ax.text(-1.7, -4.9, "实像支\n$m\\to-\\infty$", fontsize=9.5,
        ha="center", color=BLUE, va="center")
ax.text(1.7, 4.9, "虚像支\n$m\\to+\\infty$", fontsize=9.5,
        ha="center", color=GREEN, va="center")

# 图例：左上角，ncol=1，避开曲线陡峭区
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color=BLUE, lw=1.8, label=r"$x<0$：实像支（倒立）"),
    Line2D([0], [0], color=GREEN, lw=1.8, label=r"$x>0$：虚像支（正立）"),
    Line2D([0], [0], color=RED, lw=1.1, ls="--", label=r"$x=0$：渐近线"),
]
ax.legend(handles=legend_elements, loc="upper left",
          bbox_to_anchor=(0.02, 1.00), fontsize=9, frameon=False, ncol=1)

ax.set_title("(b) 牛顿形式放大率的发散", fontsize=12)

fig.savefig(OUT_SVG, bbox_inches="tight", facecolor="white")
print("written:", OUT_SVG)