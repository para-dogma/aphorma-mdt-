"""
Prometheus Metrics for AphormA-MDT
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response
import time

router = APIRouter()

# Metrics definitions
REQUEST_COUNT = Counter('aphorma_mdt_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('aphorma_mdt_request_latency_seconds', 'Request latency', ['endpoint'])
ACTIVE_CONNECTIONS = Gauge('aphorma_mdt_active_connections', 'Active connections')
TOKENS_CREATED = Counter('aphorma_mdt_tokens_created_total', 'Total tokens created')
MINT_OPERATIONS = Counter('aphorma_mdt_mint_operations_total', 'Total mint operations')
HEALTH_FACTOR_AVG = Gauge('aphorma_mdt_health_factor_avg', 'Average health factor')

@router.get('/metrics')
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

def record_request(method: str, endpoint: str, status: int, latency: float):
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)

def record_token_created():
    TOKENS_CREATED.inc()

def record_mint_operation():
    MINT_OPERATIONS.inc()
