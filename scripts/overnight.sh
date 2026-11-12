#!/usr/bin/env bash
# Full 4-category pipeline, safe to run detached:  nohup bash scripts/overnight.sh > logs/overnight.log 2>&1 &
# medical photos (resumes) -> embeddings -> train -> restart the web server with the new model.
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg
PY=venv/bin/python
echo "[$(date +%T)] start"

M=models/siglip2-base-patch16-224
[ -f $M/model.safetensors ] || $PY scripts/download_file.py \
  https://huggingface.co/google/siglip2-base-patch16-224/resolve/main/model.safetensors $M/model.safetensors

echo "[$(date +%T)] medical photos (existing files are skipped)"
$PY scripts/download_medical_commons.py > logs/download_medical.log 2>&1 || echo "medical download incomplete, continuing"

echo "[$(date +%T)] embeddings"
$PY scripts/embed_dataset.py > logs/embed.log 2>&1 || { echo "EMBED FAILED"; tail -20 logs/embed.log; exit 1; }

echo "[$(date +%T)] training"
$PY scripts/train_waste4.py > logs/train_waste4.log 2>&1 || { echo "TRAIN FAILED"; tail -20 logs/train_waste4.log; exit 1; }
tail -40 logs/train_waste4.log

echo "[$(date +%T)] restarting web server with the new model"
pkill -f "webapp/server.py" ; sleep 2
nohup $PY webapp/server.py --port 8000 > logs/server.log 2>&1 &
echo "[$(date +%T)] done: http://localhost:8000"
