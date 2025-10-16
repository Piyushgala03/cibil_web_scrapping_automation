def wait_for_loader_to_disappear(page, logging, timeout=60000):
    """
    Waits for the page loader to disappear.
    
    Args:
        page: Playwright page object.
        timeout: Maximum time to wait for the loader in milliseconds.
    """
    try:
        page.wait_for_selector(
            "div.blockUI.blockMsg.blockPage",
            state="detached",
            timeout=timeout
        )
        print("✅ Loader disappeared.")
        logging.info("Loader disappeared.")
    except Exception:
        print(f"⚠️ Loader did not disappear within {timeout/1000} seconds.")
        logging.warning(f"Loader did not disappear within {timeout/1000} seconds.")