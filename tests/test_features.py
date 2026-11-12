import numpy as np

from waste_classifier.features import N_FEATURES, extract_features
from tests.test_segmentation import synthetic_image


def test_feature_vector_shape_and_finite():
    f = extract_features(synthetic_image())
    assert f.shape == (N_FEATURES,) == (149,)
    assert np.isfinite(f).all()


def test_shape_features_are_sensible_for_a_rectangle():
    f = extract_features(synthetic_image())
    area_frac, circularity, aspect, extent = f[:4]
    assert 0.1 < area_frac < 0.5
    assert 0.6 < circularity < 0.85        # a rectangle is less round than a circle (1.0)
    assert extent > 0.95                   # a rectangle fills its bounding box


def test_lbp_histogram_is_a_density():
    lbp = extract_features(synthetic_image())[-10:]
    assert np.isclose(lbp.sum(), 1.0)


def test_features_are_deterministic():
    img = synthetic_image()
    assert np.array_equal(extract_features(img), extract_features(img))
