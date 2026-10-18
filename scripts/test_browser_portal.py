"""
Project Atlas - Playwright Browser Diagnostic Script
Tests tenant switching, sample queries, feedback, and DOM updates.
"""
from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.on('console', lambda msg: print('BROWSER CONSOLE:', msg.type, msg.text))
        page.on('request', lambda req: print('BROWSER REQ:', req.method, req.url))
        page.on('response', lambda res: print('BROWSER RES:', res.status, res.url))

        print('=== 1. Load Portal ===')
        page.goto('http://127.0.0.1:8080')
        print('Initial tenant:', page.locator('.tenant-name').inner_text())

        print('=== 2. Switch to C-02 ===')
        page.click('#btnSwitchC02')
        page.wait_for_load_state('networkidle')
        print('Tenant after switch 1:', page.locator('.tenant-name').inner_text())

        print('=== 3. Switch back to C-01 ===')
        page.click('#btnSwitchC01')
        page.wait_for_load_state('networkidle')
        print('Tenant after switch 2:', page.locator('.tenant-name').inner_text())

        print('=== 4. Switch to C-02 again ===')
        page.click('#btnSwitchC02')
        page.wait_for_load_state('networkidle')
        print('Tenant after switch 3:', page.locator('.tenant-name').inner_text())

        print('=== 5. Switch to C-01 again ===')
        page.click('#btnSwitchC01')
        page.wait_for_load_state('networkidle')
        print('Tenant after switch 4:', page.locator('.tenant-name').inner_text())


        print('=== 4. Test Sample Query Button Click ===')
        quick_btns = page.locator('.btn-quick').all()
        print(f'Found {len(quick_btns)} quick prompt buttons.')
        if quick_btns:
            print('Clicking first quick prompt button:', quick_btns[0].inner_text())
            quick_btns[0].click()
            print('Value in userInput after click:', page.locator('#userInput').input_value())
            # Wait for response
            page.wait_for_timeout(4000)
            messages = page.locator('.message').all()
            print(f'Total messages in DOM: {len(messages)}')
            for i, m in enumerate(messages):
                print(f'Message {i}: {m.inner_text()[:80]}...')

        browser.close()

if __name__ == '__main__':
    run()
