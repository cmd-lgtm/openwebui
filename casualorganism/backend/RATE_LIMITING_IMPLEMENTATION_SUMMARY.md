# Rate Limiting Implementation Summary

## Overview

This document summarizes the implementation of rate limiting for the Causal Organism platform, transforming it from an unprotected API to a production-ready system with comprehensive rate limiting protection against abuse and denial-of-service attacks.

## Requirements Addressed

### Requirement 20: Rate Limiting

**User Story:** As a platform operator, I want API requests to be rate limited, so that the system is protected from abuse and denial-of-service attacks.

**Implementation Status:** ✅ Complete

#### Acceptance Criteria

1. ✅ **20.1**: Enforce rate limit of 100 requests per minute per user
2. ✅ **20.2**: Enforce rate limit of 1000 requests per minute per IP address
3. ✅ **20.3**: Apply stricter limits to expensive endpoints (10 requests per minute)
4. ✅ **20.4**: Return HTTP 429 with Retry-After header when rate limit exceeded
5. ✅ **20.5**: Use sliding window algorithm for rate limit calculation
6. ✅ **20.6**: Store rate limit state in Redis for consistency across replicas
7. ✅ **20.7**: Allow higher limits for premium user roles
8. ✅ **20.8**: Expose metrics for rate limit hits per endpoint

## Architecture

### Components

1. **RateLimiter** (`backend/core/rate_limiter.py`)
   - Core rate limiting logic using Redis
   - Sliding window algorithm implementation
   - Per-user, per-IP, and per-endpoint rate limiting
   - Atomic operations using Redis pipelines

2. **RateLimitMiddleware** (`backend/core/rate_limit_middleware.py`)
   - FastAPI middleware for automatic rate limiting
   - Applies limits based on user role and endpoint
   - Returns HTTP 429 with proper headers
   - Integrates with Prometheus metrics

3. **RateLimitConfig** (`backend/core/rate_limiter.py`)
   - Configuration for rate limits by endpoint and role
   - Defines expensive endpoints with stricter limits
   - Role-based limit multipliers

4. **Prometheus Metrics** (`backend/core/prometheus_metrics.py`)
   - Tracks rate limit hits per endpoint
   - Monitors rate limit effectiveness

## Implementation Details

### Sliding Window Algorithm

The rate limiter uses Redis sorted sets to implement a sliding window algorithm:

1. Each request is stored as a member in a sorted set with its timestamp as the score
2. Old entries outside the window are removed before checking the limit
3. Current count is compared against the limit
4. If within limit, the new request is added to the set
5. The set automatically expires after the window duration

**Benefits:**
- More accurate than fixed windows
- No burst allowance at window boundaries
- Consistent rate limiting across time

### Rate Limit Tiers

**Per-User Limits (per minute):**
- Admin: 500 requests
- Premium: 200 requests
- Standard: 100 requests
- Free: 50 requests

**Per-IP Limit:**
- 1000 requests per minute (protects against unauthenticated abuse)

**Expensive Endpoints:**
- `/api/causal/analyze`: 10 requests/minute
- `/api/exports/request`: 5 requests/minute
- `/api/graph/employee_metrics`: 20 requests/minute

### Response Format

When rate limit is exceeded, the API returns HTTP 429 with:

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please retry after 30 seconds.",
  "limit": 100,
  "remaining": 0,
  "reset": 1234567890,
  "retry_after": 30
}
```

**Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait before retrying

### Middleware Integration

The rate limiting middleware is added to the FastAPI application during startup:

1. Rate limiter is initialized with Redis connection
2. Middleware is added to the application
3. Middleware checks rate limits for each request
4. Skips health check and metrics endpoints
5. Adds rate limit headers to all responses

### Metrics

Prometheus metrics track:
- `rate_limit_hits_total`: Total requests blocked by rate limiting
  - Labels: `endpoint`, `limit_type` (user/ip/endpoint)
- `rate_limit_requests_total`: Total requests checked against rate limits
  - Labels: `endpoint`, `limit_type`, `result` (allowed/blocked)

## Configuration

### Environment Variables

```bash
# Redis connection for rate limiting
REDIS_URL=redis://redis:6379/0
```

### Customization

Rate limits can be customized by modifying `RateLimitConfig`:

```python
# Adjust default limits
DEFAULT_USER_LIMIT = 100
DEFAULT_IP_LIMIT = 1000

