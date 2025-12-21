"""Backfill candidate `position` column.

Usage:
- Provide a CSV at `data/candidate_positions.csv` with columns `candidate_id,position` or `full_name,position` to map values.
- If the CSV is missing, the script will set position='Candidate' for all rows where position is NULL/empty.

Run: python scripts/backfill_candidate_positions.py
"""
import csv
import os
from Models.base import get_session, init_db
from Models.model_candidate import Candidate


def load_csv(path):
    mappings = {}
    by_name = {}
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                if 'candidate_id' in r and r.get('candidate_id'):
                    try:
                        cid = int(r['candidate_id'])
                        mappings[cid] = r.get('position') or r.get('position','').strip() or None
                    except Exception:
                        continue
                elif 'full_name' in r and r.get('full_name'):
                    by_name[r['full_name'].strip()] = r.get('position') or r.get('position','').strip() or None
    except FileNotFoundError:
        return None, None
    return mappings, by_name


def backfill_from_csv(session, csv_path):
    by_id, by_name = load_csv(csv_path)
    if by_id is None and by_name is None:
        return 0

    updated = 0
    candidates = session.query(Candidate).filter((Candidate.position == None) | (Candidate.position == '')).all()
    for c in candidates:
        new_pos = None
        if by_id and c.candidate_id in by_id:
            new_pos = by_id[c.candidate_id]
        elif by_name and c.full_name and c.full_name.strip() in by_name:
            new_pos = by_name[c.full_name.strip()]

        if new_pos:
            c.position = new_pos
            updated += 1

    if updated:
        session.commit()
    return updated


def backfill_default(session, default='Candidate'):
    candidates = session.query(Candidate).filter((Candidate.position == None) | (Candidate.position == '')).all()
    count = 0
    for c in candidates:
        c.position = default
        count += 1
    if count:
        session.commit()
    return count


def ensure_sample_csv(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        return
    sample = [
        {'candidate_id': '', 'full_name': 'Jared Busanon', 'position': 'President'},
        {'candidate_id': '', 'full_name': 'Bea Alonzo', 'position': 'Vice President'},
    ]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['candidate_id', 'full_name', 'position'])
        writer.writeheader()
        for r in sample:
            writer.writerow(r)


def main():
    init_db()
    session = get_session()
    try:
        csv_path = os.path.join('data', 'candidate_positions.csv')
        updated = 0
        if os.path.exists(csv_path):
            print('Found CSV mapping at', csv_path)
            updated = backfill_from_csv(session, csv_path)
            print(f'Updated {updated} positions from CSV')
        else:
            # create sample CSV for user to edit
            ensure_sample_csv(csv_path)
            updated = backfill_default(session, default='Candidate')
            print('No CSV mapping found; set default position for', updated, 'candidates')

        if updated == 0:
            print('No missing positions found or nothing updated.')
    finally:
        session.close()


if __name__ == '__main__':
    main()
