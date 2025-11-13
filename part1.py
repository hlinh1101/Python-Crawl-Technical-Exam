from dataclasses import dataclass, asdict, fields
import csv
import os
from urllib.parse import urljoin, urlparse
import time
import json


import requests
from bs4 import BeautifulSoup

from models import Book

BASE_URL = "https://books.toscrape.com/"
HTML_BACKUP_DIR = "html_backup"
OUTPUT_CSV = "books.csv"
OUTPUT_JSON = "books.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    )
}


def get_soup(url: str, session: requests.Session) -> BeautifulSoup:
    resp = session.get(url, headers=HEADERS)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, "html.parser")


def star_rating_to_int(tag) -> int:
    """
    <p class="star-rating Three"> -> 3
    """
    if tag is None:
        return 0
    rating_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5,
    }
    classes = tag.get("class", [])
    for c in classes:
        if c in rating_map:
            return rating_map[c]
    return 0


def save_product_html(url: str, html_text: str):
    os.makedirs(HTML_BACKUP_DIR, exist_ok=True)
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_")
    if not path:
        path = "index"
    filename = f"{path}.html"
    filepath = os.path.join(HTML_BACKUP_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_text)


def get_all_categories(session: requests.Session) -> dict:
    soup = get_soup(BASE_URL, session)

    categories = {}

    for a in soup.select("ul.nav.nav-list > li > ul > li > a"):
        name = a.get_text(strip=True)
        href = a.get("href")           # "catalogue/category/books/travel_2/index.html"
        url = urljoin(BASE_URL, href)
        categories[name] = url

    return categories


def parse_category_page(soup: BeautifulSoup, current_url: str):
    """Lấy danh sách URL product từ 1 trang category."""
    for article in soup.select("article.product_pod"):
        a_tag = article.select_one("h3 a")
        href = a_tag.get("href")
        product_url = urljoin(current_url, href)
        yield product_url


def get_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    """Lấy URL trang tiếp theo trong category (nếu có)."""
    next_link = soup.select_one("li.next a")
    if not next_link:
        return None
    href = next_link.get("href")
    return urljoin(current_url, href)


def clean_data(value, *char_to_remove):
    for char in char_to_remove:
        value = value.replace(char, '')
    return value.strip() if value else None


def parse_product_page(url: str, category_name: str,
                       session: requests.Session) -> Book:
    resp = session.get(url, headers=HEADERS)
    resp.raise_for_status()

    # Backup HTML
    save_product_html(url, resp.text)

    soup = BeautifulSoup(resp.content, "html.parser")

    # Title
    title_tag = soup.select_one("h1")
    title = title_tag.get_text(strip=True)

    # Price
    price_tag = soup.select_one("p.price_color")
    price = price_tag.get_text(strip=True)

    # Availability
    avail_tag = soup.select_one("p.instock.availability")
    availability_text = avail_tag.get_text(strip=True) if avail_tag else ""
    availability = clean_data(availability_text, 'In stock', 'available', '(', ')')

    # Rating
    rating_tag = soup.select_one("p.star-rating")
    star_rating = star_rating_to_int(rating_tag)

    return Book(
        title=title,
        price=price,
        availability=availability,
        product_page_url=url,
        star_rating=star_rating,
        category=category_name,
    )


def scrape_category(category_name: str, category_url: str,
                    session: requests.Session) -> list[Book]:
    books: list[Book] = []
    current_url = category_url
    page_idx = 0

    while current_url:
        page_idx += 1
        print(f"[{category_name}] Page {page_idx}: {current_url}")

        soup = get_soup(current_url, session)
        product_urls = list(parse_category_page(soup, current_url))

        for url in product_urls:
            try:
                book = parse_product_page(url, category_name, session)
                books.append(book)
                print(f"    + {book.title}")
                time.sleep(0.1)
            except Exception as e:
                print(f"[WARN] Failed to parse {url}: {e}")

        next_url = get_next_page_url(soup, current_url)
        if not next_url:
            break
        current_url = next_url

    return books


def scrape_all_categories() -> list[Book]:
    all_books: list[Book] = []
    with requests.Session() as session:
        categories = get_all_categories(session)
        print(f"Found {len(categories)} categories:")
        for name in categories:
            print(" -", name)

        for cat_name, cat_url in categories.items():
            print(f"\nScraping category: {cat_name}")
            books = scrape_category(cat_name, cat_url, session)
            all_books.extend(books)
            print(f"  -> {len(books)} books from {cat_name}")

    print(f"\nTOTAL books scraped: {len(all_books)}")
    return all_books


def save_to_json(books: list[Book], filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([asdict(b) for b in books], f, ensure_ascii=False, indent=4)
    print(f"Saved JSON: {filename}")


def save_to_csv(books: list[Book], filename: str):
    fieldnames = [f.name for f in fields(Book)]
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(asdict(b) for b in books)
    print(f"Saved CSV: {filename}")


def main():
    books = scrape_all_categories()
    save_to_csv(books, OUTPUT_CSV)
    save_to_json(books, OUTPUT_JSON)


if __name__ == "__main__":
    main()