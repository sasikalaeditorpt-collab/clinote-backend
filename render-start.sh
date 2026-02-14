#!/usr/bin/env bash
set -o errexit

# Start FastAPI using uvicorn
uvicorn typing_engine_api:app --host 0.0.0.0 --port 10000