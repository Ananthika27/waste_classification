"""Checks on the prepared dataset: no leakage between splits, all classes present."""
import pandas as pd
import pytest

from waste_classifier.config import MANIFEST_PATH, PROJECT_ROOT, WASTE10_CLASSES

pytestmark = pytest.mark.skipif(not MANIFEST_PATH.exists(), reason="run scripts/prepare_data.py first")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(MANIFEST_PATH)


def test_no_exact_duplicates(df):
    assert df.md5.is_unique


def test_near_duplicate_groups_never_cross_splits(df):
    assert (df.groupby("group").split.nunique() == 1).all()
    assert (df.groupby("dhash").split.nunique() == 1).all()


def test_every_class_in_every_split(df):
    for split in ("train", "val", "test"):
        assert set(df[df.split == split].label) == set(WASTE10_CLASSES)


def test_split_proportions(df):
    frac = df.split.value_counts(normalize=True)
    assert abs(frac["train"] - 0.70) < 0.03
    assert abs(frac["val"] - 0.15) < 0.03


def test_prepared_files_exist(df):
    sample = df.sample(min(200, len(df)), random_state=0)
    assert all((PROJECT_ROOT / p).exists() for p in sample.path)
