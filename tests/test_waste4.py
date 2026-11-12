import numpy as np
import torch
import torch.nn.functional as F

from waste_classifier.config import CATEGORIES, CLASS_TO_CATEGORY, CONCEPTS
from waste_classifier.vlm import Waste4Classifier


def make_state(d=16, w_zs=0.5):
    torch.manual_seed(0)
    concept_cats = ["biodegradable", "recyclable", "non_recyclable", "medical"]
    concept_emb = F.normalize(torch.eye(4, d), dim=1)       # concept i points along axis i
    probe_classes = ["biological", "paper", "trash", "medical"]
    W = np.eye(4, d, dtype=np.float32) * 20                  # class i fires on axis i
    return {"categories": CATEGORIES, "concept_emb": concept_emb, "concept_cats": concept_cats,
            "concept_names": ["leaf", "paper", "wrapper", "syringe"], "zs_scale": 50.0,
            "probe_W": W, "probe_b": np.zeros(4, np.float32), "probe_classes": probe_classes,
            "probe_class_cats": [CLASS_TO_CATEGORY[c] for c in probe_classes],
            "w_zeroshot": w_zs, "threshold": 0.6}


def test_every_training_class_has_a_category():
    assert set(CLASS_TO_CATEGORY.values()) == set(CATEGORIES)


def test_concepts_cover_all_categories():
    assert set(CONCEPTS) == set(CATEGORIES)
    assert all(len(v) >= 5 for v in CONCEPTS.values())


def test_paper_is_recyclable_and_cloth_non_recyclable():
    assert CLASS_TO_CATEGORY["paper"] == "recyclable"
    assert CLASS_TO_CATEGORY["clothes"] == "non_recyclable"


def test_predict_probabilities_sum_to_one_and_pick_right_category():
    model = Waste4Classifier(make_state())
    emb = F.normalize(torch.eye(4, 16), dim=1)               # one embedding per category axis
    out = model.predict(emb)
    assert np.allclose(out["probs"].sum(1), 1.0, atol=1e-5)
    assert list(out["probs"].argmax(1)) == [0, 1, 2, 3]


def test_blend_weight_extremes():
    emb = F.normalize(torch.eye(4, 16), dim=1)
    zs = Waste4Classifier(make_state(w_zs=1.0)).predict(emb)
    pr = Waste4Classifier(make_state(w_zs=0.0)).predict(emb)
    assert np.allclose(zs["probs"], zs["zero_shot"])
    assert np.allclose(pr["probs"], pr["probe"])


def test_save_load_roundtrip(tmp_path):
    model = Waste4Classifier(make_state())
    model.save(tmp_path / "m.pt")
    loaded = Waste4Classifier.load(tmp_path / "m.pt")
    emb = F.normalize(torch.randn(3, 16), dim=1)
    assert np.allclose(model.predict(emb)["probs"], loaded.predict(emb)["probs"])
