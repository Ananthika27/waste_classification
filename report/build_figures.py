"""Generate the figures used in the project report (numbers come from results/metrics and the training logs).

    python report/build_figures.py
"""
import os
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

tnr = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
if os.path.exists(tnr):
    for f in ["Times New Roman.ttf", "Times New Roman Bold.ttf", "Times New Roman Italic.ttf"]:
        p = Path("/System/Library/Fonts/Supplemental") / f
        if p.exists():
            font_manager.fontManager.addfont(str(p))
    plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True, "figure.dpi": 100})

GREEN, BLUE, GREY, RED, AMBER = "#2B8A3E", "#1971C2", "#5F676D", "#C92A2A", "#E67700"
DEEP, TINT = "#10291D", "#EEF3EF"
CATS = ["Biodegradable", "Recyclable", "Non-recyclable", "Medical"]
CCOL = [GREEN, BLUE, GREY, RED]


def save(fig, name):
    fig.savefig(OUT / name, dpi=250, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def box(ax, x, y, w, h, text, fc=TINT, ec="#9AA8A0", tc="black", fs=10, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, color="#444444"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13, lw=1.4, color=color))


def canvas(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.axis("off"); ax.grid(False)
    return fig, ax


# ---------------------------------------------------------------- Fig: system architecture
def stepbox(ax, x, y, w, h, title, sub, dark=False, fs=10.5):
    box(ax, x, y, w, h, "", fc=DEEP if dark else TINT)
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center", fontsize=fs, fontweight="bold",
            color="white" if dark else "black", linespacing=1.2)
    ax.text(x + w / 2, y + h * 0.27, sub, ha="center", va="center", fontsize=8.6,
            color="#D6E4DA" if dark else "#444444", linespacing=1.2)

fig, ax = canvas(10, 4.4, (0, 20), (0, 8.6))
steps = [("Camera or\nimage upload", "browser"), ("Crop and\nencode", "centre box,\n384 px JPEG"), ("Web server", "Python\n/api/classify"),
         ("SigLIP 2\nencoder", "frozen,\n768 numbers"), ("Trained\nclassifier", "11 classes"), ("Decision", "threshold 0.59,\nelse Unknown")]
w, pitch = 2.75, 3.3
for i, (a_, b_) in enumerate(steps):
    x = 0.25 + i * pitch
    stepbox(ax, x, 5.0, w, 3.0, a_, b_, dark=i in (3, 4))
    if i < 5: arrow(ax, x + w + 0.04, 6.5, x + pitch - 0.04, 6.5)
ax.text(10, 4.35, "Teach loop (when an answer is wrong)", ha="center", fontsize=10, style="italic", color="#444444")
for i, (t_, x_) in enumerate([("Result card: category,\nconfidence, bars, \"looks like\"", 0.25), ("Teach button: corrected photo\nsaved by category", 7.1),
                              ("Retraining: embed_dataset.py,\ntrain_waste4.py -> new model", 13.95)]):
    box(ax, x_, 0.6, 5.8, 2.9, t_, fs=9.8)
    if i < 2: arrow(ax, x_ + 5.85, 2.05, x_ + 7.05 - 0.05, 2.05)
ax.text(10, 8.5, "Real-time path: about 21 ms of model time per image", ha="center", fontsize=10.5, style="italic")
save(fig, "fig_architecture.png")

# ---------------------------------------------------------------- Fig: data preparation flow
fig, ax = canvas(10, 3.9, (0, 20), (0, 7.8))
st = [("Collect", "22,794 images\n3 photo sources"), ("Standardise", "EXIF fix, RGB,\nshorter side 288 px"), ("Exact duplicates", "MD5 hash:\n2,380 removed"),
      ("Near-duplicates", "256-bit dHash,\ndistance <= 20:\n122 groups"), ("Split 70/15/15", "stratified, by group,\nseed 42"), ("Add medical", "1,031 photos,\nsplit 50/20/30")]
w, pitch = 2.85, 3.3
for i, (a_, b_) in enumerate(st):
    x = 0.2 + i * pitch
    box(ax, x, 4.2, w, 3.2, "", fc=TINT)
    ax.text(x + w / 2, 6.6, a_, ha="center", va="center", fontsize=10, fontweight="bold")
    ax.text(x + w / 2, 5.2, b_, ha="center", va="center", fontsize=9, color="#333333", linespacing=1.3)
    if i < 5: arrow(ax, x + w + 0.04, 5.8, x + pitch - 0.04, 5.8)
box(ax, 2.0, 0.3, 16.0, 2.6, "manifest.csv: one row per image with label, source, MD5 hash, dHash, near-duplicate group and split\n(train 14,847  |  validation 3,290  |  test 3,308)", fc="#E4F0E7", fs=10)
arrow(ax, 10, 4.15, 10, 2.95)
save(fig, "fig_dataprep.png")

