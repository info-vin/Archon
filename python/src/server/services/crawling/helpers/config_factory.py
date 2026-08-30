from crawl4ai import CacheMode


def get_base_crawler_config_kwargs(settings: dict) -> dict:
    """
    Returns the base kwargs for CrawlerRunConfig to eliminate massive duplication
    across crawler strategies and ensure the anti-noise defense line is unbroken.
    """
    return {
        "cache_mode": CacheMode.BYPASS,
        "wait_until": settings.get("CRAWL_WAIT_STRATEGY", "domcontentloaded"),
        "page_timeout": int(settings.get("CRAWL_PAGE_TIMEOUT", "45000")),
        "delay_before_return_html": float(settings.get("CRAWL_DELAY_BEFORE_HTML", "0.5")),
        "scan_full_page": True,
        "process_iframes": False,
        "remove_overlay_elements": True,
        "excluded_tags": [
            "nav", "footer", "header", "aside", "script", "noscript", "style", "iframe", "svg"
        ], # 合法
        "excluded_selector": "[role='dialog'], [role='banner'], [role='navigation'], .cookie-banner, #onetrust-consent-sdk, [id*='chatbot'], [class*='chatbot'], [class*='assistant']",
        "js_code": '''
        const acceptBtn = document.querySelector("#onetrust-accept-btn-handler");
        if (acceptBtn) {
            acceptBtn.click();
        }
        ''',
    }
