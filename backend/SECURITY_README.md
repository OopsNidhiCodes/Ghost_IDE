# GhostIDE Security Implementation

This document describes the comprehensive security measures implemented in GhostIDE to protect against various threats and ensure safe code execution.

## 🔒 Security Features Overview

### 1. Input Validation and Sanitization

**Location**: `app/middleware/security.py`

- **Code Validation**: Comprehensive validation of user-submitted code to prevent dangerous operations
- **Pattern Detection**: Regex-based detection of dangerous imports, functions, and system calls
- **Language-Specific Rules**: Different validation rules for Python, JavaScript, Java, and C/C++
- **Input Sanitization**: Removal of potentially dangerous characters and control sequences
- **Size Limits**: Enforcement of maximum code size (50KB) and input length limits

**Dangerous Patterns Detected**:
- System imports (`os`, `sys`, `subprocess`, `socket`)
- File operations (`open`, `file`, `input`)
- Network operations (`urllib`, `requests`, `socket`)
- Process operations (`fork`, `spawn`, `system`)
- Dangerous functions (`exec`, `eval`, `compile`)

### 2. Rate Limiting

**Location**: `app/middleware/security.py`

- **Sliding Window Algorithm**: Tracks requests per minute with automatic cleanup
- **Endpoint-Specific Limits**:
  - Code Execution: 10 requests/minute
  - AI Requests: 20 requests/minute
  - General API: 100 requests/minute
- **IP Blocking**: Automatic 15-minute blocks for rate limit violations
- **Rate Limit Headers**: Client-side rate limit information in response headers

### 3. Authentication and Session Management

**Location**: `app/middleware/auth.py`

- **JWT Tokens**: Secure token-based authentication with IP validation
- **Session Tracking**: Comprehensive session management with timeout handling
- **IP Validation**: Tokens are tied to specific IP addresses
- **Session Cleanup**: Automatic cleanup of expired sessions
- **Activity Tracking**: Request counting and last activity timestamps

### 4. Docker Container Security

**Location**: `app/services/code_execution.py`

Enhanced Docker security configuration:
- **Network Isolation**: `network_disabled=True` - No network access
- **Read-Only Filesystem**: `read_only=True` - Prevents file system modifications
- **Non-Root User**: `user='1000:1000'` - Runs as unprivileged user
- **Capability Dropping**: `cap_drop=['ALL']` - Removes all Linux capabilities
- **Security Options**: `no-new-privileges:true` - Prevents privilege escalation
- **Resource Limits**:
  - Memory: 128MB (256MB for Java/C++)
  - CPU: 50% of one core
  - Process limit: 50 processes
  - File descriptors: 100
  - File size: 10MB maximum
- **Temporary Filesystem**: Secure tmpfs mounts with `noexec`, `nosuid`, `nodev`
- **Working Directory**: Restricted to `/tmp`
- **Environment Variables**: Minimal, secure environment setup

### 5. Security Monitoring

**Location**: `app/services/security_monitor.py`

- **Event Logging**: Comprehensive logging of all security-related events
- **Threat Detection**: Automatic detection of suspicious patterns
- **IP Threat Scoring**: Dynamic threat scoring (0-100) based on activity
- **Alert System**: Automated alerts for security violations
- **Pattern Analysis**: Detection of rapid-fire requests, validation failures, session anomalies

**Monitored Events**:
- Code execution requests
- Input validation failures
- Rate limit violations
- Session mismatches
- Suspicious activity patterns
- AI request patterns

### 6. Security Headers

**Location**: `app/middleware/security.py`

All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'`

### 7. Security Dashboard

**Location**: `app/api/endpoints/security.py`

Administrative endpoints for security monitoring:
- `/api/v1/security/summary` - Security overview and statistics
- `/api/v1/security/ip/{ip}` - IP threat information
- `/api/v1/security/block-ip/{ip}` - Manual IP blocking
- `/api/v1/security/unblock-ip/{ip}` - Manual IP unblocking
- `/api/v1/security/alerts` - Recent security alerts
- `/api/v1/security/health` - Security system health check

## 🛡️ Security Configuration

### Docker Security Configuration

**File**: `docker-security.yml`

