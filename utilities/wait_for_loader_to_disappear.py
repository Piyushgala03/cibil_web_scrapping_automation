# wait_for_loader_to_disappear.py

def wait_for_loader_to_disappear(page, logger, timeout_ms:int=60000):
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
            timeout=timeout_ms
        )
        logger.info("Loader disappeared.")
    except Exception:
        logger.warning(f"⚠️ Loader did not disappear within {timeout_ms/1000} seconds...")
        