import requests
import os
from datetime import datetime

APP_ID = os.environ.get('ADZUNA_APP_ID')
APP_KEY = os.environ.get('ADZUNA_APP_KEY')

BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search"

SEARCH_TERMS = [
    'software developer',
    'data scientist',
    'devops engineer',
    'full stack developer',
    'machine learning engineer',
    'backend developer',
    'frontend developer',
    'cloud engineer'
]

def fetch_adzuna_jobs(pages_per_term=2, results_per_page=50):
    if not APP_ID or not APP_KEY:
        print("Adzuna credentials not set. Skipping live fetch.")
        return []

    all_jobs = []
    for term in SEARCH_TERMS:
        for page in range(1, pages_per_term + 1):
            params = {
                'app_id': APP_ID,
                'app_key': APP_KEY,
                'results_per_page': results_per_page,
                'what': term,
                'content-type': 'application/json'
            }
            try:
                response = requests.get(f"{BASE_URL}/{page}", params=params, timeout=15)
                response.raise_for_status()
                data = response.json()

                results = data.get('results', [])
                for job in results:
                    all_jobs.append({
                        'title': job.get('title', 'N/A'),
                        'company': job.get('company', {}).get('display_name', 'N/A'),
                        'location': job.get('location', {}).get('display_name', 'India'),
                        'description': job.get('description', ''),
                        'source': 'adzuna',
                        'date': datetime.now().strftime('%Y-%m')
                    })

                print(f"'{term}' page {page}: {len(results)} jobs fetched")

                if len(results) < results_per_page:
                    break

            except requests.exceptions.RequestException as e:
                print(f"'{term}' page {page} failed: {e}")
                continue

    print(f"\nTotal Adzuna jobs fetched: {len(all_jobs)}")
    return all_jobs

if __name__ == '__main__':
    jobs = fetch_adzuna_jobs(pages_per_term=2)
    print(f"\nSample job:\n{jobs[0] if jobs else 'No jobs fetched'}")
