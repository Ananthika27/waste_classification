#!/usr/bin/env bash
# Finish the 4-category system: download -> embed -> train -> camera.
set -e
cd "$(dirname "$0")"
source venv/bin/activate

M=models/siglip2-base-patch16-224
echo "1/4 SigLIP model (1.5 GB, resumes if interrupted)"
[ -f $M/model.safetensors ] || python scripts/download_file.py \
  https://huggingface.co/google/siglip2-base-patch16-224/resolve/main/model.safetensors $M/model.safetensors

echo "2/4 Medical photos from Wikimedia Commons"
[ -f data/raw/medical_commons/attribution.csv ] || python scripts/download_medical_commons.py

echo "3/4 Embeddings + training"
python scripts/embed_dataset.py
python scripts/train_waste4.py

echo "4/4 Web app: open http://localhost:8000"
python webapp/server.py
