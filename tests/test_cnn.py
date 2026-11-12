import numpy as np
import pytest
import torch
from PIL import Image

from waste_classifier.cnn import (ARCHS, backbone_parameters, build_model, eval_transform,
                                  load_checkpoint, make_train_transform, save_checkpoint)
from waste_classifier.config import DEFAULT_CNN_PATH, GARBAGE10_CLASS_MAP

CLASSES = sorted(GARBAGE10_CLASS_MAP)


def test_model_output_shape():
    model = build_model(len(CLASSES), pretrained=False).eval()
    with torch.no_grad():
        out = model(torch.randn(2, 3, 224, 224))
    assert out.shape == (2, 10)


def test_eval_transform_shape():
    img = Image.fromarray(np.zeros((480, 640, 3), np.uint8))
    assert eval_transform(img).shape == (3, 224, 224)


def test_checkpoint_roundtrip_keeps_classes_and_weights(tmp_path):
    model = build_model(3, pretrained=False).eval()
    path = tmp_path / "m.pt"
    save_checkpoint(model, ["a", "b", "c"], path)
    loaded, classes = load_checkpoint(path, "cpu")
    assert classes == ["a", "b", "c"]
    x = torch.randn(1, 3, 224, 224)
    with torch.no_grad():
        assert torch.allclose(model(x), loaded(x))


@pytest.mark.parametrize("arch", list(ARCHS))
def test_every_arch_gets_correct_head(arch):
    model = build_model(10, arch=arch, pretrained=False).eval()
    with torch.no_grad():
        assert model(torch.randn(1, 3, 224, 224)).shape == (1, 10)
    head = {id(p) for p in model.classifier.parameters()}
    assert all(id(p) not in head for p in backbone_parameters(model))


def test_checkpoint_stores_calibration(tmp_path):
    path = tmp_path / "m.pt"
    save_checkpoint(build_model(3, "mobilenet_v3_large", pretrained=False), ["a", "b", "c"], path,
                    arch="mobilenet_v3_large", img_size=256, temperature=1.7, threshold=0.66)
    _, _, meta = load_checkpoint(path, "cpu", return_meta=True)
    assert (meta["arch"], meta["img_size"], meta["temperature"], meta["threshold"]) == \
        ("mobilenet_v3_large", 256, 1.7, 0.66)


def test_train_transform_output():
    img = Image.fromarray(np.random.randint(0, 255, (300, 400, 3), np.uint8))
    assert make_train_transform(224)(img).shape == (3, 224, 224)


def test_legacy_checkpoint_requires_classes(tmp_path):
    path = tmp_path / "legacy.pt"
    torch.save(build_model(10, pretrained=False).state_dict(), path)
    with pytest.raises(ValueError):
        load_checkpoint(path, "cpu")
    _, classes = load_checkpoint(path, "cpu", classes=CLASSES)
    assert classes == CLASSES


@pytest.mark.skipif(not DEFAULT_CNN_PATH.exists(), reason="trained model not present")
def test_trained_model_gives_valid_probabilities():
    model, classes = load_checkpoint(DEFAULT_CNN_PATH, "cpu", classes=CLASSES)
    assert classes == CLASSES
    x = eval_transform(Image.fromarray(np.full((300, 300, 3), 200, np.uint8))).unsqueeze(0)
    with torch.no_grad():
        p = torch.softmax(model(x), 1)
    assert torch.isclose(p.sum(), torch.tensor(1.0))
