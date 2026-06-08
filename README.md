# AphormA-MDT

**Core Orchestration Layer for DePIN Systems**

---

## Description

AphormA-MDT is a **DePIN infrastructure core** providing:
- Intent-based coordination for distributed contributors
- Reputation and state layer for resource networks
- Proof-of-Contribution verification mechanism
- Node Attestation with anti-sybil protection
- Resource Marketplace for supply/demand matching
- QoS Metrics with SLA enforcement
- WiFi Sensing - Physical presence detection
- Edge Consensus - Distributed validation
- Blockchain Anchoring - TON integration

---

## Positioning

**AphormA-MDT is the coordination layer for DePIN:**

- For Compute DePIN: Coordinate GPU/CPU providers with verified contributions
- For Storage DePIN: Match storage supply with demand, verify uptime
- For Bandwidth DePIN: Track bandwidth contribution, enforce SLAs
- For Sensor DePIN: WiFi sensing, physical presence, data verification
- For Workflow DePIN: Orchestrate distributed task execution

---

## Features

### DePIN Core
- Proof-of-Contribution - Verify real resource contributions
- Node Attestation - Hardware fingerprinting, anti-sybil
- Resource Marketplace - Supply/demand matching with pricing
- QoS Metrics - Latency, availability, throughput monitoring
- SLA Enforcement - Automatic penalties for violations
- Reputation System - Trust scores based on performance

### Security and Reliability
- JWT Authentication with refresh tokens
- Rate Limiting (Redis-based)
- RBAC Permissions
- Circuit Breaker Pattern
- Retry with Backoff
- Graceful Degradation

### Unique Differentiators
- WiFi Sensing - Physical presence via ESP32 CSI
- Edge Consensus - Sentinel distributed validation
- Blockchain Anchoring - TON on-chain verification

---

## Architecture

```
aphorma_mdt/
├── api/                      # FastAPI REST API
│   ├── main.py
│   ├── depin_routes.py
│   └── core_routes.py
── auth/                     # JWT, Rate Limiting, RBAC
│   ├── jwt_auth.py
│   ├── rate_limiter.py
│   └── rbac.py
├── blockchain/               # TON Integration
│   └── ton_anchor.py
├── cache/                    # Redis with Circuit Breaker
│   ── redis_cache.py
├── config/                   # Settings and YAML config
│   └── settings.py
── consensus/                # Window and Validator
│   ├── consensus_service.py
│   └── validator.py
├── core/                     # Error handling, retry, metrics
│   ├── circuit_breaker.py
│   ├── retry.py
│   └── metrics.py
├── depin/                    # DePIN-specific modules
│   ├── __init__.py
│   ├── proof_of_contribution.py
│   ├── node_attestation.py
│   ├── resource_marketplace.py
│   └── qos_metrics.py
── edge/                     # Sentinel consensus
│   └── sentinel_node.py
├── policy/                   # YAML policy engine
│   └── policy_engine.py
├── sensing/                  # WiFi sensing module
│   └── wifi_sensing.py
├── storage/                  # Database models
│   └── models.py
└── tests/                    # Unit and integration tests
    └── test_api.py
```

---

## API Endpoints

### DePIN Endpoints
- POST /depin/nodes/register - Register node
- GET /depin/nodes/{id}/attestation - Node status
- GET /depin/nodes/active - Active nodes
- POST /depin/contributions/submit - Submit contribution
- POST /depin/marketplace/supply - Create supply order
- POST /depin/marketplace/demand - Create demand order
- GET /depin/marketplace/stats - Market statistics
- POST /depin/qos/record - Record QoS metrics
- GET /depin/qos/{id}/summary - QoS summary

### Core Endpoints
- GET /health - Health check
- POST /tokens/{id} - Create token
- GET /tokens/{id} - Get token state
- POST /tokens/{id}/mint - Mint tokens
- GET /consensus/{id} - Consensus status
- GET /policies - List policies

**API Docs:** http://localhost:8000/docs

---

## Installation

### Local Setup
```bash
git clone https://github.com/para-dogma/aphorma-mdt-.git
cd aphorma-mdt-
pip install -r requirements.txt
uvicorn aphorma_mdt.api.main:app --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker-compose up -d
```

---

## Monitoring

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)
- **Metrics:** http://localhost:8000/metrics

---

## Roadmap

### v2.1 Current
- [x] DePIN Core Modules
- [x] Proof-of-Contribution
- [x] Node Attestation
- [x] Resource Marketplace
- [x] QoS Metrics
- [x] Security Hardening
- [x] Monitoring Stack

### v3.0 Next
- [ ] Real TON Smart Contract
- [ ] ESP32 Hardware Integration
- [ ] Production Deployment
- [ ] Scale Testing (1000+ nodes)

---

## License

MIT License - see LICENSE file for details.

---

**Production Ready - Deploy Now!**