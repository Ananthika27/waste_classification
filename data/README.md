# Data

Images are not stored in git. Layout:

```
data/
├── raw/
│   ├── trashnet/      cardboard/ glass/ metal/ paper/ plastic/ trash/              2,527 images
│   ├── garbage12/     battery/ biological/ brown-glass/ cardboard/ clothes/
│   │                  green-glass/ metal/ paper/ plastic/ shoes/ trash/ white-glass/ 15,515 images
│   └── realwaste/     Cardboard/ Food Organics/ Glass/ Metal/ Miscellaneous Trash/
│                      Paper/ Plastic/ Textile Trash/ Vegetation/                     4,752 images
├── interim/           resized, de-duplicated copies (written by scripts/prepare_data.py)
└── processed/
    ├── manifest.csv   one row per training image: path, label, source, split, md5, dhash, group
    └── features_*.csv hand-crafted features for the classical pipeline
```

## Sources

| Source | Content | License | How to get it |
|---|---|---|---|
| TrashNet (Thung & Yang, 2016) | Single objects on a white board, 6 classes | MIT | github.com/garythung/trashnet |
| Garbage Classification, 12 classes (Kaggle) | Mostly web images, 12 classes | ODbL | kaggle.com/datasets/mostafaabla/garbage-classification |
| RealWaste (Single et al., 2023) | Real landfill photos, 9 classes | CC BY 4.0 | `python scripts/download_realwaste.py` |

## Combined 10-class dataset (`waste10`)

`scripts/prepare_data.py` merges all sources into 10 classes:

| Class | Garbage-12 | TrashNet | RealWaste |
|---|---|---|---|
| battery | battery | | |
| biological | biological | | Food Organics, Vegetation |
| cardboard | cardboard | cardboard | Cardboard |
| clothes | clothes | | Textile Trash |
| glass | brown-, green-, white-glass | glass | Glass |
| metal | metal | metal | Metal |
| paper | paper | paper | Paper |
| plastic | plastic | plastic | Plastic |
| shoes | shoes | | |
| trash | trash | trash | Miscellaneous Trash |

How the data are cleaned:
- **Exact duplicates** (same MD5) are removed. **2,358 of TrashNet's 2,527 images already appear in Garbage-12**, so only 169 TrashNet images are new.
- **Near-duplicates** (256-bit dHash, Hamming distance ≤ 20) are grouped, and a group always lands in a single split, so no test image has a copy in training.
- The split is a **stratified 70 / 15 / 15** train / val / test, done per class at group level with seed 42.

Result: **20,414 unique images** (train 14,339, val 3,077, test 2,998).

## Medical photos (4-category model)

`scripts/download_medical_commons.py` downloads freely licensed photos from Wikimedia Commons
(syringes and needles, blister packs, masks, gloves, pill bottles, swabs and bandages, ampoules and vials)
into `data/raw/medical_commons/`. The author and license of every file are listed in `attribution.csv`.
1,150 were downloaded; 1,031 remained after a zero-shot filter removed drawings, diagrams and documents.
They are split 50 / 20 / 30 (train / val / test) per item type. These are web photos, so expect some
label noise (e.g. a gold bar in blister packaging appears under "Blister packs").

Photos taught in the app (Teach buttons, or keys 1-4 in `realtime.py`) are saved to
`data/raw/user_captures/<category>/` and used 80 / 20 for train / val by `scripts/embed_dataset.py`.
