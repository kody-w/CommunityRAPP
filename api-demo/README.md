# RAPP API Demo Endpoints

This folder contains static JSON responses that simulate the RAPP API. Apps can fetch these directly from GitHub raw URLs to demonstrate functionality without requiring a live backend.

## Demo Endpoints

| Endpoint | Raw URL | Description |
|----------|---------|-------------|
| Hello | [hello.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/hello.json) | Basic greeting response |
| Agents List | [agents-list.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/agents-list.json) | Available agents |
| Capabilities | [capabilities.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/capabilities.json) | API capabilities overview |
| Sample Chat | [sample-chat.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/sample-chat.json) | Example conversation |
| **CRM** | [crm.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/responses/crm.json) | Sales pipeline demo |

## Scenario: CRM (Sales Pipeline)

Full CRM simulation with multiple endpoints for realistic demos:

| Action | Endpoint | Description |
|--------|----------|-------------|
| Overview | [overview.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/scenarios/crm/overview.json) | Pipeline dashboard |
| List Deals | [list.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/scenarios/crm/list.json) | All deals grouped by stage |
| Deal Detail | [detail.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/scenarios/crm/detail.json) | Single deal view |
| Update Deal | [update.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/scenarios/crm/update.json) | After updating a deal |
| Create Deal | [create.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/scenarios/crm/create.json) | After creating a deal |
| Search | [search.json](https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/scenarios/crm/search.json) | Search results |

**Usage in apps:**
```javascript
// Simulate user viewing pipeline
const overview = await fetch('https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/scenarios/crm/overview.json');

// Simulate user clicking a deal
const detail = await fetch('https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/scenarios/crm/detail.json');

// Simulate user updating a deal
const updated = await fetch('https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/api-demo/scenarios/crm/update.json');
```

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
