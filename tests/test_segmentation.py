import numpy as np

from waste_classifier.segmentation import (clean_mask, draw_boxes, filter_small_components,
                                           get_object_mask, largest_component, otsu_mask)


def synthetic_image(h=200, w=300):
    """Bright background with one dark rectangle (the 'object') and a tiny dark speck."""
    img = np.full((h, w, 3), 230, np.uint8)
    img[50:150, 80:220] = 40      # object: 100 x 140
    img[10:12, 10:12] = 40        # 2x2 noise speck
    return img


def test_otsu_mask_makes_object_white():
    _, _, mask, thresh = otsu_mask(synthetic_image())
    assert 40 < thresh < 230
    assert mask[100, 150] == 255          # inside the object
    assert mask[190, 290] == 0            # background


def test_opening_removes_small_speck():
    _, _, mask, _ = otsu_mask(synthetic_image())
    _, cleaned = clean_mask(mask)
    assert cleaned[11, 11] == 0
    assert cleaned[100, 150] == 255


def test_largest_component_keeps_only_object():
    mask = np.zeros((100, 100), np.uint8)
    mask[10:20, 10:20] = 255   # small
    mask[40:90, 40:90] = 255   # large
    out = largest_component(mask)
    assert out[15, 15] == 0 and out[60, 60] == 255


def test_largest_component_falls_back_to_full_image():
    out = largest_component(np.zeros((50, 50), np.uint8))
    assert out.min() == 255


def test_filter_small_components_counts():
    mask = np.zeros((100, 100), np.uint8)
    mask[0:2, 0:2] = 255        # 4 px  < 1 % of 10,000
    mask[40:90, 40:90] = 255    # 2,500 px
    out, kept = filter_small_components(mask, min_area_frac=0.01)
    assert kept == 1 and out[0, 0] == 0


def test_object_mask_bounding_box_matches_object():
    mask = get_object_mask(synthetic_image())
    ys, xs = np.nonzero(mask)
    assert abs(ys.min() - 50) <= 3 and abs(ys.max() - 149) <= 3
    assert abs(xs.min() - 80) <= 3 and abs(xs.max() - 219) <= 3


def test_draw_boxes_does_not_modify_input():
    img = synthetic_image()
    before = img.copy()
    out = draw_boxes(img, get_object_mask(img))
    assert np.array_equal(img, before)
    assert (out[:, :, 1] == 255).any()     # green box drawn
