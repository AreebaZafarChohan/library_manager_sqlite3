import sqlite3
import streamlit as st
import pandas as pd
import time

# 📌 Database Connection Function
def connect_db():
    return sqlite3.connect("library_manager.db")

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # ✅ Create Genre Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # ✅ Create Books Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        year INTEGER NOT NULL,
        genre_id INTEGER,
        read_status BOOLEAN,
        rating REAL,
        read_link TEXT,
        download_link TEXT,
        password TEXT NOT NULL,
        FOREIGN KEY (genre_id) REFERENCES genres(id)
    );
    """)

    conn.commit()
    cursor.close()
    conn.close()


create_tables()

def add_genre(name):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO genres (name) VALUES (?)", (name,))
        conn.commit()
        st.success(f"✅ Genre '{name}' added successfully!")
        time.sleep(2)  
        st.rerun()  
    except sqlite3.IntegrityError:
        st.warning(f"⚠️ Genre '{name}' already exists!")
    finally:
        cursor.close()
        conn.close()

def remove_genre(name):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM genres WHERE name = ?", (name,))
        genre_id = cursor.fetchone()
        
        if genre_id:
            genre_id = genre_id[0]
            cursor.execute("SELECT COUNT(*) FROM books WHERE genre_id = ?", (genre_id,))
            book_count = cursor.fetchone()[0]
            
            if book_count > 0:
                st.warning(f"⚠️ Cannot delete '{name}'. There are {book_count} books associated with this genre!")
            else:
                cursor.execute("DELETE FROM genres WHERE id = ?", (genre_id,))
                conn.commit()
                st.success(f"✅ Genre '{name}' removed successfully!")
                time.sleep(2)  
                st.rerun()  
        else:
            st.warning(f"⚠️ Genre '{name}' not found!")
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()        

def get_genres():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM genres")
    genres = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return genres

def add_book(title, author, year, genre_id, read_status, rating, read_link, download_link, password):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO books (title, author, year, genre_id, read_status, rating, read_link, download_link, password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, author, year, genre_id, read_status, rating, read_link, download_link, password))
        conn.commit()
        st.success(f"📖 '{title}' by {author} added successfully! ✅")
        time.sleep(2)  
        st.rerun()  
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

def remove_book(title, password):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE title = ? AND password = ?", (title, password))
        conn.commit()
        if cursor.rowcount > 0:
            st.success(f"📖 '{title}' removed successfully! ✅")
            time.sleep(2)  
            st.rerun()  
        else:
            st.warning("⚠️ Incorrect password or book not found!")
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

def update_book(title, password, new_title, author, year, genre_id, read_status, rating, read_link, download_link):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE books SET title=?, author=?, year=?, genre_id=?, read_status=?, rating=?, read_link=?, download_link=? WHERE title=? AND password=?", 
                       (new_title, author, year, genre_id, read_status, rating, read_link, download_link, title, password))
        if cursor.rowcount > 0:
            conn.commit()
            st.success(f"✅ Book '{new_title}' updated successfully!")
            time.sleep(2)
            st.rerun()
        else:
            st.warning("⚠️ Incorrect password or book not found!")
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()        

def fetch_books():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT books.id, books.title, books.author, books.year, genres.name, books.read_status, books.rating
        FROM books
        JOIN genres ON books.genre_id = genres.id
        """)
        books = cursor.fetchall()
    except Exception as e:
        st.error(f"❌ Error: {e}")
        books = []
    finally:
        cursor.close()
        conn.close()
    return books

def get_book_statistics():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    total_books = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM books WHERE read_status = 1")
    read_books = cursor.fetchone()[0]
    cursor.execute("SELECT AVG(rating) FROM books WHERE rating IS NOT NULL")
    avg_rating = cursor.fetchone()[0] or 0
    cursor.execute("SELECT genres.name FROM books JOIN genres ON books.genre_id = genres.id GROUP BY books.genre_id ORDER BY COUNT(*) DESC LIMIT 1")
    most_popular_genre = cursor.fetchone()
    most_popular_genre = most_popular_genre[0] if most_popular_genre else "No Popular Genre"
    cursor.close()
    conn.close()
    return total_books, read_books, avg_rating, most_popular_genre

def fetch_books_by_genre(genre_id=None):
    conn = connect_db()
    cursor = conn.cursor()
    query = """
    SELECT books.id, books.title, books.author, books.year, genres.name, books.read_status, books.rating, books.read_link, books.download_link
    FROM books
    JOIN genres ON books.genre_id = genres.id
    """
    
    if genre_id:
        query += " WHERE books.genre_id = ?"
        cursor.execute(query, (genre_id,))
    else:
        cursor.execute(query)
    
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return books

genre_options = {None: "All"}  # Default for all genres
genre_options.update({row[0]: row[1] for row in connect_db().cursor().execute("SELECT id, name FROM genres").fetchall()})

# 📌 Sidebar Setup
st.sidebar.title("📚 Library Manager")
option = st.sidebar.radio("Navigation", ["Add Genre", "Remove Genre", "Add Book", "Remove Book", "Update Book", "View Books", "Book Statistics", "Guidelines"])

