"""Prometheus metrics integration for AphormA-MDT"""
from prometheus_client import Counter, Histogram, Gauge, Summary
import time

# HTTP metrics
HTTP_REQUESTS = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

HTTP_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
)

# Token metrics
TOKENS_ACTIVE = Gauge(
    'tokens_active_total',
    'Total active tokens'
)

TOKENS_MINTED = Counter(
    'tokens_minted_total',
    'Total tokens minted'
)

# Circuit breaker metrics
CIRCUIT_BREAKER_STATE = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service']
)

CIRCUIT_BREAKER_TRIPS = Counter(
    'circuit_breaker_trips_total',
    'Total circuit breaker trips',
    ['service']
)

# Cache metrics
CACHE_HITS = Counter(
    'cache_hits_total',    'Total cache hits',
    ['cache_name']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_name']
)

CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate',
    ['cache_name']
)

# WiFi Sensing metrics
WIFI_SENSING_DETECTIONS = Counter(
    'wifi_sensing_detections_total',
    'Total WiFi sensing detections',
    ['agent_id']
)

WIFI_SENSING_PRESENCE = Gauge(
    'wifi_sensing_presence_confidence',
    'WiFi sensing presence confidence',
    ['agent_id']
)

# Edge Consensus metrics
EDGE_CONSENSUS_VALIDATIONS = Counter(
    'edge_consensus_validations_total',
    'Total edge consensus validations'
)

EDGE_CONSENSUS_CONFIDENCE = Histogram(
    'edge_consensus_confidence',
    'Edge consensus confidence distribution'
)

# Blockchain metrics
BLOCKCHAIN_ANCHORS = Counter(
    'blockchain_anchors_total',
    'Total blockchain anchors'
)

BLOCKCHAIN_ANCHOR_LATENCY = Histogram(
    'blockchain_anchor_duration_seconds',
    'Blockchain anchor latency'
)
# Health metrics
SERVICE_HEALTH = Gauge(
    'service_health',
    'Service health status (1=healthy, 0=unhealthy)'
)

# Middleware for FastAPI
def metrics_middleware(request, call_next):
    """FastAPI middleware to collect metrics"""
    start_time = time.time()
    response = call_next(request)
    duration = time.time() - start_time
    
    HTTP_REQUESTS.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    HTTP_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
