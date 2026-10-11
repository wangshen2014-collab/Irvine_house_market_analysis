"""Audit a supplied transaction trial without inferring unavailable fields."""
import argparse
import csv
import json
import sys
from pathlib import Path

REQUIRED = ['record_id', 'address', 'city', 'community', 'close_date', 'sale_price', 'bedrooms', 'living_area_sqft', 'year_built', 'legal_property_type', 'shared_wall_status', 'source_id', 'source_url', 'retrieved_at', 'redistribution_status']
OPTIONAL = ['apn', 'contract_date', 'listing_date', 'complete_listing_history', 'seller_concession', 'financing_evidence', 'hoa_monthly', 'mello_roos_annual', 'comparable_rent']


def audit(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not set(REQUIRED + OPTIONAL).issubset(reader.fieldnames or []):
            raise ValueError('Template columns missing')
        rows = list(reader)
    failures = []
    warnings = []
    if not 20 <= len(rows) <= 30:
        failures.append('Trial target is 20–30 transactions; this is a field feasibility target, not statistical sufficiency.')
    ids = [r['record_id'].strip() for r in rows]
    if any(not i for i in ids) or len(set(ids)) != len(ids):
        failures.append('Missing or duplicate record_id')
    address_date = [(r['address'].strip().casefold(), r['close_date'].strip()) for r in rows]
    if len(set(address_date)) != len(rows):
        failures.append('Duplicate address/close-date requires manual reconciliation')
    unknown = {'', 'unknown', 'pending', 'not_available', 'unverified'}
    coverage = {c: {'observed': sum(r[c].strip().casefold() not in unknown for r in rows), 'denominator': len(rows)} for c in REQUIRED + OPTIONAL}
    communities = sorted({r['community'].strip() for r in rows if r['community'].strip().casefold() not in unknown})
    if len(communities) < 3:
        warnings.append('Fewer than 3 verified communities; sample breadth not established.')
    for i, r in enumerate(rows, 2):
        if r['redistribution_status'] not in ['approved', 'link_only', 'restricted', 'pending']:
            failures.append(f'Row {i}: unrecognized redistribution_status')
        for c in ['sale_price', 'bedrooms', 'living_area_sqft', 'year_built']:
            if r[c].strip().casefold() in unknown:
                continue
            try:
                if float(r[c]) <= 0:
                    failures.append(f'Row {i}: nonpositive {c}')
            except ValueError:
                failures.append(f'Row {i}: invalid numeric {c}')
    # Coverage is reported even when imperfect. Acceptance still needs manual source/geography checks.
    warnings.append('Manual checks required: at least 5 records, community/legal form/no shared wall, relisting history and provenance; the script cannot certify these.')
    result = {'status': 'needs_review' if not failures else 'incomplete_or_invalid', 'transaction_count': len(rows),
              'communities': communities, 'field_coverage': coverage, 'failures': failures, 'warnings': warnings,
              'manual_acceptance': 'not_certified', 'missing_is_zero': False}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    sys.exit(audit(args.input))
