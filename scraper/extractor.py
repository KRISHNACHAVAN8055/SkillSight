import sqlite3
import os
import json
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'skillsight.db')

SKILLS = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
    'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring Boot',
    'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Cassandra', 'SQLite',
    'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Jenkins',
    'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision',
    'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy',
    'Tableau', 'Power BI', 'Excel', 'Hadoop', 'Spark', 'Kafka',
    'Git', 'Linux', 'REST API', 'GraphQL', 'Microservices', 'DevOps',
    'jQuery', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'Flutter', 'React Native'
]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def extract_skills():
    print("=== Skill Extractor ===")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, description, date_scraped FROM job_postings')
    jobs = cursor.fetchall()
    print(f"Processing {len(jobs)} job postings...")

    monthly_skill_counts = defaultdict(lambda: defaultdict(int))
    monthly_job_counts = defaultdict(int)

    for job in jobs:
        description = job['description'].lower()
        month = job['date_scraped']
        monthly_job_counts[month] += 1

        for skill in SKILLS:
            if skill.lower() in description:
                monthly_skill_counts[month][skill] += 1

    print(f"Found data across {len(monthly_job_counts)} months")

    cursor.execute('DELETE FROM skill_mentions')

    for month, skills in monthly_skill_counts.items():
        total_jobs = monthly_job_counts[month]
        for skill, count in skills.items():
            normalized = round((count / total_jobs) * 100, 2)
            cursor.execute('''
                INSERT INTO skill_mentions (skill, month, count, total_jobs, normalized_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (skill, month, count, total_jobs, normalized))

    conn.commit()

    cursor.execute('SELECT COUNT(*) FROM skill_mentions')
    total = cursor.fetchone()[0]
    print(f"{total} skill-month records saved.")

    cursor.execute('''
        SELECT skill, SUM(count) as total
        FROM skill_mentions
        GROUP BY skill
        ORDER BY total DESC
        LIMIT 10
    ''')
    print("\nTop 10 most mentioned skills:")
    for row in cursor.fetchall():
        print(f"  {row['skill']}: {row['total']} mentions")

    conn.close()
    print("\nExtraction complete!")

if __name__ == '__main__':
    extract_skills()