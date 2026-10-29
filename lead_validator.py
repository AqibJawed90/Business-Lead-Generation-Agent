from urllib.parse import urlparse


EXCLUDED_DOMAINS = {
    "google.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "yelp.com",
    "tripadvisor.com",
    "wikipedia.org",
    "opentable.de",
}


def normalize_url(url: str) -> str:
    url = (url or "").strip()

    if not url:
        return ""

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    if not hostname or "." not in hostname:
        return ""

    if hostname.startswith("www."):
        hostname = hostname[4:]

    return f"https://{hostname}"


def is_valid_business_url(url: str) -> bool:
    normalized = normalize_url(url)

    if not normalized:
        return False

    hostname = urlparse(normalized).hostname or ""

    for domain in EXCLUDED_DOMAINS:
        if hostname == domain or hostname.endswith("." + domain):
            return False

    return True


def validate_leads(leads: list[dict]) -> list[dict]:
    valid_leads = []
    seen_domains = set()

    for lead in leads:
        url = normalize_url(lead.get("url", ""))

        if not is_valid_business_url(url):
            continue

        domain = urlparse(url).hostname

        if domain in seen_domains:
            continue

        seen_domains.add(domain)

        valid_leads.append({
            **lead,
            "url": url,
            "domain": domain,
        })

    return valid_leads
