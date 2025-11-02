# is_website_issue.py

def is_website_issue(response_text: str) -> bool:
    """
    Checks if the given response text indicates a website or server issue.
    Returns True if such issue is detected, otherwise False.
    """
    if not response_text:
        return False

    website_issue_signatures = [
        "Issue with API response, try after sometime.",
        "Web server is returning an unknown error",
    ]

    for sig in website_issue_signatures:
        if sig.lower() in response_text.lower():
            print("⚠️ Website issue detected! Possibly server-side problem.")
            return True

    return False
