# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a vulnerability, please report it responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please email us at: [your-email@example.com]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
### Response Timeline

- **Initial response:** Within 48 hours
- **Status update:** Within 5 business days
- **Resolution:** Depends on severity

### Security Measures Implemented

1. **Authentication & Authorization**
   - JWT with refresh tokens
   - RBAC (Role-Based Access Control)
   - Token revocation support

2. **Rate Limiting**
   - Per-endpoint limits
   - Redis-based tracking
   - Customizable thresholds

3. **Input Validation**
   - SQL injection prevention
   - XSS protection
   - Path traversal prevention
   - Request size limits

4. **Secret Management**
   - Environment variables
   - Secret rotation support
   - No hardcoded secrets

5. **Dependencies**
   - Regular security audits
   - Automated SCA scanning
   - Version pinning

6. **Monitoring**
   - Prometheus metrics
   - Security event logging
   - Alert system

## Security Best Practices

### For Developers

1. Never commit secrets to git
2. Use `.env.example` as template
3. Rotate secrets every 90 days
4. Keep dependencies updated
5. Run `scripts/security_audit.sh` before commits

### For Production
1. Use strong JWT secrets (64+ chars)
2. Enable HTTPS/SSL
3. Configure firewall rules
4. Enable database encryption
5. Set up monitoring alerts
6. Regular backup strategy

## Security Checklist

- [ ] JWT_SECRET_KEY is strong (64+ chars)
- [ ] APP_DEBUG is false in production
- [ ] DATABASE_URL uses SSL
- [ ] Redis has password protection
- [ ] All dependencies are up to date
- [ ] Security audit passes
- [ ] Monitoring is configured
- [ ] Backup strategy is in place

## Contact

For security issues: [your-email@example.com]
For general questions: Open a GitHub issue

---

**Last updated:** June 8, 2026
**Version:** 2.1.0
