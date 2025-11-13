from dataclasses import dataclass, asdict, fields
import csv
import os
from urllib.parse import urljoin, urlparse
import time
import json

import requests
import random

from models import Book

INPUT_JSON = "books.json"
OUTPUT_JSON = "books_with_country.json"
OUTPUT_CSV  = "books_with_country.csv"

RESTCOUNTRIES_URL = "https://restcountries.com/v3.1/all"
COUNTRIES_CACHE_FILE = "countries_cache.json"
COUNTRIES_CACHE_TTL = 24 * 3600 


def load_books_from_json() -> list[Book]:
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Book(**b) for b in raw]


def fetch_countries() -> list[str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    params = {
        "fields": "name"
    }

    resp = requests.get(RESTCOUNTRIES_URL, timeout=10,
                        headers=headers, params=params)

    if not resp.ok:
        print("Status:", resp.status_code)
        print("Body:", resp.text[:500])
        resp.raise_for_status()

    data = resp.json()
    countries: list[str] = []
    for c in data:
        name = c.get("name", {}).get("common")
        if name:
            countries.append(name)

    print(f"Fetched {len(countries)} countries from RestCountries API")
    return countries


def assign_random_countries(books: list[Book], countries: list[str]) -> None:
    if not countries:
        print("[WARN] No countries available.")
        return

    for b in books:
        b.publisher_country = random.choice(countries)


def fetch_countries_cached() -> list[str]:
    # Nếu file cache tồn tại & chưa hết hạn -> dùng cache
    if os.path.exists(COUNTRIES_CACHE_FILE):
        mtime = os.path.getmtime(COUNTRIES_CACHE_FILE)
        age = time.time() - mtime
        if age < COUNTRIES_CACHE_TTL:
            print("[CACHE] Using cached countries")
            with open(COUNTRIES_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print("[CACHE] Cache expired, refreshing...")

    # Nếu không có cache / cache hết hạn -> gọi API thật
    countries = fetch_countries()

    # Lưu lại cache
    with open(COUNTRIES_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(countries, f, ensure_ascii=False, indent=4)
    print(f"[CACHE] Saved {len(countries)} countries to cache file")

    return countries


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
    # countries = fetch_countries()
    books = load_books_from_json()
    countries = fetch_countries_cached()
    assign_random_countries(books, countries)

    save_to_csv(books, "books_with_country.csv")
    save_to_json(books, "books_with_country.json")


if __name__ == "__main__":
    main()