# ---------------------------------------------------------------- Fig: model architecture
fig, ax = canvas(10, 4.8, (0, 20), (0, 9.6))
bx = [("Image", "224 x 224 RGB", 0.2, 3.2, False), ("SigLIP 2\nimage encoder", "ViT-B/16, frozen", 4.3, 3.8, True),
      ("Embedding", "768 numbers,\nunit length", 9.0, 3.2, False), ("Linear\nclassifier", "11 classes,\nC = 20, balanced", 13.0, 3.3, True),
      ("Category\nscores", "sum of class\nprobabilities", 17.0, 2.8, False)]
for t_, s_, x, w_, d in bx:
    stepbox(ax, x, 5.6, w_, 3.3, t_, s_, dark=d, fs=10)
for (x1, w1), x2 in zip([(0.2, 3.2), (4.3, 3.8), (9.0, 3.2), (13.0, 3.3)], [4.3, 9.0, 13.0, 17.0]):
    arrow(ax, x1 + w1 + 0.04, 7.2, x2 - 0.04, 7.2)
box(ax, 1.0, 0.6, 8.0, 3.0, "Text encoder (same model)\n68 concept descriptions x 5 sentence templates", fc="#F6F1E6", ec="#B8A98A", fs=10)
box(ax, 11.6, 0.6, 8.0, 3.0, "\"looks like: ...\" explanation\nand zero-shot baseline (83.3%)", fc="#F6F1E6", ec="#B8A98A", fs=10)
arrow(ax, 9.05, 2.1, 11.55, 2.1)
arrow(ax, 10.6, 5.55, 14.0, 3.7, "#8A8A8A")
ax.text(12.5, 4.75, "compare", fontsize=8.8, color="#555555", style="italic", ha="left")
ax.text(10, 9.3, "Final model (V4): the trained classifier makes the decision", ha="center", fontsize=10.5, style="italic")
save(fig, "fig_model.png")

# ---------------------------------------------------------------- Fig: split
fig, ax = plt.subplots(figsize=(6.4, 3.8))
splits = ["Train", "Validation", "Test"]
data = {"Biodegradable": [1284, 274, 274], "Recyclable": [6152, 1267, 1270], "Non-recyclable": [6903, 1536, 1454], "Medical": [508, 213, 310]}
bottom = np.zeros(3)
for (k, v), c in zip(data.items(), CCOL):
    ax.bar(splits, v, bottom=bottom, color=c, label=k, width=0.55)
    bottom += np.array(v)
for i, t in enumerate(bottom): ax.text(i, t + 150, f"{int(t):,}", ha="center", fontsize=10)
ax.set_ylabel("Images"); ax.set_ylim(0, 17000); ax.legend(frameon=False, ncol=2, loc="upper right")
save(fig, "fig_split.png")

# ---------------------------------------------------------------- Fig: MobileNetV2 curves
ep = np.arange(1, 8)
fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.5))
ax[0].plot(ep, [1.122, .567, .459, .326, .182, .128, .081], "o-", color=BLUE, lw=2); ax[0].set_title("Training loss"); ax[0].set_ylim(0, 1.3)
ax[1].plot(ep, [85.2, 87.4, 88.7, 93.4, 94.3, 94.8, 95.7], "o-", color=GREEN, lw=2); ax[1].set_title("Held-out accuracy (%)"); ax[1].set_ylim(80, 100)
for a in ax:
    a.axvline(3.5, color="#999", ls="--", lw=1); a.set_xlabel("Epoch"); a.set_xticks(ep)
    a.text(1.8, a.get_ylim()[0] + 0.04 * np.diff(a.get_ylim())[0], "head only", ha="center", fontsize=9, color="#555")
    a.text(5.5, a.get_ylim()[0] + 0.04 * np.diff(a.get_ylim())[0], "fine-tuning", ha="center", fontsize=9, color="#555")
for x, y in zip(ep, [85.2, 87.4, 88.7, 93.4, 94.3, 94.8, 95.7]): ax[1].text(x, y + 0.6, f"{y}", ha="center", fontsize=9)
for x, y in zip(ep, [1.122, .567, .459, .326, .182, .128, .081]): ax[0].text(x, y + 0.05, f"{y:.2f}", ha="center", fontsize=9)
fig.tight_layout(); save(fig, "fig_mobilenet.png")

# ---------------------------------------------------------------- Fig: domain shift
fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.8), gridspec_kw={"width_ratios": [1, 1.1]})
lab = ["Own test set\n(10 classes)", "RealWaste\n(10 classes)", "RealWaste\n(4 categories)"]
val = [95.7, 45.1, 75.5]
ax[0].bar(lab, val, color=[GREEN, RED, AMBER], width=0.6)
for i, v in enumerate(val): ax[0].text(i, v + 1.5, f"{v}%", ha="center", fontsize=10)
ax[0].set_ylim(0, 105); ax[0].set_title("MobileNetV2 accuracy")
cl = ["trash", "cardboard", "clothes", "plastic", "glass", "biological", "paper", "metal"]
rc = [4.0, 26.6, 41.2, 43.3, 44.8, 55.2, 62.8, 65.0]
ax[1].barh(cl[::-1], rc[::-1], color=BLUE, height=0.6)
for i, v in enumerate(rc[::-1]): ax[1].text(v + 1, i, f"{v}%", va="center", fontsize=9.5)
ax[1].set_xlim(0, 80); ax[1].set_title("Recall per class on landfill photos")
fig.tight_layout(); save(fig, "fig_domainshift.png")

