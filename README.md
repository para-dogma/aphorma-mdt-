# AphormA-MDT

Consensus-Aware Multidimensional Token for DePIN

## Features
- Consensus Window (30s freshness)
- Effective Metrics (health-adjusted)
- Policy Engine (YAML config)
- TON Ready

## Quick Start
pip install -r requirements.txt
uvicorn aphorma_mdt.api.main:app --host 0.0.0.0 --port 8000

## API
- GET /health
- POST /tokens/{id}
- GET /tokens/{id}
- POST /tokens/{id}/mint
- GET /consensus/{id}
- GET /policies

Docs: http://localhost:8000/docs

## Docker
docker-compose up

## Tests
python -m aphorma_mdt.tests.test_api

MIT License
