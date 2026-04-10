import requests
from bs4 import BeautifulSoup
import sqlite3
import os
import time
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'skillsight.db')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

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

def scrape_naukri(pages=10):
    print("Starting Naukri scrape...")
    jobs = []

    for page in range(0, pages):
        url = f"https://www.naukri.com/it-jobs-{page}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            job_cards = soup.find_all('article', class_='jobTuple')
            if not job_cards:
                job_cards = soup.find_all('div', class_='job-container')
            if not job_cards:
                job_cards = soup.find_all('div', {'class': lambda x: x and 'job' in x.lower()})

            for card in job_cards:
                try:
                    title = card.find(['a', 'h2', 'h3'])
                    title = title.text.strip() if title else 'N/A'

                    company = card.find(class_=lambda x: x and 'company' in str(x).lower())
                    company = company.text.strip() if company else 'N/A'

                    desc = card.get_text(separator=' ', strip=True)

                    jobs.append({
                        'title': title,
                        'company': company,
                        'description': desc,
                        'source': 'naukri'
                    })
                except:
                    continue

            print(f"Page {page+1} scraped — {len(job_cards)} jobs found")
            time.sleep(random.uniform(1.5, 3.0))

        except Exception as e:
            print(f"Page {page+1} failed: {e}")
            continue

    return jobs

def generate_simulated_jobs(count=500):
    print(f"Generating {count} simulated job records...")
    jobs = []

    job_titles = [
        'Software Engineer', 'Senior Developer', 'Full Stack Developer',
        'Data Scientist', 'ML Engineer', 'DevOps Engineer',
        'Backend Developer', 'Frontend Developer', 'Cloud Architect',
        'Data Analyst', 'AI Engineer', 'Platform Engineer'
    ]

    companies = [
        'TCS', 'Infosys', 'Wipro', 'HCL', 'Tech Mahindra',
        'Accenture', 'Cognizant', 'IBM', 'Capgemini', 'LTIMindtree',
        'Mphasis', 'Hexaware', 'Persistent Systems', 'KPIT', 'Birlasoft'
    ]

    skill_weights = {
        'Python': 0.85, 'JavaScript': 0.80, 'React': 0.75, 'AWS': 0.78,
        'Docker': 0.70, 'Machine Learning': 0.72, 'Node.js': 0.65,
        'TypeScript': 0.68, 'Kubernetes': 0.62, 'FastAPI': 0.55,
        'NLP': 0.50, 'PyTorch': 0.52, 'TensorFlow': 0.54, 'Go': 0.48,
        'Rust': 0.30, 'Flutter': 0.45, 'React Native': 0.48,
        'Java': 0.75, 'Spring Boot': 0.65, 'Microservices': 0.60,
        'MySQL': 0.65, 'PostgreSQL': 0.60, 'MongoDB': 0.55,
        'Angular': 0.50, 'Vue': 0.42, 'GraphQL': 0.45,
        'Kafka': 0.40, 'Spark': 0.42, 'Hadoop': 0.25,
        'Tableau': 0.45, 'Power BI': 0.50, 'DevOps': 0.65,
        'Git': 0.80, 'Linux': 0.70, 'REST API': 0.72,
        'jQuery': 0.20, 'PHP': 0.22, 'Ruby': 0.18,
        'Excel': 0.55, 'Terraform': 0.48, 'Jenkins': 0.45,
        'GCP': 0.45, 'Azure': 0.60, 'Redis': 0.45,
        'C++': 0.40, 'C#': 0.42, 'Swift': 0.30, 'Kotlin': 0.38,
        'Deep Learning': 0.55, 'Computer Vision': 0.45, 'Scikit-learn': 0.50,
        'Pandas': 0.60, 'NumPy': 0.58, 'Cassandra': 0.20
    }

    for i in range(count):
        days_ago = random.randint(0, 365)
        job_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m')

        selected_skills = [
            skill for skill, weight in skill_weights.items()
            if random.random() < weight
        ]

        desc = f"We are looking for a skilled professional. Required skills: {', '.join(selected_skills)}. Experience in {random.choice(selected_skills)} is mandatory."

        jobs.append({
            'title': random.choice(job_titles),
            'company': random.choice(companies),
            'description': desc,
            'source': 'simulated',
            'date': job_date
        })

    print(f"{count} simulated jobs generated.")
    return jobs

def save_jobs(jobs):
    conn = get_connection()
    cursor = conn.cursor()
    saved = 0

    for job in jobs:
        date = job.get('date', datetime.now().strftime('%Y-%m'))
        cursor.execute('''
            INSERT INTO job_postings (title, company, location, description, source, date_scraped)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            job.get('title', 'N/A'),
            job.get('company', 'N/A'),
            job.get('location', 'India'),
            job.get('description', ''),
            job.get('source', 'unknown'),
            date
        ))
        saved += 1

    conn.commit()
    conn.close()
    print(f"{saved} jobs saved to database.")

if __name__ == '__main__':
    print("=== SkillSight Scraper ===")
    print("Attempting live scrape from Naukri...")
    live_jobs = scrape_naukri(pages=5)

    if len(live_jobs) < 50:
        print(f"Live scrape got only {len(live_jobs)} jobs. Switching to simulated data...")
        sim_jobs = generate_simulated_jobs(500)
        save_jobs(sim_jobs)
    else:
        save_jobs(live_jobs)

    print("Scraping complete!")