# ---------------------------------------------------------------- Fig: C sweep
C = ["0.5", "1", "2", "5", "10", "20"]
fig, ax = plt.subplots(figsize=(6.2, 3.6))
ax.plot(C, [97.66, 97.99, 98.27, 98.57, 98.63, 98.75], "o-", color=GREEN, lw=2, label="Validation accuracy")
ax.plot(C, [97.27, 97.53, 97.98, 98.34, 98.46, 98.48], "s-", color=BLUE, lw=2, label="Validation macro-F1")
ax.set_xlabel("Regularisation strength C"); ax.set_ylabel("Score (%)"); ax.set_ylim(97, 99); ax.legend(frameon=False, loc="lower right")
fig.tight_layout(); save(fig, "fig_csweep.png")

# ---------------------------------------------------------------- Fig: confusion matrix
cm = np.array([[271, 1, 2, 0], [0, 1264, 6, 0], [4, 22, 1428, 0], [0, 5, 2, 303]])
fig, ax = plt.subplots(figsize=(5.8, 4.8))
norm = cm / cm.sum(1, keepdims=True)
ax.imshow(norm, cmap="Greens", vmin=0, vmax=1.15); ax.grid(False)
for i in range(4):
    for j in range(4):
        ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", fontsize=12, fontweight="bold" if i == j else "normal",
                color="white" if norm[i, j] > 0.6 else "black")
ax.set_xticks(range(4)); ax.set_yticks(range(4))
ax.set_xticklabels(["Bio-\ndegradable", "Recyclable", "Non-\nrecyclable", "Medical"], fontsize=10); ax.set_yticklabels(CATS, fontsize=10)
ax.set_xlabel("Predicted category"); ax.set_ylabel("True category")
for s in ax.spines.values(): s.set_visible(False)
fig.tight_layout(); save(fig, "fig_confusion.png")

# ---------------------------------------------------------------- Fig: P / R / F1
fig, ax = plt.subplots(figsize=(7.4, 3.8))
P = [98.5, 97.8, 99.3, 100]; R = [98.9, 99.5, 98.2, 97.7]; F = [98.7, 98.7, 98.8, 98.9]
x = np.arange(4); w = 0.26
for k, (v, c, n) in enumerate([(P, BLUE, "Precision"), (R, GREEN, "Recall"), (F, AMBER, "F1-score")]):
    b = ax.bar(x + (k - 1) * w, v, w, color=c, label=n)
    for xi, vi in zip(x + (k - 1) * w, v): ax.text(xi, vi + 0.08, f"{vi:.1f}", ha="center", fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels(CATS); ax.set_ylim(96, 100.8); ax.set_ylabel("Score (%) - axis starts at 96%")
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13))
fig.tight_layout(); save(fig, "fig_prf.png")

# ---------------------------------------------------------------- Fig: by source
fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.8), gridspec_kw={"width_ratios": [1.35, 1]})
src = ["Garbage-12\n(n=2,282)", "Medical\n(n=310)", "RealWaste\n(n=690)", "TrashNet\n(n=26)"]; sv = [99.8, 97.7, 96.7, 73.1]
ax[0].bar(src, sv, color=GREEN, width=0.6)
for i, v in enumerate(sv): ax[0].text(i, v + 1.5, f"{v}%", ha="center", fontsize=10)
ax[0].set_ylim(0, 110); ax[0].set_title("Test accuracy by data source")
ax[1].bar(["Earlier CNN\n(MobileNetV2)", "Final model\n(SigLIP 2)"], [75.5, 96.7], color=[GREY, GREEN], width=0.55)
for i, v in enumerate([75.5, 96.7]): ax[1].text(i, v + 1.5, f"{v}%", ha="center", fontsize=10)
ax[1].set_ylim(0, 110); ax[1].set_title("Same 690 landfill photos")
fig.tight_layout(); save(fig, "fig_source.png")

# ---------------------------------------------------------------- Fig: medical
fig, ax = plt.subplots(figsize=(7.0, 3.6))
ml = ["Blister packs (n=13)", "Pill bottles (n=16)", "Masks (n=22)", "Ampoules, vials (n=50)", "Swabs, bandages (n=73)", "Gloves (n=26)", "Syringes, needles (n=110)"]
mv = [84.6, 93.8, 95.5, 96.0, 98.6, 100, 100]
ax.barh(ml, mv, color=RED, height=0.62)
for i, v in enumerate(mv): ax.text(v + 0.8, i, f"{v}%", va="center", fontsize=9.5)
ax.set_xlim(0, 112); ax.set_xlabel("Recall (%)")
fig.tight_layout(); save(fig, "fig_medical.png")

# ---------------------------------------------------------------- existing classical pipeline figure
shutil.copy(ROOT / "results/figures/pipeline/pipeline_all_classes.png", OUT / "fig_pipeline_classical.png")
print("done:", sorted(p.name for p in OUT.iterdir()))