st.header("📚 Library Manager 'sqlite3'")

genre_options = get_genres()

if option == "Add Genre":
    st.header("➕ Add Genre")
    new_genre = st.text_input("Enter Genre Name")
    if st.button("Add Genre"):
        add_genre(new_genre)
        st.rerun()

elif option == "Remove Genre":
    st.header("❌ Remove Genre")
    genre_to_remove = st.selectbox("Select Genre to Remove", list(genre_options.values()))
    if st.button("Remove Genre"):
        remove_genre(genre_to_remove)
        st.rerun()        

elif option == "Add Book":
    st.header("📖 Add Book")
    book_title = st.text_input("Title")
    book_author = st.text_input("Author")
    book_year = st.number_input("Year", min_value=1800, max_value=2025, step=1)
    book_genre = st.selectbox("Genre", list(genre_options.values()))
    book_read = st.checkbox("Read?")
    book_rating = st.slider("Rating", 0.0, 5.0, 2.5, 0.1)
    book_read_link = st.text_input("Read Online Link")
    book_download_link = st.text_input("Download Link")
    book_password = st.text_input("Set Password", type="password")
    if st.button("Add Book"):
        genre_id = next(id_ for id_, name in genre_options.items() if name == book_genre)
        add_book(book_title, book_author, book_year, genre_id, book_read, book_rating, book_read_link, book_download_link, book_password)
        st.rerun()

elif option == "Remove Book":
    st.header("❌ Remove Book")
    remove_title = st.selectbox("Select Book to Remove", [book[1] for book in fetch_books()])
    remove_password = st.text_input("Password", type="password")
    if st.button("Remove Book"):
        remove_book(remove_title, remove_password)
        st.rerun()

elif option == "Update Book":
    st.header("✏️ Update Book")
    book_title = st.text_input("Current Title")
    book_password = st.text_input("Enter Password", type="password")
    new_book_title = st.text_input("New Title")
    book_author = st.text_input("Author")
    book_year = st.number_input("Year", min_value=1800, max_value=2025, step=1)
    book_genre = st.selectbox("Genre", list(genre_options.values()))
    book_read = st.checkbox("Read?")
    book_rating = st.slider("Rating", 0.0, 5.0, 2.5, 0.1)
    book_read_link = st.text_input("Read Online Link")
    book_download_link = st.text_input("Download Link")
    if st.button("Update Book"):
        genre_id = next(id_ for id_, name in genre_options.items() if name == book_genre)
        update_book(book_title, book_password, new_book_title, book_author, book_year, genre_id, book_read, book_rating, book_read_link, book_download_link)
        

elif option == "View Books":        
    st.header("📖 View Books")
    selected_genre = st.selectbox("Filter by Genre", list(genre_options.values()))
    genre_id = next((id_ for id_, name in genre_options.items() if name == selected_genre), None)
    
    books = fetch_books_by_genre(genre_id if genre_id != 0 else None)
    
    if books:
        for book in books:
            st.subheader(f"📕 {book[1]} by {book[2]}")
            st.write(f"- **Year:** {book[3]}")
            st.write(f"- **Genre:** {book[4]}")
            st.write(f"- **Read Status:** {'✅ Read' if book[5] else '❌ Not Read'}")
            st.write(f"- **Rating:** {book[6]}/5")
            col1, col2 = st.columns(2)
            with col1:
                if book[7]:
                    st.markdown(f"[📖 Read Online]({book[7]})")
            with col2:
                if book[8]:
                    st.markdown(f"[📥 Download]({book[8]})")
    else:
        st.warning("No books available.")

elif option == "Book Statistics":
    st.header("📊 Book Statistics")
    total_books, read_books, avg_rating, most_popular_genre = get_book_statistics()
    st.write(f"- Total Books: {total_books}")
    st.write(f"- Read Books: {read_books}")
    st.write(f"- Average Rating: {avg_rating:.2f}")
    st.write(f"- Most Popular Genre: {most_popular_genre}")

elif option == "Guidelines":
    st.header("📜 Guidelines")
    st.markdown("""
    - **Add Genre**: Enter a unique genre name and click 'Add Genre'. Duplicate genres are not allowed.
    - **Remove Genre**: Select a genre to remove. A genre can only be deleted if no books are associated with it.
    - **Add Book**: Provide complete book details (title, author, year, genre, read status, rating, read/download links). Set a password for future updates and removal.
    - **Remove Book**: Select a book and enter the correct password to delete it.
    - **Update Book**: Provide the correct current book title and password to modify its details.
    - **View Books**: Browse all books, filter by genre, and access read/download links if available.
    - **Book Statistics**: View insights such as total books, read books, average ratings, and the most popular genre.
    """)

st.markdown(
        "<p style='text-align: center; font-size: 14px; color: gray'>"
        "Library Manager developed with ❤️ by Areeba Zafar |  © 2025</p>",
        unsafe_allow_html=True
    )