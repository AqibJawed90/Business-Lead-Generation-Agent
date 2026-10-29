
from urllib.parse import urlparse


# Directory, listing, social media aur news websites
EXCLUDED_DOMAINS = {
    # Directories and review platforms
    "goodfirms.co",
    "ezilon.com",
    "aeroleads.com",
    "yelp.com",
    "tripadvisor.com",
    "opentable.de",

    # Social platforms
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",

    # Media and general information
    "wikipedia.org",
    "cntraveller.com",
    "andershusa.com",
    "visitberlin.de",
    "berlin.de",
    "welcome-to-berlin.com",
    "revenuebase.ai",
}


# Titles that often indicate a directory, list, or association
EXCLUDED_TITLE_PHRASES = {
    "list of",
    "top real estate companies",
    "best real estate companies",
    "companies directory",
    "company directory",
    "business directory",
    "real estate directory",
    "top 10",
    "top 18",
    "industry association",
    "federation",
}


def get_hostname(url: str) -> str:
    """URL se normalized hostname return karta hai."""

    hostname = (urlparse(url).hostname or "").lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    return hostname


def is_directory_or_media(url: str) -> bool:
    """Known directory, media aur social domains ko identify karta hai."""

    hostname = get_hostname(url)

    if not hostname:
        return True

    return any(
        hostname == domain or hostname.endswith("." + domain)
        for domain in EXCLUDED_DOMAINS
    )


def has_excluded_title(title: str) -> bool:
    """Search result title mein directory/listing signals check karta hai."""

    normalized_title = title.lower().strip()

    return any(
        phrase in normalized_title
        for phrase in EXCLUDED_TITLE_PHRASES
    )


def is_likely_business_name(title: str) -> bool:
    """Empty ya clearly generic titles ko reject karta hai."""

    title = title.strip()

    if len(title) < 3:
        return False

    if has_excluded_title(title):
        return False

    return True


def qualify_businesses(leads: list[dict]) -> list[dict]:
    """
    Search results mein se likely business websites filter karta hai.

    Note: Ye heuristic filter hai; final business authenticity verify nahi karta.
    """

    qualified = []
    seen_domains = set()

    for lead in leads:
        url = lead.get("url", "").strip()
        title = lead.get("title", "").strip()

        if not url or not title:
            continue

        hostname = get_hostname(url)

        if not hostname:
            continue

        if is_directory_or_media(url):
            continue

        if not is_likely_business_name(title):
            continue

        # Same business domain ko ek hi baar include karna
        if hostname in seen_domains:
            continue

        seen_domains.add(hostname)

        qualified.append({
            **lead,
            "business_name": title,
            "qualification_status": "potential_business",
        })

    return qualified
