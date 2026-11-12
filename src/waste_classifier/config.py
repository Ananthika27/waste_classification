"""Central configuration: paths, class definitions and shared constants."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---- Paths ----
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
PIPELINE_FIG_DIR = FIGURES_DIR / "pipeline"
CM_FIG_DIR = FIGURES_DIR / "confusion_matrices"

TRASHNET_DIR = RAW_DIR / "trashnet"
GARBAGE_DIR = RAW_DIR / "garbage12"

DEFAULT_CNN_PATH = MODELS_DIR / "mobilenetv2_garbage10.pt"

# ---- Reproducibility ----
SEED = 42
TEST_SIZE = 0.2

IMAGE_EXTS = (".jpg", ".jpeg", ".png")

# ---- Datasets ----
# TrashNet: 6 classes, one folder per class.
TRASHNET_CLASS_MAP = {c: [c] for c in
                      ["cardboard", "glass", "metal", "paper", "plastic", "trash"]}

# Garbage Classification (12 folders) merged into 10 classes.
GARBAGE10_CLASS_MAP = {
    "battery":    ["battery"],
    "biological": ["biological"],
    "cardboard":  ["cardboard"],
    "clothes":    ["clothes"],
    "glass":      ["brown-glass", "green-glass", "white-glass"],
    "metal":      ["metal"],
    "paper":      ["paper"],
    "plastic":    ["plastic"],
    "shoes":      ["shoes"],
    "trash":      ["trash"],
}
GARBAGE10_MAX_PER_CLASS = 600

DATASETS = {
    "trashnet":  {"root": TRASHNET_DIR, "class_map": TRASHNET_CLASS_MAP, "max_per_class": None},
    "garbage10": {"root": GARBAGE_DIR, "class_map": GARBAGE10_CLASS_MAP,
                  "max_per_class": GARBAGE10_MAX_PER_CLASS},
}

# ---- Combined multi-source dataset for the CNN (see scripts/prepare_data.py) ----
REALWASTE_DIR = RAW_DIR / "realwaste"
INTERIM_DIR = DATA_DIR / "interim"          # resized, de-duplicated copies used for training
MANIFEST_PATH = PROCESSED_DIR / "manifest.csv"
PREPARED_SHORT_SIDE = 288                   # resize so the shorter side is this many pixels
SPLIT_FRACTIONS = {"train": 0.70, "val": 0.15, "test": 0.15}

# source name -> (root folder, {source folder: target class})
SOURCES = {
    "garbage12": (GARBAGE_DIR, {f: c for c, fs in GARBAGE10_CLASS_MAP.items() for f in fs}),
    "trashnet":  (TRASHNET_DIR, {c: c for c in TRASHNET_CLASS_MAP}),
    "realwaste": (REALWASTE_DIR, {
        "Cardboard": "cardboard",
        "Food Organics": "biological",
        "Glass": "glass",
        "Metal": "metal",
        "Miscellaneous Trash": "trash",
        "Paper": "paper",
        "Plastic": "plastic",
        "Textile Trash": "clothes",
        "Vegetation": "biological",
    }),
}
WASTE10_CLASSES = sorted(GARBAGE10_CLASS_MAP)

# Which bin each class goes to (used by the real-time system)
CLASS_TO_BIN = {
    "paper": "recyclable", "cardboard": "recyclable", "plastic": "recyclable",
    "metal": "recyclable", "glass": "recyclable",
    "biological": "organic", "battery": "hazardous",
    "clothes": "textile", "shoes": "textile", "trash": "general",
}

# ---- 4-category disposal system (biodegradable / recyclable / non-recyclable / medical) ----
CATEGORIES = ["biodegradable", "recyclable", "non_recyclable", "medical"]
CATEGORY_LABELS = {"biodegradable": "Biodegradable", "recyclable": "Recyclable",
                   "non_recyclable": "Non-recyclable", "medical": "Medical waste"}

# Training-data classes -> category. Rule: paper/books recyclable; cloth, leather, shoes non-recyclable.
CLASS_TO_CATEGORY = {
    "biological": "biodegradable",
    "paper": "recyclable", "cardboard": "recyclable", "plastic": "recyclable",
    "metal": "recyclable", "glass": "recyclable",
    "clothes": "non_recyclable", "shoes": "non_recyclable", "trash": "non_recyclable",
    "battery": "non_recyclable",     # hazardous: special collection point
    "medical": "medical",
}

# Text descriptions for the vision-language model, grouped by category.
CONCEPTS = {
    "biodegradable": [
        "food scraps", "leftover cooked food", "a banana peel", "fruit peels", "vegetable peels and scraps",
        "dry leaves", "fresh green leaves", "flowers", "eggshells", "a rotten fruit", "a piece of bread",
        "a coconut shell", "tea leaves", "garden waste and twigs",
    ],
    "recyclable": [
        "a sheet of paper", "a handwritten note", "a notebook", "a book", "a newspaper", "a magazine",
        "a cardboard box", "a paper bag", "an empty plastic water bottle", "a plastic container",
        "a plastic jug", "an aluminium drink can", "a metal tin can", "a glass bottle", "a glass jar",
        "a steel spoon",
    ],
    "non_recyclable": [
        "a thermocol (styrofoam) piece", "a styrofoam food container", "a chips packet",
        "a candy wrapper", "a multilayer plastic wrapper", "a dirty food-stained packaging",
        "a cloth handkerchief", "a piece of cloth", "old clothes", "a leather belt", "a leather wallet",
        "a leather shoe", "a sneaker", "a rubber slipper", "a toothbrush", "a used diaper",
        "a cigarette butt", "a broken ceramic cup", "a battery",
    ],
    "medical": [
        "an empty tablet blister strip", "a blister pack of pills", "a strip of medicine tablets",
        "a used syringe", "an injection syringe with needle", "a hypodermic needle",
        "a disposable surgical face mask", "an N95 mask", "used medical gloves", "latex gloves",
        "a medicine bottle", "a pill bottle", "a glass medicine vial", "an ampoule",
        "a used bandage", "cotton gauze with blood", "a cotton swab", "an IV drip bag", "a saline bottle",
    ],
}
PROMPT_TEMPLATES = [
    "a photo of {}.", "a close-up photo of {}.", "a photo of {} held in a hand.",
    "a photo of discarded {}.", "{} lying on a table.",
]
VLM_HUB_ID = "google/siglip2-base-patch16-224"
_VLM_LOCAL = MODELS_DIR / "siglip2-base-patch16-224"     # filled by curl / huggingface download
VLM_MODEL_ID = str(_VLM_LOCAL) if (_VLM_LOCAL / "model.safetensors").exists() else VLM_HUB_ID
WASTE4_MODEL_PATH = MODELS_DIR / "waste4_siglip.pt"
MEDICAL_DIR = RAW_DIR / "medical_commons"

# ---- Classical pipeline ----
FEATURE_IMAGE_SIZE = 256
UNKNOWN_THRESHOLD_CLASSICAL = 0.5

# ---- CNN ----
CNN_IMAGE_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
UNKNOWN_THRESHOLD_CNN = 0.60