Defines security profiles for different language containers with:
- Resource limits per language
- Security options and capabilities
- Environment restrictions
- Monitoring thresholds
- Dangerous pattern definitions

### Rate Limiting Configuration

```python
# Rate limits (requests per minute)
'code_execution': 10,
'ai_requests': 20,
'api_requests': 100
```

### Threat Detection Thresholds

```python
'failed_validations_per_minute': 5,
'rate_limit_violations_per_hour': 3,
'suspicious_patterns_per_hour': 10,
'different_sessions_per_ip': 20,
'code_execution_failures_per_minute': 8
```

## 🔍 Security Testing

### Test Files

- `tests/test_security.py` - Comprehensive security test suite
- `test_security_simple.py` - Simple validation tests

### Running Security Tests

```bash
# Run comprehensive tests
python -m pytest backend/tests/test_security.py -v

# Run simple validation tests
cd backend
python test_security_simple.py
```

### Test Coverage

- Input validation for all supported languages
- Rate limiting enforcement
- Session management
- JWT token validation
- Docker security configuration
- Security monitoring and alerting

## 🚨 Security Alerts and Monitoring

### Alert Types

1. **RAPID_EVENTS** - Too many requests in short time
2. **MULTIPLE_VALIDATION_FAILURES** - Repeated input validation failures
3. **SESSION_ANOMALIES** - Session hijacking attempts
4. **CODE_EXECUTION_ABUSE** - Excessive code execution requests

### Threat Levels

- **LOW** - Normal security events
- **MEDIUM** - Suspicious activity requiring monitoring
- **HIGH** - Potential security threats requiring action
- **CRITICAL** - Active attacks requiring immediate blocking

### Automatic Responses

- **Rate Limiting**: Automatic temporary blocks for excessive requests
- **IP Blocking**: Automatic blocking for critical threats
- **Session Invalidation**: Automatic cleanup of suspicious sessions
- **Alert Generation**: Real-time alerts for security teams

## 🔧 Security Maintenance

### Regular Tasks

1. **Log Review**: Regular review of security logs and alerts
2. **Pattern Updates**: Update dangerous pattern detection rules
3. **Threshold Tuning**: Adjust rate limits and threat thresholds
4. **Container Updates**: Keep Docker images updated with security patches
5. **Dependency Updates**: Regular updates of security-related dependencies

### Security Monitoring

- Monitor `/api/v1/security/summary` for overall security status
- Review `/api/v1/security/alerts` for recent security events
- Check high-threat IPs and consider additional restrictions
- Monitor resource usage and adjust limits as needed

## 🎯 Security Best Practices

### For Developers

1. **Input Validation**: Always validate and sanitize user inputs
2. **Rate Limiting**: Respect rate limits and implement client-side throttling
3. **Session Management**: Properly handle session tokens and expiration
4. **Error Handling**: Don't expose sensitive information in error messages

### For Administrators

1. **Regular Monitoring**: Check security dashboard regularly
2. **Log Analysis**: Review security logs for patterns and trends
3. **Incident Response**: Have procedures for handling security alerts
4. **Updates**: Keep all security components updated

### For Users

1. **Safe Code**: Write code that follows security guidelines
2. **Rate Awareness**: Be aware of rate limits to avoid blocks
3. **Session Security**: Don't share session tokens or credentials
4. **Reporting**: Report suspicious activity or security concerns

## 📊 Security Metrics

The security system tracks various metrics:

- Total security events per hour/day
- Rate limit violations
- Blocked IP addresses
- High-threat IP addresses
- Alert frequency by type
- Top threat IPs with scores

These metrics help identify trends and improve security measures over time.

## 🔮 Future Security Enhancements

Planned security improvements:

1. **Machine Learning**: AI-based threat detection
2. **Behavioral Analysis**: User behavior pattern analysis
3. **Advanced Sandboxing**: Enhanced container isolation
4. **Threat Intelligence**: Integration with threat intelligence feeds
5. **Audit Logging**: Comprehensive audit trail for compliance
6. **Multi-Factor Authentication**: Enhanced authentication options

---

**Remember**: Security is an ongoing process. Regular review and updates of these measures are essential to maintain a secure environment for GhostIDE users. 👻🔒