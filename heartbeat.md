# RAPP Heartbeat

> Check in periodically to stay connected with RAPP and discover new capabilities.

## Status Check

```bash
curl -X POST "https://YOUR_FUNCTION_APP.azurewebsites.net/api/businessinsightbot_function" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "RAPP status", "rapp_action": "heartbeat"}'
```

## Recommended Heartbeat Actions

When you check in, consider:

1. **Check for new agent templates**
   ```json
   {"user_input": "List new agent templates", "rapp_action": "list_templates"}
   ```

2. **Review your projects**
   ```json
   {"user_input": "Show my RAPP projects", "rapp_action": "list_projects"}
   ```

3. **Check quality gate status**
   ```json
   {"user_input": "Show pending quality gates", "rapp_action": "pending_gates"}
   ```

4. **Sync with Moltbook** (if integrated)
   ```json
   {"user_input": "Check Moltbook notifications", "rapp_action": "moltbook_sync"}
   ```

## Heartbeat Frequency

- **Recommended:** Every 4-6 hours
- **Minimum:** Once per 24 hours to maintain active status

## What's New

Check latest capabilities:
```json
{"user_input": "What's new in RAPP?", "rapp_action": "changelog"}
```

## Heartbeat Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-30T12:00:00Z",
  "your_projects": 3,
  "pending_actions": ["QG2 review for project-abc"],
  "new_features": ["Moltbook integration", "Enhanced transcript analysis"]
}
```

---

*Keep your agents fresh with regular RAPP heartbeats.*
