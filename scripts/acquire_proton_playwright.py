#!/usr/bin/env python3
"""
Acquire Proton Drive shared files using Playwright.
Lets Proton's own web client handle the crypto.
"""

import asyncio
import os
import sys
from pathlib import Path

SHARES = {
    "audio": {
        "url": "https://drive.proton.me/urls/XA248JXEJC#ERr0VGD3cKud",
        "output": "assets/source/audio/master",
    },
    "image": {
        "url": "https://drive.proton.me/urls/HJ9B06AF74#UlhAg0ZnPzCH",
        "output": "assets/source/visual/artwork",
    },
}


async def download_share(name: str, config: dict, download_dir: str) -> bool:
    """Download a single Proton Drive share using Playwright."""
    from playwright.async_api import async_playwright

    print(f"\n{'='*60}")
    print(f"Acquiring {name}: {config['url']}")
    print(f"{'='*60}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print(f"1. Navigating to {config['url']}...")
        try:
            await page.goto(config["url"], wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"   Navigation timeout (may still work): {e}")

        # Wait for page to load and authenticate
        print("2. Waiting for authentication...")
        await asyncio.sleep(5)

        # Take a screenshot to see what we're dealing with
        screenshot_path = f"/tmp/proton_{name}_page.png"
        await page.screenshot(path=screenshot_path)
        print(f"   Screenshot saved to {screenshot_path}")

        # Get page content for debugging
        title = await page.title()
        print(f"   Page title: {title}")

        # Check if there's a password prompt
        password_input = await page.query_selector('input[type="password"]')
        if password_input:
            print("   Password prompt detected - share requires explicit password")
            # We don't have a separate password, the fragment should handle it
            # This might mean the share requires a user-set password we don't have
            await browser.close()
            return False

        # Look for download button
        print("3. Looking for download button...")
        
        # Try various selectors for download button
        download_selectors = [
            'button[data-testid="download"]',
            'button:has-text("Download")',
            'button:has-text("download")',
            '[class*="download"]',
            'a[download]',
        ]
        
        download_button = None
        for selector in download_selectors:
            download_button = await page.query_selector(selector)
            if download_button:
                print(f"   Found download button: {selector}")
                break

        if not download_button:
            # Try to find any buttons
            buttons = await page.query_selector_all("button")
            print(f"   Found {len(buttons)} buttons on page")
            for btn in buttons[:5]:
                text = await btn.text_content()
                print(f"     - '{text}'")
            
            # Get page text for debugging
            body_text = await page.text_content("body")
            print(f"   Page text (first 500 chars): {body_text[:500] if body_text else 'empty'}")
            await browser.close()
            return False

        # Click download and wait for the download
        print("4. Downloading...")
        try:
            async with page.expect_download(timeout=120000) as download_info:
                await download_button.click()
            
            download = await download_info.value
            output_path = Path(download_dir) / download.suggested_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            await download.save_as(str(output_path))
            print(f"   Saved to {output_path} ({output_path.stat().st_size} bytes)")
            await browser.close()
            return True
        except Exception as e:
            print(f"   Download failed: {e}")
            await browser.close()
            return False


async def main():
    """Main entry point."""
    print("Proton Drive Acquisition (Playwright)")
    print("="*60)

    download_dir = "/tmp/proton_downloads"
    os.makedirs(download_dir, exist_ok=True)

    results = {}
    for name, config in SHARES.items():
        success = await download_share(name, config, download_dir)
        results[name] = {"success": success}

    print("\n" + "="*60)
    print("Summary:")
    for name, result in results.items():
        status = "✓" if result["success"] else "✗"
        print(f"  {status} {name}")

    return 0 if all(r["success"] for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))