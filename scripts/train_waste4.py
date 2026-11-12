"""Train the 4-category classifier (biodegradable / recyclable / non-recyclable / medical) on SigLIP 2 embeddings.

Compares three heads on the validation split, picks the best, then reports once on the test split:
  A. zero-shot   : image vs. text concepts (config.CONCEPTS), no training data
  B. linear probe: logistic regression on labelled embeddings (fine-grained classes -> category)
  C. blend       : w * A + (1 - w) * B, with w tuned on validation

    python scripts/embed_dataset.py     # once
    python scripts/train_waste4.py
"""
import argparse
import json

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score

from waste_classifier.cnn import get_device
from waste_classifier.config import (CATEGORIES, CM_FIG_DIR, PROCESSED_DIR,
                                     RESULTS_DIR, SEED, WASTE4_MODEL_PATH)
from waste_classifier.plotting import save_confusion_matrix
from waste_classifier.vlm import SigLIP, Waste4Classifier

EMB_PATH = PROCESSED_DIR / "siglip_embeddings.npz"


def load():
    z = np.load(EMB_PATH, allow_pickle=True)  # our own file; older versions stored strings as objects
    df = pd.DataFrame({k: z[k] for k in ["path", "label", "subtype", "category", "source", "split"]})
    return df, torch.as_tensor(z["emb"].astype(np.float32))


