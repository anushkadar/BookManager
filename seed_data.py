import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta
from db import DB_NAME, create_tables

faker = Faker()

NUM_BOOKS = 50000  # Adjust for load testing
NUM_USERS = 5000   # Number of users to generate

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

        cur.execute("""
                    INSERT INTO books (book_number, title, author, translator, pub_date, isbn, language, genre, edition, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (book_number, title, author, translator, pub_date, isbn, language, genre, edition, status))

        book_id = cur.lastrowid

        cur.execute("""
                    INSERT INTO inventory (book_id, available, lent, missing, damaged)
                    VALUES (?, ?, ?, ?, ?)
                    """, (book_id, random.randint(0, 3), random.randint(0, 3), 0, 0))

    conn.commit()
    conn.close()
    print(f"✅ Inserted {n} fake books.")

def seed_users(n=NUM_USERS):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    membership_types = ['Student', 'Faculty', 'Staff', 'Researcher', 'Guest']
    type_weights = [0.6, 0.2, 0.15, 0.04, 0.01]
    statuses = ['Active', 'Expired', 'Banned']

    for i in range(n):
        first_name = faker.first_name()
        last_name = faker.last_name()
        name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}@{faker.domain_name()}"
        phone = faker.phone_number()
        membership_type = random.choices(membership_types, weights=type_weights, k=1)[0]
        status = random.choices(statuses, weights=[0.85, 0.1, 0.05], k=1)[0]

        cur.execute("""
                    INSERT INTO users (name, email, phone, membership_type, status)
                    VALUES (?, ?, ?, ?, ?)
                    """, (name, email, phone, membership_type, status))

    conn.commit()
    conn.close()
    print(f"✅ Inserted {n} fake users.")

def seed_loans():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Get all user IDs
    cur.execute("SELECT id FROM users")
    user_ids = [row[0] for row in cur.fetchall()]

    # Get all available book IDs
    cur.execute("SELECT book_id FROM books WHERE status = 'Available' LIMIT 10000")
    book_ids = [row[0] for row in cur.fetchall()]

    # Seed ~10% of users with loans
    num_loans = int(len(user_ids) * 0.1)

    for _ in range(num_loans):
        user_id = random.choice(user_ids)
        book_id = random.choice(book_ids)
        loan_date = faker.date_between(start_date='-1y', end_date='today')
        loan_dt = datetime.strptime(str(loan_date), '%Y-%m-%d')
        due_dt = loan_dt + timedelta(days=14)
        return_date = due_dt if random.random() > 0.2 else None

        cur.execute("""
                    INSERT INTO loans (user_id, book_id, loan_date, due_date, return_date)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        user_id,
                        book_id,
                        loan_date,
                        due_dt.strftime('%Y-%m-%d'),
                        return_date.strftime('%Y-%m-%d') if return_date else None
                    ))

        if not return_date:
            cur.execute("UPDATE books SET status = 'Not Available' WHERE book_id = ?", (book_id,))

    conn.commit()
    conn.close()
    print(f"✅ Inserted {num_loans} fake loan records.")

if __name__ == "__main__":
    create_tables()
    seed_books()
    seed_users()
    seed_loans()
