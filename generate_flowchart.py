"""
Generates a system architecture flowchart for the Text Summarization project.
Run: python generate_flowchart.py
Output: plots/system_architecture_flowchart.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

os.makedirs("plots", exist_ok=True)

fig, ax = plt.subplots(figsize=(14, 20))
ax.set_xlim(0, 14)
ax.set_ylim(0, 20)
ax.axis("off")
fig.patch.set_facecolor("#F8F9FA")

# ── Color palette ─────────────────────────────────────────────────────────────
C_USER      = "#1F497D"   # dark blue  — user actions
C_FRONTEND  = "#2E74B5"   # blue       — frontend
C_BACKEND   = "#2E8B57"   # green      — backend / Flask
C_MODEL     = "#8B2252"   # purple     — model / inference
C_DECISION  = "#C55A11"   # orange     — decision
C_IO        = "#4472C4"   # mid blue   — I/O
C_WHITE     = "#FFFFFF"
C_ARROW     = "#555555"
C_TITLE_BG  = "#1F497D"


def draw_box(ax, x, y, w, h, label, sublabel=None, color="#2E74B5",
             shape="rect", fontsize=10):
    """Draw a rounded rectangle with label."""
    if shape == "diamond":
        # Diamond for decisions
        dx, dy = w / 2, h / 2
        diamond = plt.Polygon(
            [[x, y + dy], [x + dx, y + 2*dy],
             [x + w, y + dy], [x + dx, y]],
            closed=True, facecolor=color, edgecolor="white",
            linewidth=1.5, zorder=3
        )
        ax.add_patch(diamond)
        ax.text(x + w/2, y + dy, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=C_WHITE,
                zorder=4, wrap=True)
    else:
        box = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.08",
            facecolor=color, edgecolor="white",
            linewidth=1.5, zorder=3
        )
        ax.add_patch(box)
        if sublabel:
            ax.text(x + w/2, y + h*0.62, label, ha="center", va="center",
                    fontsize=fontsize, fontweight="bold", color=C_WHITE, zorder=4)
            ax.text(x + w/2, y + h*0.28, sublabel, ha="center", va="center",
                    fontsize=fontsize - 1.5, color="#D0E8FF", zorder=4,
                    style="italic")
        else:
            ax.text(x + w/2, y + h/2, label, ha="center", va="center",
                    fontsize=fontsize, fontweight="bold", color=C_WHITE,
                    zorder=4, multialignment="center")


def arrow(ax, x1, y1, x2, y2, label="", color=C_ARROW):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=1.8, mutation_scale=18),
                zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx + 0.15, my, label, fontsize=8, color=color,
                style="italic", zorder=5)


def side_arrow(ax, x1, y1, x2, y2, label="", color=C_ARROW):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=1.5, connectionstyle="arc3,rad=0.0",
                                mutation_scale=15),
                zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx + 0.1, my, label, fontsize=7.5, color=color,
                style="italic", zorder=5)


# ── Title ─────────────────────────────────────────────────────────────────────
title_box = FancyBboxPatch((0.5, 18.8), 13, 0.9,
                            boxstyle="round,pad=0.1",
                            facecolor=C_TITLE_BG, edgecolor="none", zorder=3)
ax.add_patch(title_box)
ax.text(7, 19.25, "System Architecture Flowchart — Text Summarization Website",
        ha="center", va="center", fontsize=13, fontweight="bold",
        color=C_WHITE, zorder=4)

# ── START ─────────────────────────────────────────────────────────────────────
draw_box(ax, 5.0, 17.6, 4.0, 0.7, "START", color="#1F497D", fontsize=11)
arrow(ax, 7.0, 17.6, 7.0, 17.1)

# ── User opens website ────────────────────────────────────────────────────────
draw_box(ax, 4.0, 16.3, 6.0, 0.75,
         "User Opens Website in Browser", color=C_USER, fontsize=10)
arrow(ax, 7.0, 16.3, 7.0, 15.75)

# ── Input method decision ─────────────────────────────────────────────────────
draw_box(ax, 4.5, 14.9, 5.0, 0.8,
         "Input Method?", color=C_DECISION, shape="diamond", fontsize=10)

# Left branch: File Upload
arrow(ax, 4.5, 15.3, 2.2, 15.3, color=C_DECISION)
ax.text(3.1, 15.42, "Upload File", fontsize=8.5, color=C_DECISION,
        fontweight="bold")
draw_box(ax, 0.4, 14.3, 3.2, 0.8,
         "Upload .txt / .pdf\n(≤ 5 MB)", color=C_FRONTEND, fontsize=9)
arrow(ax, 2.0, 14.3, 2.0, 13.55)
draw_box(ax, 0.4, 12.75, 3.2, 0.75,
         "POST /api/upload\nExtract Text", color=C_BACKEND, fontsize=9)
arrow(ax, 2.0, 12.75, 2.0, 12.1)
draw_box(ax, 0.4, 11.3, 3.2, 0.75,
         "Populate\nText Input Area", color=C_FRONTEND, fontsize=9)
arrow(ax, 3.6, 11.65, 5.2, 11.65, color=C_ARROW)

# Right branch: Direct text
arrow(ax, 9.5, 15.3, 11.8, 15.3, color=C_DECISION)
ax.text(10.1, 15.42, "Type / Paste", fontsize=8.5, color=C_DECISION,
        fontweight="bold")
draw_box(ax, 10.4, 14.3, 3.2, 0.8,
         "Type / Paste Text\n(≤ 10,000 chars)", color=C_FRONTEND, fontsize=9)
arrow(ax, 12.0, 14.3, 12.0, 12.1)
draw_box(ax, 10.4, 11.3, 3.2, 0.75,
         "Live Character\nCount Update", color=C_FRONTEND, fontsize=9)
arrow(ax, 10.4, 11.65, 8.8, 11.65, color=C_ARROW)

# ── Select summary length ─────────────────────────────────────────────────────
draw_box(ax, 4.5, 10.5, 5.0, 0.75,
         "Select Summary Length\n(Short / Medium / Long)", color=C_FRONTEND, fontsize=9)
arrow(ax, 7.0, 10.5, 7.0, 9.95)

# ── Click Summarize ───────────────────────────────────────────────────────────
draw_box(ax, 4.5, 9.2, 5.0, 0.7,
         'Click "Summarize" Button', color=C_USER, fontsize=10)
arrow(ax, 7.0, 9.2, 7.0, 8.65)

# ── Client-side validation ────────────────────────────────────────────────────
draw_box(ax, 4.5, 7.8, 5.0, 0.8,
         "Client-side Validation\nPassed?", color=C_DECISION,
         shape="diamond", fontsize=9)

# Validation fail → show error
arrow(ax, 9.5, 8.2, 11.5, 8.2, color="#C00000")
ax.text(9.7, 8.32, "No", fontsize=8.5, color="#C00000", fontweight="bold")
draw_box(ax, 10.4, 7.6, 3.2, 0.7,
         "Show Validation\nError Message", color="#C00000", fontsize=9)
# Loop back arrow
ax.annotate("", xy=(12.0, 9.55), xytext=(12.0, 7.6),
            arrowprops=dict(arrowstyle="-|>", color="#C00000",
                            lw=1.5, mutation_scale=14,
                            connectionstyle="arc3,rad=0.0"), zorder=2)

# Validation pass
arrow(ax, 7.0, 7.8, 7.0, 7.25, color="#2E8B57")
ax.text(7.1, 7.5, "Yes", fontsize=8.5, color="#2E8B57", fontweight="bold")

# ── POST /api/summarize ───────────────────────────────────────────────────────
draw_box(ax, 4.0, 6.4, 6.0, 0.75,
         "POST /api/summarize\n{ text, length }",
         color=C_BACKEND, fontsize=9)
arrow(ax, 7.0, 6.4, 7.0, 5.85)

# ── Show loading indicator ────────────────────────────────────────────────────
draw_box(ax, 4.5, 5.05, 5.0, 0.7,
         "Show Loading Indicator\nDisable Summarize Button",
         color=C_FRONTEND, fontsize=9)
arrow(ax, 7.0, 5.05, 7.0, 4.5)

# ── Model inference ───────────────────────────────────────────────────────────
draw_box(ax, 3.5, 3.65, 7.0, 0.75,
         "DistilBART Model Inference\n(Beam Search Decoding)",
         color=C_MODEL, fontsize=9)
arrow(ax, 7.0, 3.65, 7.0, 3.1)

# ── API response decision ─────────────────────────────────────────────────────
draw_box(ax, 4.5, 2.25, 5.0, 0.8,
         "API Response\nSuccess?", color=C_DECISION,
         shape="diamond", fontsize=9)

# Error path
arrow(ax, 4.5, 2.65, 2.5, 2.65, color="#C00000")
ax.text(3.0, 2.77, "Error", fontsize=8.5, color="#C00000", fontweight="bold")
draw_box(ax, 0.4, 2.1, 3.2, 0.7,
         "Show Error Banner\nRe-enable Button",
         color="#C00000", fontsize=9)

# Success path
arrow(ax, 7.0, 2.25, 7.0, 1.7, color="#2E8B57")
ax.text(7.1, 1.95, "Yes", fontsize=8.5, color="#2E8B57", fontweight="bold")

# ── Display summary ───────────────────────────────────────────────────────────
draw_box(ax, 4.0, 0.85, 6.0, 0.75,
         "Display Summary + Word Count\nEnable Copy & Download",
         color=C_FRONTEND, fontsize=9)

# ── END ───────────────────────────────────────────────────────────────────────
draw_box(ax, 5.5, 0.05, 3.0, 0.65, "END", color="#1F497D", fontsize=11)
arrow(ax, 7.0, 0.85, 7.0, 0.7)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_items = [
    (C_USER,     "User Action"),
    (C_FRONTEND, "Frontend (Browser)"),
    (C_BACKEND,  "Backend (Flask API)"),
    (C_MODEL,    "Model Inference"),
    (C_DECISION, "Decision"),
    ("#C00000",  "Error Path"),
]
lx, ly = 0.3, 4.5
ax.text(lx, ly + 0.3, "Legend", fontsize=9, fontweight="bold", color="#333")
for i, (color, label) in enumerate(legend_items):
    patch = FancyBboxPatch((lx, ly - i*0.42), 0.35, 0.28,
                            boxstyle="round,pad=0.04",
                            facecolor=color, edgecolor="white",
                            linewidth=1, zorder=3)
    ax.add_patch(patch)
    ax.text(lx + 0.5, ly - i*0.42 + 0.14, label,
            fontsize=8, va="center", color="#333")

plt.tight_layout(pad=0.5)
out = os.path.join("plots", "system_architecture_flowchart.png")
fig.savefig(out, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close(fig)
print(f"✓ Flowchart saved: {os.path.abspath(out)}")
