from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
API_KEY = "hlink"


def test_get_books():
    resp = client.get("/books")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_books_filter_by_country():
    # Lấy 1 sách bất kỳ để xem publisher_country
    resp_all = client.get("/books")
    assert resp_all.status_code == 200
    books = resp_all.json()
    assert len(books) > 0

    sample_country = books[0]["publisher_country"]

    # Gọi API filter theo country đó
    resp = client.get(f"/books?country={sample_country}")
    assert resp.status_code == 200
    filtered = resp.json()

    # Tất cả sách trả về đều có country đúng
    for b in filtered:
        assert b["publisher_country"].lower() == sample_country.lower()


def test_post_book_authorized():
    new_book = {
        "title": "Unit Test Book Authorized",
        "price": "£10.99",
        "availability": "In stock",
        "product_page_url": "http://example.com",
        "star_rating": 5,
        "category": "Test",
        "publisher_country": "Japan"
    }
    resp = client.post(
        "/books",
        json=new_book,
        headers={"X-API-KEY": API_KEY},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == new_book["title"]


def test_post_book_unauthorized():
    new_book = {
        "title": "Unit Test Book Unauthorized",
        "price": "£9.99",
        "availability": "In stock",
        "product_page_url": "http://example.com",
        "star_rating": 4,
        "category": "Test",
        "publisher_country": "Viet Nam"
    }
    # Không gửi X-API-KEY
    resp = client.post("/books", json=new_book)
    assert resp.status_code == 401
    body = resp.json()
    assert "Invalid or missing API key" in body["detail"]


def test_post_duplicate_title():
    title = "Duplicate Test Book"

    book1 = {
        "title": title,
        "price": "£5.00",
        "availability": "In stock",
        "product_page_url": "http://example.com/dup1",
        "star_rating": 3,
        "category": "Test",
        "publisher_country": "France"
    }
    book2 = {
        "title": title,  # trùng title
        "price": "£6.00",
        "availability": "In stock",
        "product_page_url": "http://example.com/dup2",
        "star_rating": 4,
        "category": "Test",
        "publisher_country": "Germany"
    }

    # Lần 1: OK
    resp1 = client.post(
        "/books",
        json=book1,
        headers={"X-API-KEY": API_KEY},
    )
    assert resp1.status_code == 201

    # Lần 2: phải lỗi 400 vì trùng title
    resp2 = client.post(
        "/books",
        json=book2,
        headers={"X-API-KEY": API_KEY},
    )
    assert resp2.status_code == 400
    body = resp2.json()
    assert "already exists" in body["detail"]


def test_delete_book_authorized():
    title = "Unit Test Book To Delete"

    new_book = {
        "title": title,
        "price": "£7.77",
        "availability": "In stock",
        "product_page_url": "http://example.com/delete",
        "star_rating": 4,
        "category": "Test",
        "publisher_country": "Italy"
    }

    # Thêm sách trước
    resp_add = client.post(
        "/books",
        json=new_book,
        headers={"X-API-KEY": API_KEY},
    )
    assert resp_add.status_code == 201

    # Xoá sách
    resp_del = client.delete(
        f"/books/{title}",
        headers={"X-API-KEY": API_KEY},
    )
    assert resp_del.status_code == 204


def test_delete_book_not_found():
    title = "This Book Definitely Does Not Exist 12345"
    resp = client.delete(
        f"/books/{title}",
        headers={"X-API-KEY": API_KEY},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert "not found" in body["detail"]