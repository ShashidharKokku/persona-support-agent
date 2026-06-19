# API Troubleshooting Guide

## 401 Unauthorized Error
A 401 error means your API key is missing, invalid, or expired.

**Steps to resolve:**
- Verify your Authorization header format: `Authorization: Bearer YOUR_API_KEY`
- Ensure the API key is active and not revoked from the developer dashboard
- Check that the key has the correct permissions/scopes enabled
- Regenerate a new key from Settings > API Keys if the issue persists

## 403 Forbidden Error
A 403 error means you don't have permission to access that resource.

**Steps to resolve:**
- Confirm your account plan includes access to the requested endpoint
- Check if IP whitelisting is enabled and your IP is allowed
- Contact your account administrator to verify role permissions

## 429 Rate Limiting Error
You are sending too many requests per minute and have hit the rate limit.

**Rate Limits by Plan:**
- Free Tier: 60 requests/minute, 1,000 requests/day
- Pro Tier: 1,000 requests/minute, 50,000 requests/day
- Enterprise: Custom limits — contact sales

**Steps to resolve:**
- Implement exponential backoff with jitter in your retry logic
- Cache repeated identical requests to reduce API calls
- Upgrade your plan if you consistently hit limits

## 500 Internal Server Error
This is a server-side error on our end.

**Steps to resolve:**
- Wait 2-3 minutes and retry the request
- Check our status page at status.ourplatform.com
- If the issue persists beyond 30 minutes, contact technical support with your request ID

## Bearer Token Authentication
To authenticate API requests, include your token in the HTTP header:

```
GET /api/v1/resource HTTP/1.1
Host: api.ourplatform.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

Token expiry: Bearer tokens expire after 24 hours. Refresh using the `/auth/refresh` endpoint.

## Webhook Configuration
To set up webhooks for event-driven integrations:
1. Navigate to Settings > Webhooks in your dashboard
2. Enter your endpoint URL (must be HTTPS)
3. Select the events you want to receive
4. Save and copy the webhook secret for payload verification
5. Verify incoming payloads using HMAC-SHA256 signature

## Database Integration Errors
If you're seeing connection errors with database integrations:
- Verify your connection string format: `postgresql://user:password@host:5432/dbname`
- Ensure your database server allows inbound connections from our IP range: 192.168.1.0/24
- Check SSL/TLS certificate validity
- Confirm firewall rules allow port 5432 (PostgreSQL) or 3306 (MySQL)
