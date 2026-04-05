import asyncio
from playwright.async_api import async_playwright
import os

OUT_DIR = r"C:\Users\mnanc\navigator\navigator\docs\screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

FRONTEND_PATH = r"file:///C:\Users\mnanc\navigator\navigator\frontend\index.html"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        # Screenshot 1: Hero + briefing
        await page.goto(FRONTEND_PATH)
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{OUT_DIR}\\01-hero.png", full_page=True)
        print("Shot 1 done: hero + overview")

        # Screenshot 2: Questionnaire section visible
        await page.evaluate("document.querySelector('#questionnaire').scrollIntoView()")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUT_DIR}\\02-questionnaire.png", full_page=True)
        print("Shot 2 done: questionnaire")

        # Screenshot 3: Recommendation cards
        await page.evaluate("document.querySelector('.recommendations-card').scrollIntoView()")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUT_DIR}\\03-recommendations.png", full_page=True)
        print("Shot 3 done: recommendations")

        # Screenshot 4: Workflow section
        await page.evaluate("document.querySelector('.workflow-card').scrollIntoView()")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUT_DIR}\\04-workflow.png", full_page=True)
        print("Shot 4 done: workflow")

        # Screenshot 5: Settings tab
        await page.click("[data-tab-target='settings']")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUT_DIR}\\05-settings.png", full_page=False)
        print("Shot 5 done: settings")

        await browser.close()
        print("All done.")

asyncio.run(main())