def cat_scores(y_true, probs):
    pred = probs.argmax(1)
    return {"accuracy": accuracy_score(y_true, pred), "macro_f1": f1_score(y_true, pred, average="macro")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target-acc", type=float, default=0.99,
                    help="accuracy on accepted items the UNKNOWN threshold should reach on validation")
    args = ap.parse_args()

    df, emb = load()
    y_cat = df.category.map(CATEGORIES.index).values
    split = {s: (df.split == s).values for s in ("train", "val", "test")}
    print(pd.crosstab(df.category, df.split).to_string(), "\n")

    # ---------- text side: concept embeddings
    vlm = SigLIP(device=get_device())
    names, cats, concept_emb = vlm.concept_embeddings()
    print(f"{len(names)} text concepts | logit scale {vlm.logit_scale:.1f}")

    # ---------- B: linear probe on fine-grained labels
    classes = sorted(df.label.unique())
    cls_cat = df.groupby("label").category.first().to_dict()
    y_cls = df.label.map(classes.index).values
    best = None
    for C in [0.5, 1, 2, 5, 10, 20]:
        clf = LogisticRegression(C=C, max_iter=3000, class_weight="balanced", random_state=SEED)
        clf.fit(emb[split["train"]].numpy(), y_cls[split["train"]])
        state = {"probe_W": clf.coef_.astype(np.float32), "probe_b": clf.intercept_.astype(np.float32)}
        tmp = {"categories": CATEGORIES, "concept_emb": concept_emb, "concept_cats": cats,
               "concept_names": names, "zs_scale": vlm.logit_scale, "probe_classes": classes,
               "probe_class_cats": [cls_cat[c] for c in classes],
               "w_zeroshot": 0.0, "threshold": 0.5, **state}
        s = cat_scores(y_cat[split["val"]], Waste4Classifier(tmp).predict(emb[split["val"]])["probe"])
        print(f"probe C={C:<4} val acc {s['accuracy']:.4f} macro-F1 {s['macro_f1']:.4f}")
        if best is None or s["macro_f1"] > best[0]:
            best = (s["macro_f1"], C, tmp)
    _, best_C, state = best

    # ---------- A + C: zero-shot temperature and blend weight on validation
    model = Waste4Classifier(state)
    rows = []
    for zs_scale in [10, 25, 50, 100, vlm.logit_scale]:
        model.zs_scale = zs_scale
        for w in np.round(np.arange(0, 1.01, 0.1), 2):
            model.w_zs = w
            s = cat_scores(y_cat[split["val"]], model.predict(emb[split["val"]])["probs"])
            rows.append({"zs_scale": zs_scale, "w_zeroshot": w, **s})
    grid = pd.DataFrame(rows)
    zs_only = grid[grid.w_zeroshot == 1.0].sort_values("macro_f1").iloc[-1]
    # Prefer the simplest model (smallest zero-shot weight) within 0.002 macro-F1 of the best:
    # differences smaller than that are validation noise, and heavy blending flattens confidences.
    near = grid[grid.macro_f1 >= grid.macro_f1.max() - 0.002]
    best_row = near.sort_values(["w_zeroshot", "zs_scale"], ascending=[True, False]).iloc[0]
    print(f"\nVal  A zero-shot only : acc {zs_only.accuracy:.4f} macro-F1 {zs_only.macro_f1:.4f}")
    print(f"Val  B probe only     : acc {grid[grid.w_zeroshot == 0].accuracy.max():.4f} "
          f"macro-F1 {grid[grid.w_zeroshot == 0].macro_f1.max():.4f}  (C={best_C})")
    print(f"Val  C blend          : acc {best_row.accuracy:.4f} macro-F1 {best_row.macro_f1:.4f}  "
          f"(w_zeroshot={best_row.w_zeroshot}, zs_scale={best_row.zs_scale:.0f})")
    state["zs_scale"], state["w_zeroshot"] = float(best_row.zs_scale), float(best_row.w_zeroshot)
    model = Waste4Classifier(state)

    # ---------- UNKNOWN threshold on validation
    vp = model.predict(emb[split["val"]])["probs"]
    conf, correct = vp.max(1), vp.argmax(1) == y_cat[split["val"]]
    thr = next((round(t, 2) for t in np.arange(0.3, 0.96, 0.01)
                if correct[conf >= t].mean() >= args.target_acc), 0.95)
    state["threshold"] = thr
    model = Waste4Classifier(state)

    # ---------- final test report (touched once)
    te = split["test"]
    out = model.predict(emb[te])
    yt = y_cat[te]
    results = {}
    for head in ["zero_shot", "probe", "probs"]:
        results[head] = cat_scores(yt, out[head])
    pred = out["probs"].argmax(1)
    tdf = df[te].assign(pred=[CATEGORIES[i] for i in pred], ok=pred == yt, conf=out["probs"].max(1))
    keep = tdf.conf >= thr

    print(f"\n========== TEST ({te.sum()} images) ==========")
    for head, name in [("zero_shot", "A zero-shot"), ("probe", "B probe"), ("probs", "C final blend")]:
        print(f"{name:15s} accuracy {results[head]['accuracy']:.4f} | macro-F1 {results[head]['macro_f1']:.4f}")
    print("\nPer source:\n" + tdf.groupby("source").ok.agg(["mean", "size"]).round(4).to_string())
    med = tdf[tdf.category == "medical"]
    if len(med):
        print("\nMedical recall per item type:\n" + med.groupby("subtype").ok.agg(["mean", "size"]).round(3).to_string())
    fp_med = (tdf[tdf.category != "medical"].pred == "medical").mean()
    print(f"Non-medical items wrongly flagged as medical: {fp_med:.2%}")
    print(f"\nUNKNOWN threshold {thr}: {keep.mean():.1%} accepted, {tdf[keep].ok.mean():.2%} of those correct")
    report = classification_report(yt, pred, labels=range(len(CATEGORIES)), target_names=CATEGORIES, digits=3)
    print("\n" + report)

    # ---------- save
    state["meta"] = {"vlm": vlm.model_id, "probe_C": best_C, "test": results,
                     "test_per_source": tdf.groupby("source").ok.mean().to_dict(),
                     "false_medical_rate": float(fp_med)}
    model.save(WASTE4_MODEL_PATH)
    (RESULTS_DIR / "metrics").mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "metrics" / "waste4_siglip.json").write_text(json.dumps(
        {**state["meta"], "threshold": thr, "w_zeroshot": state["w_zeroshot"], "zs_scale": state["zs_scale"]},
        indent=2, default=float))
    (RESULTS_DIR / "metrics" / "waste4_siglip_report.txt").write_text(report)
    grid.to_csv(RESULTS_DIR / "metrics" / "waste4_val_grid.csv", index=False)
    save_confusion_matrix([CATEGORIES[i] for i in yt], list(tdf.pred), CATEGORIES,
                          "Confusion Matrix - 4 categories (test)", CM_FIG_DIR / "waste4_siglip.png")
    print(f"Saved {WASTE4_MODEL_PATH}")


if __name__ == "__main__":
    main()
