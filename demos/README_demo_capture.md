# Contract Analysis Demo Capture

Automated screen capture for the Contract Analysis Agent demo using Playwright.

## Quick Start

### 1. First Run (Manual Login Required)

```bash
cd demos
python capture_contract_demo.py --save-auth auth.json
```

This will:
- Open a browser to the M365 Copilot link
- Prompt you to log in manually
- Save your auth state to `auth.json` for future runs
- Run through all 7 demo steps
- Capture screenshots at each step

### 2. Subsequent Runs (Uses Saved Auth)

```bash
python capture_contract_demo.py --auth-state auth.json
```

### 3. Interactive Mode (Manual Control)

```bash
python capture_contract_demo.py --interactive
```

Commands in interactive mode:
- `s` - Take screenshot
- `m <message>` - Send message and capture response
- `q` - Quit

## Demo Steps Captured

| Step | Title | What It Shows |
|------|-------|---------------|
| 1 | List Contracts | Available contracts in Azure storage |
| 2 | Full Workup | Complete analysis with PDF report |
| 3 | Risk Deep Dive | Detailed risks from label perspective |
| 4 | Contract Comparison | Which deal is better for the label |
| 5 | Deal Breakers | Absolute deal breakers in artist-favorable contract |
| 6 | Clause Extraction | Financial + termination clauses only |
| 7 | Negotiation Strategy | AI recommendations for negotiation |

## Output

Screenshots are saved to `demo_captures/` by default:

```
demo_captures/
├── 20260108_123456_00_copilot_loaded.png
├── 20260108_123456_01a_before_introduction.png
├── 20260108_123456_01b_response_introduction.png
├── 20260108_123456_02a_before_full_contract.png
├── 20260108_123456_02b_response_full_contract.png
...
└── 20260108_123456_99_demo_complete.png
```

## Options

```
--headed          Run with visible browser (default)
--headless        Run without visible browser
--auth-state      Path to saved authentication state
--save-auth       Save auth state after login
--output-dir      Custom output directory
--interactive     Interactive mode with manual control
```

## Troubleshooting

### "Could not find chat input"
The M365 Copilot UI may have changed. Run in interactive mode to inspect:
```bash
python capture_contract_demo.py --interactive
```

### Authentication Issues
Delete `auth.json` and run with `--save-auth auth.json` to re-authenticate.

### Timeouts
Increase wait times in `DEMO_STEPS` in the script if responses are slow.

## Customizing the Demo

Edit `DEMO_STEPS` in `capture_contract_demo.py` to change:
- Messages sent at each step
- Wait times for responses
- Step titles and descriptions
