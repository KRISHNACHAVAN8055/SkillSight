from scraper.adzuna_client import fetch_adzuna_jobs
from scraper.scraper import save_jobs
from scraper.extractor import extract_skills
from models.predictor import run_predictions

print("=== Fetching real job data from Adzuna ===")
jobs = fetch_adzuna_jobs(pages_per_term=2)

if len(jobs) < 50:
    print(f"WARNING: Only {len(jobs)} jobs fetched. Check API credentials or network.")
else:
    print(f"\n=== Saving {len(jobs)} real jobs to database ===")
    save_jobs(jobs)

    print("\n=== Re-extracting skills from real data ===")
    extract_skills()

    print("\n=== Re-running predictions on real data ===")
    run_predictions()

    print("\n=== Done. Database now reflects real job market data. ===")
