#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contract Analysis Agent - Demo Screen Capture Script
Uses Playwright to automate and capture screenshots of the demo flow in M365 Copilot.

Usage:
    python capture_contract_demo.py [--headed] [--auth-state auth.json]

Options:
    --headed        Run in headed mode (visible browser)
    --auth-state    Path to saved authentication state (skip login)
    --save-auth     Save authentication state after login for reuse
    --output-dir    Directory for screenshots (default: demo_captures)
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwright not installed. Install with: pip install playwright && playwright install")
    sys.exit(1)


# Demo configuration
M365_COPILOT_URL = "https://m365.cloud.microsoft/chat/entity1-d870f6cd-4aa5-4d42-9626-ab690c041429/eyJpZCI6IjhmM2ZhYTZkLWQzZjItNDExYy1iMThiLTlkYzBhZThiN2ZlYiIsInNjZW5hcmlvIjoibGF1bmNoY29waWxvdGV4dGVuc2lvbiIsInByb3BlcnRpZXMiOnsiY2xpY2tUaW1lc3RhbXAiOiJXZWQgSmFuIDA3IDIwMjYifSwidmVyc2lvbiI6MSwic291cmNlIjoib25BcHBJbnN0YWxsYXRpb24iLCJjb3JyZWxhdGlvbklkIjoiZTA2N2IxNTItMGZjYy00ZjYwLTg2NWUtZmVmZTk4NmU3YmE0IiwiaXNVcGdyYWRlIjpmYWxzZX0=?auth=2"

# Demo steps - Contract Analysis Agent walkthrough
DEMO_STEPS = [
    {
        "step": 1,
        "title": "Introduction - List Contracts",
        "message": "List all contracts available for analysis",
        "wait_time": 10,
        "description": "Display available contracts in Azure storage"
    },
    {
        "step": 2,
        "title": "Full Contract Workup",
        "message": "Work on bella_rivers_recording_agreement.pdf",
        "wait_time": 90,  # Longer wait for full analysis
        "description": "Run comprehensive analysis with risk assessment and PDF report"
    },
    {
        "step": 3,
        "title": "Risk Deep Dive",
        "message": "What are the biggest risks to the label in this contract?",
        "wait_time": 30,
        "description": "Detailed risk analysis from label perspective"
    },
    {
        "step": 4,
        "title": "Contract Comparison",
        "message": "Compare bella_rivers_recording_agreement.pdf with viper_morrison_recording_agreement.pdf. Which deal is better for the label?",
        "wait_time": 60,
        "description": "Side-by-side comparison showing which contract favors the label"
    },
    {
        "step": 5,
        "title": "Deal Breaker Analysis",
        "message": "Identify all risks in viper_morrison_recording_agreement.pdf from the label's perspective. What are the deal breakers?",
        "wait_time": 45,
        "description": "Identify absolute deal breakers in the artist-favorable contract"
    },
    {
        "step": 6,
        "title": "Clause Extraction",
        "message": "Extract only the financial and termination clauses from bella_rivers_recording_agreement.pdf",
        "wait_time": 30,
        "description": "Targeted extraction of specific clause types"
    },
    {
        "step": 7,
        "title": "Negotiation Strategy",
        "message": "Based on the Viper Morrison contract risks, what should the label push back on during negotiation?",
        "wait_time": 30,
        "description": "AI-generated negotiation recommendations"
    }
]


