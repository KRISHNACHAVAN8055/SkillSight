import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'skillsight.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS job_postings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            description TEXT,
            source TEXT,
            date_scraped TEXT
        );
        CREATE TABLE IF NOT EXISTS skill_mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill TEXT,
            month TEXT,
            count INTEGER,
            total_jobs INTEGER,
            normalized_count REAL
        );
        CREATE TABLE IF NOT EXISTS skill_forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill TEXT,
            slope REAL,
            obsolescence_score REAL,
            category TEXT,
            forecast_json TEXT
        );
        CREATE TABLE IF NOT EXISTS resume_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT,
            resume_text TEXT,
            analysis_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()