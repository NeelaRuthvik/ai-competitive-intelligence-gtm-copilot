
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def fetch_page(url):

    # Validate URL
    parsed_url = urlparse(url)

    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        raise ValueError("Invalid URL")

    headers = {
        "User-Agent": "CompetitiveIntelligenceResearchBot/1.0"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        return response.text

    except requests.exceptions.RequestException as error:
        print(f"Error fetching webpage: {error}")
        return None


def extract_page_information(html, url):

    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Extract page title
    title = soup.title.get_text(strip=True) if soup.title else None

    # Extract meta description
    description_tag = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    description = (
        description_tag.get("content")
        if description_tag else None
    )

    # Extract headings
    headings = [
        heading.get_text(" ", strip=True)
        for heading in soup.find_all(["h1", "h2", "h3"])
    ]

    # Extract visible page text
    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    page_text = soup.get_text(" ", strip=True)

    return {
        "source_url": url,
        "page_title": title,
        "description": description,
        "headings": headings,
        "page_text": page_text
    }


def scrape_page(url):

    html = fetch_page(url)

    if html is None:
        return None

    return extract_page_information(html, url)
