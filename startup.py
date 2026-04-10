from db.database import init_db
from scraper.scraper import generate_simulated_jobs, save_jobs
from scraper.extractor import extract_skills
from models.predictor import run_predictions
from werkzeug.security import generate_password_hash
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'skillsight.db')

def check_and_seed():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM job_postings')
    count = cursor.fetchone()[0]

    if count < 100:
        print("Seeding database...")
        jobs = generate_simulated_jobs(500)
        save_jobs(jobs)
        extract_skills()
        run_predictions()
        print("Data seeded.")

    # Always ensure demo account exists
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('demo@skillsight.com',))
    if cursor.fetchone()[0] == 0:
        hashed = generate_password_hash('demo1234')
        cursor.execute('INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)',
                       ('Demo User', 'demo@skillsight.com', hashed))
        conn.commit()
        print("Demo account created.")

    conn.close()

if __name__ == '__main__':
    check_and_seed()