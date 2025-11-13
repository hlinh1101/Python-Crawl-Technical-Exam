from dataclasses import dataclass

@dataclass
class Book:
    title: str
    price: str
    availability: str
    product_page_url: str
    star_rating: int
    category: str
    publisher_country: str | None = None
