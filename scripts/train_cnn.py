"""Train a CNN waste classifier on the combined, de-duplicated dataset (data/processed/manifest.csv).

Recipe: ImageNet-pretrained backbone, strong augmentation, class-balanced sampling,
AdamW + warmup/cosine schedule, label smoothing, best epoch chosen on the validation split,
early stopping, temperature scaling and an automatically chosen "unknown" threshold.
The held-out test split is touched only once, at the end.

    python scripts/prepare_data.py                    # once
    python scripts/train_cnn.py --arch convnext_tiny --epochs 15
    python scripts/train_cnn.py --arch mobilenet_v3_large --epochs 20
    python scripts/train_cnn.py --limit 64 --epochs 1  # quick smoke test
"""
import argparse
import copy
import json
import math
import random
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, classification_report, f1_score
from torch.utils.data import DataLoader, WeightedRandomSampler

from waste_classifier.cnn import (ARCHS, ImageDataset, backbone_parameters, build_model, get_device,
                                  head_parameters, make_eval_transform, make_train_transform,
                                  save_checkpoint)
from waste_classifier.config import (CM_FIG_DIR, FIGURES_DIR, MANIFEST_PATH, MODELS_DIR, PROJECT_ROOT,
                                     RESULTS_DIR, SEED, WASTE10_CLASSES)
from waste_classifier.plotting import save_confusion_matrix

METRICS_DIR = RESULTS_DIR / "metrics"


# ------------------------------------------------------------------ helpers
def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_splits(classes, limit=None):
    df = pd.read_csv(MANIFEST_PATH)
    df["file"] = df.path.map(lambda p: str(PROJECT_ROOT / p))
    df["y"] = df.label.map(classes.index)
    splits = {s: df[df.split == s].reset_index(drop=True) for s in ("train", "val", "test")}
    if limit:  # small stratified subset for smoke tests
        splits = {s: d.groupby("label", group_keys=False).head(limit).reset_index(drop=True)
                  for s, d in splits.items()}
    return splits


@torch.no_grad()
def predict_logits(model, loader, device, tta=False):
    model.eval()
    out = []
    for x, _ in loader:
        x = x.to(device)
        logits = model(x)
        if tta:
            logits = (logits + model(torch.flip(x, dims=[3]))) / 2
        out.append(logits.float().cpu())
    return torch.cat(out)


def fit_temperature(logits, labels):
    """Temperature scaling (Guo et al., 2017): one scalar T minimising validation NLL."""
    log_t = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([log_t], lr=0.1, max_iter=200)
    y = torch.as_tensor(labels)

    def closure():
        opt.zero_grad()
        loss = F.cross_entropy(logits / log_t.exp(), y)
        loss.backward()
        return loss

    opt.step(closure)
    return float(log_t.detach().exp())


def ece(probs, labels, n_bins=15):
    """Expected calibration error."""
    conf, pred = probs.max(1)
    correct = pred.eq(torch.as_tensor(labels)).float()
    edges = torch.linspace(0, 1, n_bins + 1)
    err = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            err += m.float().mean() * (conf[m].mean() - correct[m].mean()).abs()
    return float(err)


def choose_threshold(probs, labels, target_acc):
    """Lowest confidence threshold whose accepted predictions reach `target_acc` on validation."""
    conf, pred = probs.max(1)
    correct = pred.eq(torch.as_tensor(labels))
    for t in np.arange(0.30, 0.96, 0.01):
        keep = conf >= t
        if keep.any() and correct[keep].float().mean() >= target_acc:
            return round(float(t), 2)
    return 0.95


def selective(probs, labels, t):
    conf, pred = probs.max(1)
    keep = conf >= t
    correct = pred.eq(torch.as_tensor(labels))
    return {"threshold": t, "coverage": float(keep.float().mean()),
            "accuracy_on_accepted": float(correct[keep].float().mean()) if keep.any() else None}


@torch.no_grad()
def latency_ms(model, device, size, n=50):
    model.eval()
    x = torch.randn(1, 3, size, size, device=device)
    for _ in range(10):
        model(x)
    if device == "mps":
        torch.mps.synchronize()
    t = time.perf_counter()
    for _ in range(n):
        model(x)
    if device == "mps":
        torch.mps.synchronize()
    return (time.perf_counter() - t) / n * 1000


