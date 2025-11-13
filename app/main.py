from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Depends, Header
from pydantic import BaseModel
import json
import os

BOOKS_FILE = "data/books_with_country.json"
API_KEY = "hlink"

# ==== Pydantic models ====
class Book(BaseModel):
    title: str
    price: str
    availability: str
    product_page_url: str
    star_rating: int
    category: str
    publisher_country: str


def verify_api_key(x_api_key: str = Header(None)):
    """
    Dependency để kiểm tra header X-API-KEY.
    Nếu sai hoặc không có -> 401 Unauthorized.
    """
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )


# ==== Load data từ file khi khởi động ====
def load_books_from_file() -> List[Book]:
    if not os.path.exists(BOOKS_FILE):
        print(f"[WARN] {BOOKS_FILE} not found. Starting with empty list.")
        return []

    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # convert dict -> Book
    books = [Book(**b) for b in raw]
    print(f"[INFO] Loaded {len(books)} books from {BOOKS_FILE}")
    return books


def save_books_to_file(books: List[Book]) -> None:
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump([b.model_dump() for b in books], f, ensure_ascii=False, indent=4)
    print(f"[INFO] Saved {len(books)} books to {BOOKS_FILE}")


app = FastAPI(title="Books API", version="1.0.0")

# "database" in-memory
books_db: List[Book] = load_books_from_file()


# ==== ENDPOINTS ====


@app.get("/books", response_model=List[Book])
def get_books(country: Optional[str] = Query(None, description="Publisher country")):
    """
    GET /books
    - Nếu không có query ?country= -> trả full list.
    - Nếu có ?country=XYZ -> filter theo publisher_country.
    """
    if country is None:
        return books_db

    # so sánh không phân biệt hoa thường
    filtered = [
        b for b in books_db
        if b.publisher_country.lower() == country.lower()
    ]
    return filtered


@app.post(
    "/books",
    response_model=Book,
    status_code=201,
    dependencies=[Depends(verify_api_key)]
)
def add_book(book: Book):
    """
    POST /books
    Thêm 1 book mới (JSON body).
    """
    # Kiểm tra trùng title
    for b in books_db:
        if b.title == book.title:
            raise HTTPException(
                status_code=400,
                detail=f"Book with title '{book.title}' already exists."
            )

    books_db.append(book)
    save_books_to_file(books_db)
    return book


@app.delete(
    "/books/{title}",
    status_code=204,
    dependencies=[Depends(verify_api_key)]
)
def delete_book(title: str):
    """
    DELETE /books/{title}
    Xoá book theo title (match chính xác).
    """
    global books_db
    index_to_delete = None

    for i, b in enumerate(books_db):
        if b.title == title:
            index_to_delete = i
            break

    if index_to_delete is None:
        raise HTTPException(
            status_code=404,
            detail=f"Book with title '{title}' not found."
        )

    books_db.pop(index_to_delete)
    save_books_to_file(books_db)

    return


@app.get("/")
def root():
    return {"message": "Books API is running. Try GET /books"}
