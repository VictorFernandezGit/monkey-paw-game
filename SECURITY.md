# Security Documentation

## Overview
This document outlines the security measures implemented in the Monkey's Paw application and provides guidance for maintaining security best practices.

## Security Measures Implemented

### 1. Input Validation & Sanitization
- **Username Validation**: Length (2-50 chars), alphanumeric + hyphens/underscores only
- **Wish Validation**: Length (5-500 chars), pattern matching for malicious content
- **XSS Prevention**: Using `bleach` library to sanitize all user inputs
- **Content Filtering**: Blocks dangerous patterns like `<script>`, `javascript:`, etc.

### 2. CSRF Protection
- **Flask-WTF Integration**: Automatic CSRF token generation and validation
- **Token Management**: 1-hour token lifetime with secure cookie settings
- **Frontend Integration**: CSRF tokens included in all POST requests

### 3. Rate Limiting
- **Global Limits**: 200 requests per day, 50 per hour
- **Endpoint-Specific Limits**:
  - `/set_username`: 10 per minute
  - `/wish`: 20 per minute
  - `/generate_suggestions`: 5 per minute
  - `/leaderboard`: 30 per minute
- **Storage Backend**: Redis in production, memory in development
- **Distributed Rate Limiting**: Supports multiple server instances

### 4. Session Security
- **Secure Session Key**: Uses `secrets.token_hex(32)` for strong random generation
- **Session Timeout**: 1-hour session lifetime
- **Secure Cookies**: HTTPOnly, SameSite=Lax, Secure in production
- **Session Validation**: All protected endpoints verify session state

### 5. Security Headers
- **X-Content-Type-Options**: `nosniff` - prevents MIME type sniffing
- **X-Frame-Options**: `DENY` - prevents clickjacking
- **X-XSS-Protection**: `1; mode=block` - enables XSS filtering
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **HSTS**: `max-age=31536000; includeSubDomains` (production only)

### 6. Error Handling
- **Information Disclosure Prevention**: Generic error messages to users
- **Detailed Logging**: Server-side logging for debugging
- **Graceful Degradation**: Fallback mechanisms for service failures

### 7. Database Security
- **SQL Injection Prevention**: Using SQLAlchemy ORM
- **Parameterized Queries**: All database operations use ORM
- **Connection Security**: Environment-based database configuration

## Security Dependencies

```txt
flask-limiter    # Rate limiting
flask-wtf        # CSRF protection
bleach          # Input sanitization
redis           # Rate limiting storage (production)
```

## Environment Variables

### Required for Security
```bash
FLASK_SECRET_KEY=your-secure-secret-key-here
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=your-database-connection-string
FLASK_ENV=production  # For production security settings
```

### Optional for Enhanced Security
```bash
REDIS_URL=redis://localhost:6379  # For distributed rate limiting
```

### Security Best Practices
1. **Never commit secrets** to version control
2. **Use strong, unique secrets** for each environment
3. **Rotate secrets regularly** in production
4. **Use environment-specific configurations**
5. **Configure Redis** for production rate limiting

## Production Security Checklist

### Before Deployment
- [ ] Set `FLASK_ENV=production`
- [ ] Configure strong `FLASK_SECRET_KEY`
- [ ] Set up HTTPS/TLS certificates
- [ ] Configure secure database connections
- [ ] Set up Redis for rate limiting storage
- [ ] Set up monitoring and logging
- [ ] Review and update dependencies

### Ongoing Security
- [ ] Regular dependency updates
- [ ] Security header monitoring
- [ ] Rate limiting effectiveness review
- [ ] Session management monitoring
- [ ] Error log analysis
- [ ] API usage monitoring
- [ ] Redis health monitoring

## Security Testing

### Manual Testing
1. **XSS Testing**: Try injecting `<script>alert('xss')</script>` in inputs
2. **CSRF Testing**: Attempt requests without valid CSRF tokens
3. **Rate Limiting**: Test endpoint limits by making rapid requests
4. **Input Validation**: Test boundary conditions and malicious inputs
5. **Redis Integration**: Verify rate limiting persists across server restarts

### Automated Testing Recommendations
- Implement security-focused unit tests
- Use tools like Bandit for Python security scanning
- Regular dependency vulnerability scanning
- Automated security header validation
- Redis connectivity and rate limiting tests

## Incident Response

### Security Breach Response
1. **Immediate Actions**:
   - Disable affected functionality
   - Review logs for intrusion scope
   - Reset affected user sessions
   - Update security measures
   - Check Redis for rate limiting anomalies

2. **Investigation**:
   - Analyze attack vectors
   - Review security logs
   - Assess data exposure
   - Document incident details
   - Review rate limiting effectiveness

3. **Recovery**:
   - Implement additional security measures
   - Update security documentation
   - Notify affected users if necessary
   - Review and improve security practices
   - Adjust rate limiting thresholds if needed

## Security Contact

For security issues or questions:
- Review this documentation
- Check application logs
- Contact the development team
- Consider responsible disclosure for vulnerabilities

## Compliance Notes

This application implements security measures aligned with:
- OWASP Top 10 Web Application Security Risks
- General Data Protection Regulation (GDPR) principles
- Industry-standard web security practices

---

**Last Updated**: January 2025
**Version**: 1.1 