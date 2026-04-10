import sqlite3
import os
import json
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'skillsight.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_skills():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT skill FROM skill_mentions')
    skills = [row['skill'] for row in cursor.fetchall()]
    conn.close()
    return skills

def get_skill_trend(skill):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT month, normalized_count
        FROM skill_mentions
        WHERE skill = ?
        ORDER BY month ASC
    ''', (skill,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def compute_obsolescence_score(slope, max_slope=5.0):
    normalized = max(-1, min(1, slope / max_slope))
    score = round((1 - normalized) * 50, 2)
    return max(0, min(100, score))

def classify_skill(score):
    if score < 35:
        return 'Rising'
    elif score < 50:
        return 'Stable'
    elif score < 70:
        return 'Declining'
    else:
        return 'Critical'

def predict_skill(skill):
    rows = get_skill_trend(skill)

    if len(rows) < 3:
        return None

    months = [row['month'] for row in rows]
    counts = [row['normalized_count'] for row in rows]

    X = np.array(range(len(counts))).reshape(-1, 1)
    y = np.array(counts)

    model = LinearRegression()
    model.fit(X, y)

    slope = round(model.coef_[0], 4)

    last_index = len(counts)
    future_X = np.array(range(last_index, last_index + 6)).reshape(-1, 1)
    forecast_values = model.predict(future_X)
    forecast_values = [round(max(0, v), 2) for v in forecast_values]

    last_month = months[-1]
    year, month = map(int, last_month.split('-'))
    forecast_months = []
    for i in range(1, 7):
        m = month + i
        y_offset = (m - 1) // 12
        m = ((m - 1) % 12) + 1
        forecast_months.append(f"{year + y_offset}-{m:02d}")

    forecast = dict(zip(forecast_months, forecast_values))

    score = compute_obsolescence_score(slope)
    category = classify_skill(score)

    return {
        'skill': skill,
        'slope': slope,
        'obsolescence_score': score,
        'category': category,
        'historical_months': months,
        'historical_counts': counts,
        'forecast': forecast
    }

def run_predictions():
    print("=== SkillSight Predictor ===")
    skills = get_all_skills()
    print(f"Running predictions for {len(skills)} skills...")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM skill_forecasts')

    results = []
    for skill in skills:
        result = predict_skill(skill)
        if result:
            cursor.execute('''
                INSERT INTO skill_forecasts (skill, slope, obsolescence_score, category, forecast_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                result['skill'],
                result['slope'],
                result['obsolescence_score'],
                result['category'],
                json.dumps(result['forecast'])
            ))
            results.append(result)

    conn.commit()
    conn.close()

    print(f"\nPredictions complete for {len(results)} skills.")
    print("\n--- Category Breakdown ---")
    for cat in ['Rising', 'Stable', 'Declining', 'Critical']:
        count = sum(1 for r in results if r['category'] == cat)
        print(f"  {cat}: {count} skills")

    print("\n--- Top 5 Rising Skills ---")
    rising = sorted([r for r in results if r['category'] == 'Rising'],
                    key=lambda x: x['obsolescence_score'])
    for r in rising[:5]:
        print(f"  {r['skill']} — Score: {r['obsolescence_score']}")

    print("\n--- Top 5 Critical Skills ---")
    critical = sorted([r for r in results if r['category'] == 'Critical'],
                      key=lambda x: x['obsolescence_score'], reverse=True)
    for r in critical[:5]:
        print(f"  {r['skill']} — Score: {r['obsolescence_score']}")

    print("\nAll predictions saved to database.")

if __name__ == '__main__':
    run_predictions()