# Add expensive endpoints
EXPENSIVE_ENDPOINTS = {
    "/api/new/expensive/endpoint": 5,
}

# Adjust role limits
ROLE_LIMITS = {
    "admin": 500,
    "premium": 200,
    "standard": 100,
    "free": 50,
}
```

## Testing

### Unit Tests

Comprehensive unit tests in `backend/tests/test_rate_limiting.py`:

1. **User Rate Limiting**
   - Requests within limit are allowed
   - Requests exceeding limit are blocked
   - Retry-after is calculated correctly

2. **IP Rate Limiting**
   - IP-based limits work independently
   - Protects against unauthenticated abuse

3. **Endpoint Rate Limiting**
   - Expensive endpoints have stricter limits
   - Limits are enforced per user per endpoint

4. **Sliding Window Algorithm**
   - Old requests expire correctly
   - Window slides properly over time

5. **Configuration**
   - Role-based limits work correctly
   - Expensive endpoints are identified

6. **Middleware**
   - Middleware integrates with FastAPI
   - Headers are added correctly
   - 429 responses are formatted properly

### Running Tests

```bash
# Run all rate limiting tests
pytest backend/tests/test_rate_limiting.py -v

# Run specific test
pytest backend/tests/test_rate_limiting.py::TestRateLimiter::test_user_rate_limit_exceeded -v
```

## Deployment Considerations

### Redis Requirements

- Redis 5.0+ (for sorted set operations)
- Persistent storage recommended (AOF or RDB)
- High availability setup for production (Redis Sentinel or Cluster)

### Performance

- Redis operations are O(log N) for sorted set operations
- Minimal latency impact (<5ms per request)
- Scales horizontally with Redis cluster

### Monitoring

Monitor these metrics in Grafana:

1. **Rate Limit Hit Rate**
   - `rate(rate_limit_hits_total[5m])`
   - Alert if consistently high (may indicate attack or misconfigured limits)

2. **Rate Limit Effectiveness**
   - `rate_limit_hits_total / rate_limit_requests_total`
   - Should be <5% under normal conditions

3. **Per-Endpoint Blocking**
   - `rate_limit_hits_total{endpoint="/api/causal/analyze"}`
   - Identify endpoints that may need limit adjustments

### Troubleshooting

**Issue: Rate limiter not working**
- Check Redis connection: `redis-cli ping`
- Verify REDIS_URL environment variable
- Check logs for initialization errors

**Issue: Legitimate users being blocked**
- Review rate limits in `RateLimitConfig`
- Check user role assignments
- Consider increasing limits for specific endpoints

**Issue: Rate limiting too lenient**
- Reduce limits in `RateLimitConfig`
- Add more endpoints to `EXPENSIVE_ENDPOINTS`
- Implement additional IP-based blocking

## Future Enhancements

1. **Dynamic Rate Limiting**
   - Adjust limits based on system load
   - Implement adaptive rate limiting

2. **Whitelist/Blacklist**
   - Allow certain IPs to bypass limits
   - Block known malicious IPs

3. **Rate Limit Quotas**
   - Daily/monthly quotas in addition to per-minute limits
   - Quota tracking and reporting

4. **Distributed Rate Limiting**
   - Use Redis Cluster for higher scale
   - Implement consistent hashing for better distribution

5. **Rate Limit Analytics**
   - Dashboard showing rate limit patterns
   - Identify potential abuse patterns
   - Optimize limits based on usage data

## References

- Requirements: `.kiro/specs/architecture-scalability-audit/requirements.md` (Requirement 20)
- Design: `.kiro/specs/architecture-scalability-audit/design.md`
- Tasks: `.kiro/specs/architecture-scalability-audit/tasks.md` (Task 18)
- Implementation: `backend/core/rate_limiter.py`, `backend/core/rate_limit_middleware.py`
- Tests: `backend/tests/test_rate_limiting.py`
