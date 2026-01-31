# RAPP API Demo Endpoints

This folder contains static JSON responses that simulate the RAPP API. Apps can fetch these directly from GitHub raw URLs to demonstrate functionality without requiring a live backend.

## Demo Endpoints

| Endpoint | Raw URL | Description |
|----------|---------|-------------|
| Hello | [hello.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/hello.json) | Basic greeting response |
| Agents List | [agents-list.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/agents-list.json) | Available agents |
| Capabilities | [capabilities.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/capabilities.json) | API capabilities overview |
| Sample Chat | [sample-chat.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/sample-chat.json) | Example conversation |

## Testing

Click any link above to test - if you see JSON, it works!

Or use curl:
```bash
curl https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/hello.json
```

Or fetch in JavaScript:
```javascript
const response = await fetch('https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/hello.json');
const data = await response.json();
console.log(data.assistant_response);
```

## Switching to Live API

To use a real RAPP API instead of demo mode:

1. **Deploy your own RAPP backend** - See [openrapp](https://github.com/kody-w/openrapp) for Azure Functions deployment
2. **Configure the app** - Open Settings and enter your API endpoint:
   ```
   https://YOUR-FUNCTION-APP.azurewebsites.net/api/businessinsightbot_function
   ```
3. **Add your function key** if authentication is required

## Response Format

All RAPP API responses follow this structure:

```json
{
  "assistant_response": "Formatted markdown response for display",
  "voice_response": "Shorter response optimized for text-to-speech",
  "agent_logs": "Debug info about which agents were called",
  "user_guid": "User identifier for memory persistence",
  "mode": "demo | live"
}
```

## Adding New Demo Responses

1. Create a JSON file in `responses/`
2. Follow the response format above
3. Include `"mode": "demo"` to indicate it's simulated
4. Add the raw URL to this README
