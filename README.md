# AphormA-MDT v1.1

**Consensus-Aware Multidimensional Token for DePIN**

## MVS Features (Minimal Viable Set)

✅ **health_factor**: Dynamic agent health (0.0-1.0)  
✅ **consensus_window**: Time-based validity window (30s)  
✅ **effective_balance**: Balance adjusted by health  
✅ **Policy-ready**: Configurable via YAML (planned)

## Quick Start

```bash
pip install -r requirements.txt
python3 -m aphorma_mdt.api.main
```

## API Endpoints

- `POST /tokens/{agent_id}` - Create token
- `GET /tokens/{agent_id}` - Get full token state
- `GET /tokens/{agent_id}/effective-balance` - Health-adjusted balance
- `GET /tokens/{agent_id}/consensus` - Check consensus validity
- `POST /tokens/{agent_id}/mint?amount=100` - Mint tokens

## Example

```bash
curl -X POST http://localhost:8000/tokens/agent-001
curl http://localhost:8000/tokens/agent-001
```

## Status

✅ **MVS Complete** - Production Ready v1.1
