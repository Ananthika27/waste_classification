"""Train SVM and Random Forest on hand-crafted features; report and plot the better one.

Replaces train.py / train12.py.

    python scripts/train_classical.py --dataset trashnet
    python scripts/train_classical.py --dataset garbage10
"""
import argparse
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from waste_classifier.config import (CM_FIG_DIR, DATASETS, PROCESSED_DIR, SEED, TEST_SIZE,
                                     UNKNOWN_THRESHOLD_CLASSICAL)
from waste_classifier.plotting import save_confusion_matrix


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=list(DATASETS), required=True)
    ap.add_argument("--features", type=Path, help="feature CSV (default: data/processed/features_<dataset>.csv)")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    df = pd.read_csv(args.features or PROCESSED_DIR / f"features_{args.dataset}.csv")
    X = df.drop(columns=["label"]).values
    y = df["label"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SEED, stratify=y)

    scaler = StandardScaler().fit(X_train)
    svm = SVC(kernel="rbf", C=10, gamma="scale", class_weight="balanced", probability=True,
              random_state=SEED).fit(scaler.transform(X_train), y_train)
    rf = RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                random_state=SEED).fit(X_train, y_train)

    X_test_s = scaler.transform(X_test)
    preds = {"SVM": svm.predict(X_test_s), "Random Forest": rf.predict(X_test)}
    probas = {"SVM": svm.predict_proba(X_test_s), "Random Forest": rf.predict_proba(X_test)}
    for name, p in preds.items():
        print(f"{name} accuracy: {accuracy_score(y_test, p):.3f}")

    best = max(preds, key=lambda n: accuracy_score(y_test, preds[n]))
    print("\nBest model:", best)
    print(classification_report(y_test, preds[best]))

    # Open-set rejection on the best model: low-confidence predictions become "unknown"
    probs = probas[best]
    n_unknown = int((probs.max(axis=1) < UNKNOWN_THRESHOLD_CLASSICAL).sum())
    print(f"Marked unknown (confidence < {UNKNOWN_THRESHOLD_CLASSICAL}): {n_unknown} of {len(y_test)}")

    tag = "rf" if best == "Random Forest" else "svm"
    save_confusion_matrix(y_test, preds[best], sorted(set(y)), f"Confusion Matrix - {best}",
                          CM_FIG_DIR / f"{tag}_{args.dataset}.png", show=args.show)


if __name__ == "__main__":
    main()
