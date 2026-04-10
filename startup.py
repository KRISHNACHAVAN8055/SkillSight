from db.database import init_db
from scraper.scraper import generate_simulated_jobs, save_jobs
from scraper.extractor import extract_skills
from models.predictor import run_predictions
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'skillsight.db')

def check_and_seed():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM job_postings')
    count = cursor.fetchone()[0]
    conn.close()

    if count < 100:
        print("Seeding database with simulated data...")
        jobs = generate_simulated_jobs(500)
        save_jobs(jobs)
        extract_skills()
        run_predictions()
        print("Database seeded successfully.")
    else:
        print(f"Database already has {count} jobs. Skipping seed.")

if __name__ == '__main__':
    check_and_seed()