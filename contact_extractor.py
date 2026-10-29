
import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 15

CONTACT_PATHS = [
    "/contact",
    "/contact/",
    "/kontakt",
    "/kontakt/",
    "/contact-us",
    "/contact-us/",
    "/impressum",
    "/impressum/",
    "/imprint",
    "/about/contact",
]


def normalize_email(email: str) -> str:
    return email.strip().strip(".,;:()[]<>").lower()


def extract_emails(soup: BeautifulSoup, text: str) -> set[str]:
    emails = set()

    # Emails visible in page text
    email_pattern = (
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )
    emails.update(re.findall(email_pattern, text))

    # Emails from mailto links
    for link in soup.select('a[href^="mailto:"]'):
        email = link.get("href", "").split(":", 1)[1].split("?")[0]

        if email:
            emails.add(email)

    cleaned = set()

    for email in emails:
        email = normalize_email(email)

        if "example." in email:
            continue

        if re.fullmatch(email_pattern, email):
            cleaned.add(email)

    return cleaned


def normalize_phone(phone: str) -> str:
    """Phone number ke extra spaces aur punctuation ko clean karta hai."""

    phone = phone.strip()
    phone = re.sub(r"\s+", " ", phone)
    phone = phone.strip(" ,;")

    return phone


def is_valid_phone(phone: str) -> bool:
    """
    Basic phone validation.

    Dates, year ranges aur date-time combinations reject karta hai.
    International phone numbers ko support karta hai.
    """

    candidate = normalize_phone(phone)

    if not candidate:
        return False

    # Date formats, e.g. 20.10.2026, 2026-10-22, 20/10/2026
    date_patterns = [
        r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}",
        r"\d{4}-\d{1,2}-\d{1,2}",
    ]

    # Reject any candidate containing a date, even if the regex
    # accidentally adds digits from the neighbouring text.
    if any(re.search(pattern, candidate) for pattern in date_patterns):
        return False

    # Reject year ranges, e.g. 2002 - 2014
    if re.search(
        r"(?<!\d)(?:19|20)\d{2}\s*[-–]\s*(?:19|20)\d{2}(?!\d)",
        candidate,
    ):
        return False

    # A phone number should contain 8–15 digits
    digits = re.sub(r"\D", "", candidate)

    if not 8 <= len(digits) <= 15:
        return False

    # Allow only common phone formatting characters
    if not re.fullmatch(r"\+?[\d\s()./-]+", candidate):
        return False

    return True


def extract_phones(soup: BeautifulSoup, text: str) -> list[str]:
    phones = []

    # First priority: explicit telephone links
    for link in soup.select('a[href^="tel:"]'):
        raw_phone = link.get("href", "").split(":", 1)[1]
        raw_phone = raw_phone.split("?", 1)[0]
        phone = normalize_phone(raw_phone)

        if is_valid_phone(phone):
            phones.append(phone)

    # Second priority: phone numbers in visible text.
    # Limit candidates to avoid joining dates and nearby unrelated digits.
    if not phones:
        phone_pattern = re.compile(
            r"(?<!\w)\+?\d[\d()./-]*(?:\s+\d[\d()./-]*){1,5}(?!\w)"
        )

        for match in phone_pattern.finditer(text):
            candidate = normalize_phone(match.group(0))

            if is_valid_phone(candidate):
                phones.append(candidate)

    # Remove duplicates while preserving order
    unique_phones = []
    seen = set()

    for phone in phones:
        digits = re.sub(r"\D", "", phone)

        if digits not in seen:
            seen.add(digits)
            unique_phones.append(phone)

    return unique_phones


def extract_contact_info(website_url: str) -> dict:
    result = {
        "email": "",
        "phone": "",
        "contact_page": "",
        "status": "not_checked",
    }

    website_url = website_url.strip()

    if not website_url:
        result["status"] = "invalid_url"
        return result

    if not website_url.startswith(("http://", "https://")):
        website_url = "https://" + website_url

    parsed = urlparse(website_url)

    if not parsed.hostname:
        result["status"] = "invalid_url"
        return result

    # Try www and non-www versions
    host = parsed.hostname
    hosts = [host]

    if host.startswith("www."):
        hosts.append(host[4:])
    else:
        hosts.append("www." + host)

    # Homepage first, followed by common contact pages
    pages_to_try = [website_url]

    for alternative_host in hosts:
        base = f"https://{alternative_host}"

        for path in CONTACT_PATHS:
            pages_to_try.append(urljoin(base + "/", path.lstrip("/")))

    visited = set()
    successful_pages = 0
    errors = []

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        for page_url in pages_to_try:
            if page_url in visited:
                continue

            visited.add(page_url)

            try:
                response = session.get(
                    page_url,
                    timeout=TIMEOUT,
                    allow_redirects=True,
                )

                if response.status_code in (403, 404, 410):
                    errors.append(f"{response.status_code}: {page_url}")
                    continue

                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "")

                if "html" not in content_type.lower():
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text(" ", strip=True)

                successful_pages += 1

                emails = extract_emails(soup, text)
                phones = extract_phones(soup, text)

                # Keep the first email and phone found
                if not result["email"] and emails:
                    result["email"] = sorted(emails)[0]

                if not result["phone"] and phones:
                    result["phone"] = phones[0]

                # Record contact/imprint pages only
                final_url = response.url
                final_path = urlparse(final_url).path.lower()

                if (
                    not result["contact_page"]
                    and any(
                        word in final_path
                        for word in (
                            "contact",
                            "kontakt",
                            "impressum",
                            "imprint",
                        )
                    )
                ):
                    result["contact_page"] = final_url

                # Stop when all three fields have been found
                if (
                    result["email"]
                    and result["phone"]
                    and result["contact_page"]
                ):
                    break

            except requests.RequestException as error:
                errors.append(
                    f"{type(error).__name__}: {page_url}"
                )

    finally:
        session.close()

    if successful_pages:
        result["status"] = "success"
    elif errors:
        result["status"] = "request_error: " + errors[0]
    else:
        result["status"] = "no_accessible_pages"

    return result


if __name__ == "__main__":
    test_url = input("Business website URL: ").strip()

    contact = extract_contact_info(test_url)

    print("\n===== CONTACT EXTRACTION RESULT =====")
    print(f"Status: {contact['status']}")
    print(f"Email: {contact['email'] or 'Not found'}")
    print(f"Phone: {contact['phone'] or 'Not found'}")
    print(f"Contact page: {contact['contact_page'] or 'Not found'}")
