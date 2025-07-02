import sqlite3
import random
from faker import Faker
from db import DB_NAME, create_tables

faker = Faker()

NUM_BOOKS = 50000  # Adjust for load testing

def seed_books(n=NUM_BOOKS):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for i in range(n):
        book_number = 100000 + i
        title = faker.sentence(nb_words=5)
        author = faker.name()
        translator = faker.name() if random.random() > 0.7 else ''
        pub_date = faker.date()
        isbn = faker.isbn13()
        language = random.choice(['English', 'Spanish', 'French', 'German', 'Arabic'])
        genre = random.choice(['Fiction', 'Non-fiction', 'Sci-Fi', 'Fantasy', 'Biography'])
        edition = f"{random.randint(1, 10)}th"
        status = random.choice(['Available', 'Not Available', 'Missing'])

        # Insert into books
        cur.execute("""
                    INSERT INTO books (book_number, title, author, translator, pub_date, isbn, language, genre, edition, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (book_number, title, author, translator, pub_date, isbn, language, genre, edition, status))

        book_id = cur.lastrowid

        # Insert default inventory
        cur.execute("""
                    INSERT INTO inventory (book_id, available, lent, missing, damaged)
                    VALUES (?, ?, ?, ?, ?)
                    """, (book_id, random.randint(0, 3), random.randint(0, 3), 0, 0))

    conn.commit()
    conn.close()
    print(f"✅ Inserted {n} fake books.")

if __name__ == "__main__":
    create_tables()
    seed_books()
