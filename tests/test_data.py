import pytest

from waste_classifier.config import DATASETS, GARBAGE10_MAX_PER_CLASS
from waste_classifier.data import load_file_list


def needs(dataset):
    return pytest.mark.skipif(not DATASETS[dataset]["root"].exists(),
                              reason=f"dataset '{dataset}' not downloaded")


def test_unknown_dataset_raises():
    with pytest.raises(ValueError):
        load_file_list("nope")


@needs("trashnet")
def test_trashnet_counts():
    files, labels, classes = load_file_list("trashnet")
    assert classes == ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
    assert len(files) == len(labels) == 2527


@needs("garbage10")
def test_garbage10_is_balanced_and_merges_glass():
    files, labels, classes = load_file_list("garbage10")
    assert len(classes) == 10 and "glass" in classes
    assert all(labels.count(c) == GARBAGE10_MAX_PER_CLASS for c in classes)
    glass = [f for f, l in zip(files, labels) if l == "glass"]
    assert {"brown-glass", "green-glass", "white-glass"} <= {f.split("/")[-2] for f in glass}


@needs("garbage10")
def test_sampling_is_reproducible():
    assert load_file_list("garbage10") == load_file_list("garbage10")
    assert load_file_list("garbage10", seed=1)[0] != load_file_list("garbage10")[0]
