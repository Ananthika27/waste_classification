# Waste Sorter

A real-time computer-vision system that sorts waste into four disposal categories:

| Category | Examples |
|---|---|
| 🟢 **Biodegradable** | food scraps, fruit and vegetable peels, leaves, flowers |
| 🔵 **Recyclable** | paper, notes, books, cardboard, plastic bottles, metal cans, glass |
| ⚪ **Non-recyclable** | thermocol, chip packets and wrappers, dirty packaging, cloth, leather, shoes, batteries* |
| 🔴 **Medical waste** | tablet blister strips, syringes and needles, masks, gloves, medicine bottles, bandages |

\* batteries are hazardous and go to a special collection point.

When the model is not confident enough, it answers **Unknown — check manually**.

It runs as a **web app** (live camera + image upload, http://localhost:8000) or as a desktop camera window.

## How it works

```
camera frame ─▶ centre crop ─▶ SigLIP 2 image encoder (Google, ViT-B/16) ─▶ 768-d embedding
                                                                              │
                     ┌────────────────────────────────────────────────────────┤
                     ▼                                                        ▼
        trained linear head                                  zero-shot text concepts
  (21k labelled photos, fine-grained                (e.g. "an empty tablet blister strip",
   classes mapped to the 4 categories)               "a used syringe", "a chips packet")
                     └──────────────▶ weighted blend ◀────────────────────────┘
                                          │
                       calibrated probabilities over the 4 categories
                                          │
                    temporal smoothing ─▶ UNKNOWN threshold ─▶ display
```

* The **trained head** learns from real photos, so it handles everyday materials accurately.
* The **zero-shot concepts** (68 text descriptions) were evaluated as a no-training baseline (83.3 % test accuracy). In the final model the trained head makes the decision, because blending the two gained under 0.002 macro-F1 on validation; the concepts are kept to produce the *"looks like: …"* explanation shown in the app.
* **Medical waste** is learned from 1,031 freely licensed Wikimedia Commons photos, since no public medical-waste image dataset could be downloaded directly.
* The blend weight, the zero-shot temperature and the UNKNOWN threshold are all tuned on the validation split. The test split is used once, for the final report.
* **Teach it:** in the app, a wrong prediction can be corrected with one click. The photo is saved to `data/raw/user_captures/` and used in the next training run. This is the fastest way to adapt the model to your own camera, lighting and items.

## Results

See [`results/metrics/waste4_siglip.json`](results/metrics/waste4_siglip.json) and the confusion matrix in [`results/figures/confusion_matrices/waste4_siglip.png`](results/figures/confusion_matrices/waste4_siglip.png).

Held-out **test split: 3,308 images**, never used for training or for choosing settings.

| Head | Accuracy | Macro-F1 |
|---|---|---|
| A. Zero-shot only (text concepts, no training) | 83.3 % | 0.818 |
| B. Trained linear head | **98.7 %** | **0.988** |
| C. Final model (B selected on validation; zero-shot used for the "looks like" explanation) | **98.7 %** | **0.988** |

| Category | Precision | Recall |
|---|---|---|
| Biodegradable | 0.985 | 0.989 |
| Recyclable | 0.978 | 0.995 |
| Non-recyclable | 0.993 | 0.982 |
| Medical waste | 1.000 | 0.977 |

| By data source | Accuracy |
|---|---|
| Garbage-12 (web images) | 99.8 % |
| **RealWaste (real landfill photos)** | **96.7 %** (old MobileNetV2 on the same 690 images: 75.5 % as 4 categories, 45.1 % as 10 classes) |
| Medical photos (Wikimedia Commons) | 97.7 % |

* **Medical** (recall per item type): syringes/needles 100 %, gloves 100 %, swabs/bandages 98.6 %, ampoules/vials 96.0 %, masks 95.5 %, pill bottles 93.8 %, blister packs 84.6 % (only 13 test photos). **0 %** of non-medical items were flagged as medical.
* **UNKNOWN threshold 0.59** (chosen on validation): 99 % of items get an answer, and 99.1 % of those answers are correct.
* **Speed:** about 21 ms per image on an Apple M-series GPU (SigLIP 2 base, 375 M parameters).

### Earlier experiments (10 material classes)

| Model | Data | Test accuracy |
|---|---|---|
| Random Forest, hand-crafted features | TrashNet, 6 classes | 73.1 % |
| Random Forest, hand-crafted features | Garbage-10 | 64.7 % |
| MobileNetV2 fine-tuned | Garbage-10 (clean photos) | 95.7 % |
| MobileNetV2 fine-tuned | **RealWaste (real landfill photos, unseen)** | **45.1 %** |

The last row is why the project moved to a larger, multi-source dataset and a vision-language backbone: a model trained only on clean studio photos fails on real-world images.

## Data

Four sources, de-duplicated and split 70 / 15 / 15 with near-duplicate grouping (details in [`data/README.md`](data/README.md)):

| Source | Images | Notes |
|---|---|---|
| Garbage Classification (12 classes, Kaggle) | 15,493 | web images |
| RealWaste (UCI, CC BY 4.0) | 4,752 | real landfill photos, `scripts/download_realwaste.py` |
| TrashNet | 169 unique | 2,358 of its 2,527 images are already in Garbage-12 |
| Wikimedia Commons medical photos | ~900 | CC-licensed, `scripts/download_medical_commons.py`, credits in `attribution.csv` |

## Quick start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && pip install -e .

# data + backbone
python scripts/download_realwaste.py
python scripts/download_medical_commons.py
python scripts/download_file.py \
  https://huggingface.co/google/siglip2-base-patch16-224/resolve/main/model.safetensors \
  models/siglip2-base-patch16-224/model.safetensors        # plus the small config/tokenizer files
python scripts/prepare_data.py          # merge, de-duplicate, split

# train the 4-category model
python scripts/embed_dataset.py         # SigLIP embeddings for every image (about 5 min in the final run; longer on a busy machine)
python scripts/train_waste4.py          # -> models/waste4_siglip.pt + metrics

# run
python webapp/server.py                 # open http://localhost:8000
python scripts/realtime.py              # or: desktop camera window
```

`scripts/overnight.sh` runs the whole training pipeline unattended and restarts the web server.

**Camera on macOS:** the web app asks for camera permission in the browser. The desktop window (`realtime.py`) needs *System Settings → Privacy & Security → Camera* enabled for your terminal or VS Code.

## Project structure

```
waste_classification/
├── src/waste_classifier/
│   ├── config.py           paths, categories, class→category map, text concepts
│   ├── data.py             dataset discovery
│   ├── vlm.py              SigLIP 2 wrapper + Waste4Classifier (probe + zero-shot blend)
│   ├── engine.py           inference engines shared by the web app and camera window
│   ├── cnn.py              CNN models (MobileNet, EfficientNet, ConvNeXt), checkpoints
│   ├── segmentation.py     classical Otsu / morphology pipeline
│   ├── features.py         hand-crafted shape / colour / texture features
│   └── plotting.py
├── scripts/
│   ├── download_*.py       datasets and model weights
│   ├── prepare_data.py     merge + de-duplicate + split  -> data/processed/manifest.csv
│   ├── embed_dataset.py    SigLIP embeddings
│   ├── train_waste4.py     4-category model (main)
│   ├── train_cnn.py        CNN baseline (10 material classes)
│   ├── train_classical.py  hand-crafted-feature baseline
│   ├── evaluate.py         score any CNN checkpoint by split / source
│   ├── realtime.py         desktop camera window
│   └── predict.py          classify image files (CNN)
├── webapp/                 server.py (stdlib HTTP + JSON API) and static/index.html
├── tests/                  pytest suite
├── data/                   raw / interim / processed (images not in git)
├── models/                 trained weights (not in git)
└── results/                metrics, confusion matrices, figures
```

## Tests

```bash
python -m pytest
```

## Limitations

* Classifies **one item at a time** inside the on-screen box; several items in one frame need a detector (planned: YOLO + tracking).
* Medical-waste accuracy is measured on web photos from Wikimedia Commons, which are cleaner than real hospital waste.
* Paper vs. tissue, and cloth vs. biodegradable fabric, are inherently ambiguous by appearance alone.
