#!/usr/bin/env python3
"""
Contract Analysis Agent Demo - Playwright Controller

Run the demo with a simple keyboard interface while filming.
Press number keys (1-7) to send demo steps, or 'q' to quit.
"""

import asyncio
import sys
from playwright.async_api import async_playwright, Page

DEMO_STEPS = [
    ("List Contracts", "List all contracts available for analysis"),
    ("Full Workup", "Work on bella_rivers_recording_agreement.pdf"),
    ("Risk Deep Dive", "What are the biggest risks to the label in this contract?"),
    ("Compare Contracts", "Compare bella_rivers_recording_agreement.pdf with viper_morrison_recording_agreement.pdf"),
    ("Deal Breakers", "Identify all risks in viper_morrison_recording_agreement.pdf from the label's perspective. Flag any potential deal breakers."),
    ("Clause Extraction", "Extract only the financial and termination clauses from bella_rivers_recording_agreement.pdf"),
    ("Negotiation Strategy", "Based on the Viper Morrison contract risks, what should the label push back on during negotiations?"),
]


async def send_message(page: Page, message: str) -> bool:
    """Type and send a message in M365 Copilot chat."""
    try:
        # Find the chat input - try multiple selectors
        input_selectors = [
            '#m365-chat-editor-target-element',
            '[aria-label="Message Copilot"]',
            '[data-lexical-editor="true"]',
        ]

        chat_input = None
        for selector in input_selectors:
            try:
                chat_input = await page.wait_for_selector(selector, timeout=2000)
                if chat_input:
                    break
            except:
                continue

        if not chat_input:
            print("  ERROR: Could not find chat input")
            return False

        # Click to focus
        await chat_input.click()
        await asyncio.sleep(0.1)

        # Clear any existing text
        await page.keyboard.press("Meta+a")  # Select all (Cmd+A on Mac)
        await asyncio.sleep(0.05)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.1)

        # Type the message
        await page.keyboard.type(message, delay=10)  # Fast but visible typing
        await asyncio.sleep(0.2)

        # Find and click send button
        send_button = await page.query_selector('button[aria-label="Send"]')
        if send_button:
            is_disabled = await send_button.get_attribute("disabled")
            if not is_disabled:
                await send_button.click()
                return True

        # Fallback: press Enter
        await page.keyboard.press("Enter")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def print_menu():
    """Print the demo step menu."""
    print("\n" + "=" * 50)
    print("CONTRACT ANALYSIS DEMO CONTROLLER")
    print("=" * 50)
    for i, (title, _) in enumerate(DEMO_STEPS, 1):
        print(f"  [{i}] {title}")
    print("  [c] Custom message")
    print("  [q] Quit")
    print("-" * 50)


async def run_demo():
    """Main demo runner."""
    print("\nStarting Contract Analysis Demo...")
    print("Browser will open - please log in to M365 Copilot if needed.\n")

    async with async_playwright() as p:
        # Launch browser - use headed mode so user can see it
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )

        # Create context with viewport
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            no_viewport=True  # Allow window resizing
        )

        page = await context.new_page()

        # Navigate to M365 Copilot
        print("Opening M365 Copilot...")
        await page.goto("https://m365.cloud.microsoft/chat")

        # Wait for user to log in
        print("\n" + "=" * 50)
        print("WAITING FOR LOGIN")
        print("=" * 50)
        print("Please log in to M365 Copilot in the browser window.")
        print("Once you're in the chat, press ENTER here to continue...")
        input()

        # Main loop
        completed_steps = set()

        while True:
            print_menu()

            # Show completed steps
            if completed_steps:
                print(f"Completed: {', '.join(str(s) for s in sorted(completed_steps))}")

            choice = input("\nEnter choice: ").strip().lower()

            if choice == 'q':
                print("\nClosing browser...")
                break

            if choice == 'c':
                custom_msg = input("Enter custom message: ").strip()
                if custom_msg:
                    print(f"\nSending custom message...")
                    if await send_message(page, custom_msg):
                        print("  Sent!")
                    else:
                        print("  Failed to send")
                continue

            try:
                step_num = int(choice)
                if 1 <= step_num <= len(DEMO_STEPS):
                    title, message = DEMO_STEPS[step_num - 1]
                    print(f"\nSending Step {step_num}: {title}")
                    print(f"  Message: {message[:60]}...")

                    if await send_message(page, message):
                        print("  Sent!")
                        completed_steps.add(step_num)
                    else:
                        print("  Failed to send")
                else:
                    print(f"Invalid step number. Choose 1-{len(DEMO_STEPS)}")
            except ValueError:
                print("Invalid choice. Enter a number (1-7), 'c' for custom, or 'q' to quit.")

        await browser.close()

    print("\nDemo complete!")


if __name__ == "__main__":
    asyncio.run(run_demo())