class DemoCapture:
    def __init__(self, output_dir: str = "demo_captures", headed: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.headed = headed
        self.browser = None
        self.page = None
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def setup(self, auth_state_path: str = None):
        """Initialize browser and navigate to M365 Copilot."""
        playwright = await async_playwright().start()

        # Browser launch options
        launch_opts = {
            "headless": not self.headed,
            "slow_mo": 100,  # Slow down for visibility
        }

        self.browser = await playwright.chromium.launch(**launch_opts)

        # Create context with optional saved auth
        # MacBook Pro 16" M1 default scaled resolution: 1792x1120
        # Subtract ~90px for menu bar + dock
        context_opts = {
            "viewport": {"width": 1792, "height": 1030},
            "record_video_dir": str(self.output_dir / "videos") if self.headed else None,
        }

        if auth_state_path and Path(auth_state_path).exists():
            context_opts["storage_state"] = auth_state_path
            print(f"Using saved auth state: {auth_state_path}")

        self.context = await self.browser.new_context(**context_opts)
        self.page = await self.context.new_page()

        return playwright

    async def navigate_to_copilot(self):
        """Navigate to M365 Copilot and wait for it to load."""
        print(f"\nNavigating to M365 Copilot...")
        print(f"URL: {M365_COPILOT_URL[:80]}...")

        await self.page.goto(M365_COPILOT_URL, wait_until="networkidle", timeout=120000)

        # Check if we need to authenticate
        if "login.microsoftonline.com" in self.page.url or "login.live.com" in self.page.url:
            print("\n" + "="*60)
            print("AUTHENTICATION REQUIRED")
            print("="*60)
            print("Please log in to your Microsoft account in the browser.")
            print("The script will continue once you're logged in.")
            print("="*60 + "\n")

            # Wait for redirect back to M365 after login
            await self.page.wait_for_url("**/m365.cloud.microsoft/**", timeout=300000)
            print("Authentication successful!")

        # Wait for Copilot chat to load
        await asyncio.sleep(5)
        await self.capture_screenshot("00_copilot_loaded", "M365 Copilot Loaded")

    async def save_auth_state(self, path: str):
        """Save authentication state for future runs."""
        await self.context.storage_state(path=path)
        print(f"Auth state saved to: {path}")

    async def capture_screenshot(self, name: str, description: str = ""):
        """Capture a screenshot with metadata."""
        filename = f"{self.timestamp}_{name}.png"
        filepath = self.output_dir / filename

        await self.page.screenshot(path=str(filepath), full_page=False)
        print(f"  Screenshot: {filename}")

        # Save metadata
        meta_file = self.output_dir / f"{self.timestamp}_{name}.txt"
        meta_file.write_text(f"Description: {description}\nTimestamp: {datetime.now().isoformat()}\n")

        return filepath

    async def send_message(self, message: str):
        """Send a message in the Copilot chat."""
        # M365 Copilot specific selectors (based on actual DOM inspection)
        # Primary: id="m365-chat-editor-target-element" with contenteditable
        input_selectors = [
            '#m365-chat-editor-target-element',  # Primary M365 Copilot input
            'span[data-lexical-editor="true"]',  # Lexical editor span
            '[aria-label="Message Copilot"][contenteditable="true"]',
            'span[role="combobox"][contenteditable="true"]',
            '[contenteditable="true"][aria-label*="Message"]',
            'div[contenteditable="true"]',
            'span[contenteditable="true"]',
        ]

        input_element = None
        for selector in input_selectors:
            try:
                input_element = await self.page.wait_for_selector(selector, timeout=5000)
                if input_element:
                    print(f"  Found input with selector: {selector}")
                    break
            except:
                continue

        if not input_element:
            print("  WARNING: Could not find chat input. Taking screenshot for manual inspection.")
            await self.capture_screenshot("error_no_input", "Could not find chat input")
            return False

        # Click to focus and clear any existing content
        await input_element.click()
        await asyncio.sleep(0.3)

        # For contenteditable, we need to type character by character or use keyboard
        # First select all and delete (use Meta for Mac, Control for others)
        import platform
        select_all = "Meta+a" if platform.system() == "Darwin" else "Control+a"
        await self.page.keyboard.press(select_all)
        await self.page.keyboard.press("Backspace")

        # Type the message
        await self.page.keyboard.type(message, delay=10)

        # Capture before sending
        await asyncio.sleep(0.5)

        # Send message - M365 Copilot uses aria-label="Send" button
        send_selectors = [
            'button[aria-label="Send"]',  # Primary M365 send button
            '.fai-SendButton',  # Class-based selector
            'button[type="submit"][aria-label="Send"]',
            'button[type="submit"]',
        ]

        sent = False
        for selector in send_selectors:
            try:
                send_btn = await self.page.wait_for_selector(selector, timeout=3000)
                if send_btn:
                    # Check if button is enabled
                    is_disabled = await send_btn.get_attribute("disabled")
                    if is_disabled:
                        print("  Send button disabled, waiting...")
                        await asyncio.sleep(1)
                    await send_btn.click()
                    print(f"  Clicked send button: {selector}")
                    sent = True
                    break
            except Exception as e:
                continue

        if not sent:
            # Fallback: press Enter
            print("  Fallback: pressing Enter to send")
            await input_element.press("Enter")

        return True

    async def count_feedback_buttons(self) -> int:
        """Count the number of 'Give feedback' buttons on the page."""
        try:
            # Look for feedback buttons by text content
            buttons = await self.page.query_selector_all('button')
            count = 0
            for btn in buttons:
                try:
                    text = await btn.inner_text()
                    if 'Give feedback' in text or 'feedback' in text.lower():
                        count += 1
                except:
                    pass
            return count
        except:
            return 0

    async def wait_for_response(self, timeout_seconds: int = 60):
        """Wait for the AI response to complete."""
        print(f"  Waiting up to {timeout_seconds}s for response...")

        # Wait for response to start generating
        await asyncio.sleep(5)

        # Poll for completion - look for signs that response is done
        start_time = asyncio.get_event_loop().time()
        check_interval = 3  # Check every 3 seconds

        while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
            elapsed = int(asyncio.get_event_loop().time() - start_time)

            # Check for "Stop generating" button - if present, still generating
            try:
                stop_btn = await self.page.query_selector('button:has-text("Stop generating")')
                if stop_btn:
                    if elapsed % 10 == 0:
                        print(f"  Still generating... ({elapsed}s elapsed)")
                    await asyncio.sleep(check_interval)
                    continue
            except:
                pass

            # Check for "Regenerate" button - if present, response is complete
            try:
                regen_btn = await self.page.query_selector('button:has-text("Regenerate")')
                if regen_btn:
                    print(f"  Response complete! (Regenerate button found after {elapsed}s)")
                    await asyncio.sleep(3)  # Extra wait for full rendering
                    return
            except:
                pass

            # Also check for "Give feedback" or feedback buttons
            try:
                feedback_btns = await self.page.query_selector_all('button')
                for btn in feedback_btns:
                    text = await btn.inner_text()
                    if 'feedback' in text.lower():
                        print(f"  Response complete! (Feedback button found after {elapsed}s)")
                        await asyncio.sleep(3)
                        return
            except:
                pass

            if elapsed % 10 == 0 and elapsed > 0:
                print(f"  Still waiting... ({elapsed}s elapsed)")

            await asyncio.sleep(check_interval)

        print(f"  Response timeout after {timeout_seconds}s")

        # Final wait for any remaining rendering
        await asyncio.sleep(5)

        # Scroll to show latest content
        try:
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        except:
            pass

    async def run_demo_step(self, step: dict):
        """Execute a single demo step with screenshot capture."""
        step_num = step["step"]
        title = step["title"]
        message = step["message"]
        wait_time = step["wait_time"]
        description = step["description"]

        print(f"\n{'='*60}")
        print(f"STEP {step_num}: {title}")
        print(f"{'='*60}")
        print(f"Message: {message[:80]}{'...' if len(message) > 80 else ''}")
        print(f"Description: {description}")

        # Capture before sending
        await self.capture_screenshot(
            f"{step_num:02d}a_before_{title.lower().replace(' ', '_')[:20]}",
            f"Before: {title}"
        )

        # Send message
        success = await self.send_message(message)
        if not success:
            print(f"  ERROR: Failed to send message for step {step_num}")
            return

        # Wait for response
        await self.wait_for_response(wait_time)

        # Capture after response
        await self.capture_screenshot(
            f"{step_num:02d}b_response_{title.lower().replace(' ', '_')[:20]}",
            f"Response: {title}"
        )

        # Scroll and capture full response if needed
        try:
            # Scroll up to see full response
            await self.page.evaluate("document.querySelector('.chat-messages')?.scrollTo(0, 0)")
            await asyncio.sleep(0.5)
            await self.capture_screenshot(
                f"{step_num:02d}c_full_{title.lower().replace(' ', '_')[:20]}",
                f"Full Response: {title}"
            )
        except:
            pass

        print(f"  Step {step_num} complete!")

    async def run_full_demo(self, save_auth: str = None):
        """Run the complete demo sequence."""
        print("\n" + "="*60)
        print("CONTRACT ANALYSIS AGENT - DEMO CAPTURE")
        print("="*60)
        print(f"Output directory: {self.output_dir}")
        print(f"Total steps: {len(DEMO_STEPS)}")
        print("="*60)

        # Navigate to Copilot
        await self.navigate_to_copilot()

        # Save auth if requested
        if save_auth:
            await self.save_auth_state(save_auth)

        # Run each demo step
        for step in DEMO_STEPS:
            try:
                await self.run_demo_step(step)
            except Exception as e:
                print(f"  ERROR in step {step['step']}: {e}")
                await self.capture_screenshot(
                    f"{step['step']:02d}_error",
                    f"Error: {str(e)[:100]}"
                )

        # Final summary screenshot
        await self.capture_screenshot("99_demo_complete", "Demo Complete")

        print("\n" + "="*60)
        print("DEMO CAPTURE COMPLETE")
        print("="*60)
        print(f"Screenshots saved to: {self.output_dir}")
        print(f"Total screenshots: {len(list(self.output_dir.glob('*.png')))}")
        print("="*60)

    async def cleanup(self):
        """Clean up browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


async def interactive_mode():
    """Run in interactive mode - manual control with screenshot hotkeys."""
    print("\n" + "="*60)
    print("INTERACTIVE MODE")
    print("="*60)
    print("Browser will open. You can manually navigate and the script")
    print("will capture screenshots on command.")
    print("")
    print("Commands (type in terminal):")
    print("  s - Take screenshot")
    print("  q - Quit")
    print("="*60)

    demo = DemoCapture(headed=True)
    playwright = await demo.setup()

    await demo.navigate_to_copilot()

    screenshot_num = 1
    while True:
        cmd = input("\nCommand (s=screenshot, q=quit): ").strip().lower()
        if cmd == 'q':
            break
        elif cmd == 's':
            name = input("Screenshot name (or Enter for auto): ").strip()
            if not name:
                name = f"manual_{screenshot_num:03d}"
            await demo.capture_screenshot(name, "Manual capture")
            screenshot_num += 1
        elif cmd.startswith('m '):
            # Send message
            message = cmd[2:]
            await demo.send_message(message)
            await demo.wait_for_response(30)
            await demo.capture_screenshot(f"msg_{screenshot_num:03d}", message[:50])
            screenshot_num += 1

    await demo.cleanup()


async def main():
    parser = argparse.ArgumentParser(description="Capture Contract Analysis Agent demo screenshots")
    parser.add_argument("--headed", action="store_true", default=True, help="Run in headed mode (visible browser)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--auth-state", type=str, help="Path to saved authentication state")
    parser.add_argument("--save-auth", type=str, help="Save authentication state to this path")
    parser.add_argument("--output-dir", type=str, default="demo_captures", help="Output directory for screenshots")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")

    args = parser.parse_args()

    if args.interactive:
        await interactive_mode()
        return

    headed = not args.headless

    demo = DemoCapture(output_dir=args.output_dir, headed=headed)

    try:
        playwright = await demo.setup(auth_state_path=args.auth_state)
        await demo.run_full_demo(save_auth=args.save_auth)
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        raise
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