def plot_history(hist, path):
    h = pd.DataFrame(hist)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(h.epoch, h.train_loss, label="train")
    ax[0].plot(h.epoch, h.val_loss, label="validation")
    ax[0].set(title="Loss", xlabel="epoch")
    ax[1].plot(h.epoch, h.train_acc, label="train")
    ax[1].plot(h.epoch, h.val_acc, label="validation")
    ax[1].plot(h.epoch, h.val_f1, label="validation macro-F1", linestyle="--")
    ax[1].set(title="Accuracy", xlabel="epoch")
    for a in ax:
        a.grid(alpha=0.3)
        a.legend()
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=120)
    plt.close()


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arch", choices=list(ARCHS), default="convnext_tiny")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch-size", type=int, default=48)
    ap.add_argument("--lr", type=float, default=2e-4, help="backbone learning rate (head gets 10x)")
    ap.add_argument("--weight-decay", type=float, default=0.05)
    ap.add_argument("--warmup-epochs", type=float, default=1.0)
    ap.add_argument("--label-smoothing", type=float, default=0.1)
    ap.add_argument("--img-size", type=int, default=224)
    ap.add_argument("--patience", type=int, default=5, help="early stopping on val macro-F1")
    ap.add_argument("--no-balance", action="store_true", help="disable class-balanced sampling")
    ap.add_argument("--target-acc", type=float, default=0.98,
                    help="validation accuracy the 'unknown' threshold should guarantee on accepted items")
    ap.add_argument("--tta", action="store_true", help="flip test-time augmentation for the final test")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, help="images per class per split (smoke test)")
    ap.add_argument("--name", help="run name (default: <arch>_waste10)")
    args = ap.parse_args()

    seed_everything(SEED)
    name = args.name or f"{args.arch}_waste10"
    classes = WASTE10_CLASSES
    device = get_device()
    splits = load_splits(classes, args.limit)
    print(f"Device: {device} | arch: {args.arch} | " +
          " | ".join(f"{s}: {len(d)}" for s, d in splits.items()))

    tr = splits["train"]
    if args.no_balance:
        sampler, shuffle = None, True
    else:  # every class is drawn equally often
        w = 1.0 / tr.y.map(tr.y.value_counts()).values
        sampler, shuffle = WeightedRandomSampler(torch.as_tensor(w, dtype=torch.double), len(tr),
                                                 generator=torch.Generator().manual_seed(SEED)), False
    loader_kw = dict(batch_size=args.batch_size, num_workers=args.workers,
                     persistent_workers=args.workers > 0)
    train_dl = DataLoader(ImageDataset(tr.file, tr.y, make_train_transform(args.img_size)),
                          sampler=sampler, shuffle=shuffle, drop_last=True, **loader_kw)
    eval_tf = make_eval_transform(args.img_size)
    val_dl = DataLoader(ImageDataset(splits["val"].file, splits["val"].y, eval_tf), **loader_kw)
    test_dl = DataLoader(ImageDataset(splits["test"].file, splits["test"].y, eval_tf), **loader_kw)

    model = build_model(len(classes), args.arch).to(device)
    opt = torch.optim.AdamW([
        {"params": backbone_parameters(model), "lr": args.lr},
        {"params": list(head_parameters(model)), "lr": args.lr * 10},
    ], weight_decay=args.weight_decay)
    total = args.epochs * len(train_dl)
    warm = int(args.warmup_epochs * len(train_dl))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / warm if s < warm else
                                              0.01 + 0.99 * 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, total - warm))))
    loss_fn = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)

    hist, best_f1, best_state, bad_epochs = [], -1.0, None, 0
    for ep in range(1, args.epochs + 1):
        model.train()
        t0, run_loss, run_correct, seen = time.time(), 0.0, 0, 0
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            loss = loss_fn(logits, y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            run_loss += loss.item() * len(y)
            run_correct += (logits.argmax(1) == y).sum().item()
            seen += len(y)

        vl = predict_logits(model, val_dl, device)
        vy = splits["val"].y.values
        vpred = vl.argmax(1).numpy()
        row = {"epoch": ep, "train_loss": run_loss / seen, "train_acc": run_correct / seen,
               "val_loss": float(F.cross_entropy(vl, torch.as_tensor(vy))),
               "val_acc": accuracy_score(vy, vpred), "val_f1": f1_score(vy, vpred, average="macro"),
               "lr": opt.param_groups[0]["lr"], "seconds": time.time() - t0}
        hist.append(row)
        improved = row["val_f1"] > best_f1
        print(f"epoch {ep:2d}/{args.epochs}  train loss {row['train_loss']:.3f} acc {row['train_acc']:.3f} | "
              f"val loss {row['val_loss']:.3f} acc {row['val_acc']:.3f} F1 {row['val_f1']:.3f} | "
              f"{row['seconds']:.0f}s{'  *best*' if improved else ''}", flush=True)
        if improved:
            best_f1, best_state, bad_epochs = row["val_f1"], copy.deepcopy(model.state_dict()), 0
        else:
            bad_epochs += 1
            if bad_epochs >= args.patience:
                print(f"Early stopping: no improvement for {args.patience} epochs")
                break

    # ---------------- calibrate on validation with the best weights
    model.load_state_dict(best_state)
    vl = predict_logits(model, val_dl, device)
    vy = splits["val"].y.values
    T = fit_temperature(vl, vy)
    vprobs = F.softmax(vl / T, 1)
    threshold = choose_threshold(vprobs, vy, args.target_acc)
    print(f"\nTemperature: {T:.3f} | unknown threshold: {threshold}")

    # ---------------- final, one-time evaluation on the test split
    te = splits["test"]
    tl = predict_logits(model, test_dl, device, tta=args.tta)
    ty = te.y.values
    tpred = tl.argmax(1).numpy()
    tprobs_raw, tprobs = F.softmax(tl, 1), F.softmax(tl / T, 1)
    per_source = {s: float(accuracy_score(ty[te.source == s], tpred[te.source == s]))
                  for s in sorted(te.source.unique())}
    metrics = {
        "run": name, "arch": args.arch, "args": vars(args), "device": device,
        "n_images": {s: len(d) for s, d in splits.items()},
        "epochs_trained": len(hist), "best_epoch": int(np.argmax([h["val_f1"] for h in hist]) + 1),
        "val_macro_f1": best_f1,
        "test_accuracy": float(accuracy_score(ty, tpred)),
        "test_macro_f1": float(f1_score(ty, tpred, average="macro")),
        "test_accuracy_per_source": per_source,
        "temperature": T,
        "ece_before_calibration": ece(tprobs_raw, ty), "ece_after_calibration": ece(tprobs, ty),
        "selective": selective(tprobs, ty, threshold),
        "latency_ms_batch1": {device: latency_ms(model, device, args.img_size)},
        "params_millions": sum(p.numel() for p in model.parameters()) / 1e6,
    }
    report = classification_report(ty, tpred, target_names=classes, digits=3)
    print(f"\nTEST accuracy {metrics['test_accuracy']:.4f} | macro-F1 {metrics['test_macro_f1']:.4f}")
    print("Per source:", {k: round(v, 4) for k, v in per_source.items()})
    print(f"ECE {metrics['ece_before_calibration']:.4f} -> {metrics['ece_after_calibration']:.4f} "
          f"after temperature scaling")
    sel = metrics["selective"]
    print(f"At threshold {threshold}: {sel['coverage']:.1%} of items accepted, "
          f"{sel['accuracy_on_accepted']:.2%} of those correct")
    print(f"Latency (batch 1, {device}): {metrics['latency_ms_batch1'][device]:.1f} ms | "
          f"{metrics['params_millions']:.1f} M parameters")
    print("\n" + report)

    # ---------------- save everything
    out = MODELS_DIR / f"{name}.pt"
    save_checkpoint(model, classes, out, arch=args.arch, img_size=args.img_size,
                    temperature=T, threshold=threshold,
                    extra={"test_accuracy": metrics["test_accuracy"], "test_macro_f1": metrics["test_macro_f1"]})
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    (METRICS_DIR / f"{name}.json").write_text(json.dumps(metrics, indent=2))
    (METRICS_DIR / f"{name}_report.txt").write_text(report)
    pd.DataFrame(hist).to_csv(METRICS_DIR / f"{name}_history.csv", index=False)
    plot_history(hist, FIGURES_DIR / "training_curves" / f"{name}.png")
    save_confusion_matrix([classes[i] for i in ty], [classes[i] for i in tpred], classes,
                          f"Confusion Matrix - {name} (test)", CM_FIG_DIR / f"{name}.png")
    print(f"Saved {out}, metrics in {METRICS_DIR}")


if __name__ == "__main__":
    main()
