from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True if you don't want the browser to open
        page = browser.new_page()

        # Navigate to IOSCO website
        page.goto("https://www.iosco.org/")

        # Print the page title as confirmation
        print("Page Title:", page.title())

        # Close browser
        browser.close()

if __name__ == "__main__":
    run()