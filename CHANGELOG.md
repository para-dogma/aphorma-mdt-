# Changelog

All notable changes to AphormA-MDT will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-06-08

### Added
- WiFi Sensing module for physical presence detection
- Edge Consensus with Sentinel distributed validation
- TON Blockchain anchoring integration
- Prometheus metrics and Grafana dashboards
- JWT refresh tokens with rotation
- Advanced rate limiting with Redis
- OWASP security middleware
- Secret rotation management- Security audit workflow (GitHub Actions)
- Comprehensive audit report

### Security
- Enhanced JWT with refresh token support
- Token revocation via Redis blacklist
- Input validation middleware (SQL injection, XSS, path traversal)
- Security headers on all responses
- Automated dependency security scanning
- Secret rotation every 90 days

### Infrastructure
- Prometheus monitoring setup
- Grafana dashboards (10 panels)
- Alert rules for critical metrics
- Docker Compose with monitoring stack

### Documentation
- AUDIT_REPORT.md with full project audit
- SECURITY.md with security policy
- Updated README.md with v2.1 features
- API documentation via Swagger

## [2.0.0] - 2026-06-06

### Added
- Production-ready architecture
- Circuit breaker pattern
- Retry with exponential backoff
- Graceful degradation
- Docker multi-stage builds
- CI/CD pipeline
- Comprehensive testing framework

### Security
- JWT authentication
- RBAC permissions
- Rate limiting
- Security headers

## [1.1.0] - 2026-06-05

### Added
- Policy Engine with YAML configuration
- Redis cache layer
- Storage layer with WAL mode
- Consensus window (30s freshness)
- Effective metrics calculation

## [1.0.0] - 2026-06-04
### Added
- Initial MVS structure
- Basic API endpoints
- Token management
- Consensus service
- Validator implementation

---

[Unreleased]
- Real TON smart contract deployment
- ESP32 hardware integration
- Performance optimization
- Scale testing (1000+ agents)
