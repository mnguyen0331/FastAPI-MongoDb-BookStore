# Student's name: Phu Nguyen
# Course: CPSC 449-01 13991
# Assignment: Final Project
# Date: May 12, 2023

from fastapi import FastAPI, HTTPException
from pymongo import ReturnDocument
from pydantic import BaseModel, validator
from database import books_collection
from bson import ObjectId
from bson.son import SON

app = FastAPI()

# Book Model
class Book(BaseModel):
    title: str
    author: str
    description: str
    price: float 
    stock: int
    sales: int

    # Data Validation

    # Sanitize str inputs. Remove spaces from beginning and end
    @validator('title', 'author', 'description', pre=True)
    def sanitize_str_fields(cls, v):
        return v.strip()
    
    # Check for empty strings in str fields
    @validator('title', 'author', 'description')
    def check_empty(cls, v):
        if len(v) == 0:
            raise ValueError('Empty value!')
        return v
    
    # Check for negative number in number fields
    @validator('price', 'stock', 'sales')
    def check_negative(cls, v):
        if v < 0:
            raise ValueError('Negative value!')
        return v

    # Normalize title and author to capitalize the first char of each word.
    @validator('title', 'author')
    def normalize(cls, v):
        return ' '.join((word.capitalize()) for word in v.split(' '))


# Convert book record to dict type
def to_book_dict(book: Book) -> dict:
    return {
        "id": str(book["_id"]),
        "title": book["title"],
        "author": book["author"],
        "description": book["description"],
        "price": book["price"],
        "stock": book["stock"],
        "sales": book["sales"]
    }

# Convert a list of book records to a list of books dict type
def to_books_dict(books: list[Book]) -> list:
    return [to_book_dict(book) for book in books]

# Aggregation

# Return the total number of books in the store
def get_total_books() -> int:
    find_total_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$stock"}}}
    ]
    total_books = list(books_collection.aggregate(find_total_pipeline))[0]['total']
    return total_books
    # print('-' * 100)
    # print(f'The total number of books in the store is {total_books} books')
    # print('-' * 100)

# Return the top 5 bestselling books
def get_bestselling_books() -> list:
    best_selling_pipeline = [
        {"$group": {"_id": "$title", "sales": {"$sum": "$sales"}}},
        {"$sort": SON([("sales", -1)])},
        {"$limit": 5}
    ]
    bestselling_books = list(books_collection.aggregate(best_selling_pipeline))
    return bestselling_books
    # print('The top 5 bestselling books: ')
    # for book in bestselling_books:
    #     print(book)
    # print('-' * 100)

# Return the top 5 authors with the most books in the store
def get_most_book_authors() -> list:
    most_book_pipeline = [
        {"$group": {"_id": "$author", "number_of_books": {"$sum": "$stock"}}},
        {"$sort": SON([("number_of_books", -1)])},
        {"$limit": 5}
    ]
    authors = list(books_collection.aggregate(most_book_pipeline))
    return authors
    # print('The top 5 authors with the most books in the store: ')
    # for author in authors:
    #     print(author)
    # print('-' * 100)

# API Endpoints

# Retrieve a list of all books in the store
@app.get("/books")
async def get_all_books():
    books = to_books_dict(books_collection.find())
    return {
        'data': books
    }

# Retrieve a specific book by ID
@app.get("/books/{book_id}")
async def get_book(id: str):
    book = books_collection.find_one({"_id": ObjectId(id)})
    # Check for the existence of book_id
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book with id# '{id}' does not exist!")
    return {
        'data': to_book_dict(book)
    }

# Adds a new book to the store
@app.post('/books')
async def save_book(book: Book):
    # Check for duplicate title
    existed_book = books_collection.find_one({"title": book.title})
    if existed_book is not None:
        raise HTTPException(status_code=409, detail=f"Book with title '{book.title}' already exists!")
    try:
        books_collection.insert_one(dict(book))
        return {
            'message': 'Successfully inserted new book',
        }
    except Exception as error:
        print(error)
        return {
            'message': 'Failed to insert new book'
        }

# Update an existing book by ID
@app.put('/books/{book_id}')
async def update_book(id: str, book: Book):
    # Check for duplicate title with existing books
    existed_book = books_collection.find_one({"title": book.title})
    if existed_book is not None and to_book_dict(existed_book)["id"] != id:
        raise HTTPException(status_code=409, detail=f"Book with title '{book.title}' already exists!")
    updated_book = books_collection.find_one_and_update({"_id": ObjectId(id)}, {
            "$set": dict(book)},
            return_document=ReturnDocument.AFTER
    )
    # Check for the existence of book_id
    if updated_book is None:
        raise HTTPException(status_code=404, detail=f"Book with id# '{id}' does not exist!")
    return {
        'message': 'Successfully updated book',
        'data': to_book_dict(updated_book)
    }
   

# Deletes a book from the store by ID
@app.delete('/books/{book_id}')
async def delete_book(id: str):
    deleted_book = books_collection.find_one_and_delete({"_id": ObjectId(id)})
    # Check for the existence of book_id
    if deleted_book is None:
        raise HTTPException(status_code=404, detail=f"Book with id# '{id}' does not exist!")
    return {
        'message': 'Successfully deleted book'
    }

# Searches for books by title, author, and price range
@app.get('/search')
async def search_books(title: str = "", author: str = "", min_price: float = 0, max_price: float = 999):
    if min_price < 0 or max_price < 0 or min_price > max_price:
        raise HTTPException(status_code=400, detail="Invalid price ranges!")
    books = to_books_dict(books_collection.find({
        # Search books that have title parameter in their title fields, case insensitive
        "title": {
            "$regex": f"{title}",
            "$options": "i"
        },
        # Search books that has author parameter in their author fields, case insensitive
        "author": {
            "$regex": f"{author}",
            "$options": "i"
        },
        # Search books that have prices between min_price (default 0) and max_price (default 999), inclusive
        "price": {
            "$gte": min_price,
            "$lte": max_price
        }
    }))
    if len(books) == 0:
        return {
            'message': 'No books match search parameters!'
        }
    return {
        'data': books
    }
