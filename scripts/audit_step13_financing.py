#!/usr/bin/env python3
"""Limited step-13 check: solve payments by balance iteration and bisection.

Does not import or run the production build/audit scripts. All prices and loans
are synthetic. Passing arithmetic never opens the step-12/A integration gate.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from functools import lru_cache
from pathlib import Path

getcontext().prec = 44
ROOT = Path(__file__).resolve().parents[1]
D = Decimal


def balance_after(principal, rate, payment, months):
    balance, interest_total = principal, D(0)
    for _ in range(months):
        interest = balance * rate / D(1200)
        interest_total += interest
        balance += interest - payment
    return balance, interest_total


@lru_cache(maxsize=None)
def payment_for(principal, rate, months):
    """Root of terminal balance, without the annuity closed-form expression."""
    low, high = D(0), principal * (1 + rate / D(1200))
    for _ in range(160):
        middle = (low + high) / 2
        balance, _ = balance_after(principal, rate, middle, months)
        if balance > 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def table(name):
    with (ROOT / 'data/clean' / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--evidence-dir', type=Path)
    ap.add_argument('--out', type=Path, default=ROOT / 'qa/step13_financing_independent.json')
    args = ap.parse_args()
    design = json.loads((ROOT / 'data/scenario_analysis_design.json').read_text())
    checks = []

    def check(family, row, field, actual, expected):
        error = abs(actual - D(str(expected)))
        checks.append(dict(family=family, row=row, field=field,
                           recomputed=float(actual), recorded=float(expected),
                           absolute_error=float(error), tolerance=0.000001,
                           passed=error <= D('0.000001')))

    principal = D(str(design['loan_math']['normalization_principal_usd']))
    rate0 = D(str(design['loan_math']['fixed_rate_pct']))
    fixed_payment = payment_for(principal, rate0, 360)
    p0 = D(str(design['payment_sensitivity']['initial_price_index']))
    d = D(str(design['payment_sensitivity']['initial_down_fraction']))
    rows = table('scenario_equal_payment_boundaries.csv')
    for row in rows:
        rate = D(row['rate_pct'])
        pay = payment_for(principal, rate, 360)
        ratio = fixed_payment / pay
        check('equal_payment', row['rate_pct'], 'PI_per_100k', pay, row['PI_per_100k'])
        check('equal_payment', row['rate_pct'], 'fixed_cash_equal_PI_price_index',
              p0 * d + p0 * (1 - d) * ratio, row['fixed_cash_equal_PI_price_index'])
        check('equal_payment', row['rate_pct'], 'fixed_fraction_equal_PI_price_index',
              p0 * ratio, row['fixed_fraction_equal_PI_price_index'])

    low_rate = D(str(design['loan_math']['points_lower_rate_pct']))
    point_cost = principal * D(str(design['loan_math']['points_fraction']))
    low_payment = payment_for(principal, low_rate, 360)
    savings = fixed_payment - low_payment
    for row in table('scenario_points.csv'):
        n = int(row['months'])
        old_b, old_i = balance_after(principal, rate0, fixed_payment, n)
        new_b, new_i = balance_after(principal, low_rate, low_payment, n)
        values = {'monthly_PI_saving': savings, 'cash_saving_net_cost': n*savings-point_cost,
                  'remaining_balance_saving': old_b-new_b,
                  'interest_saving_net_cost': old_i-new_i-point_cost}
        for key, value in values.items():
            check('points', n, key, value, row[key])
    interest_break_even = next(n for n in range(1, 361)
                              if balance_after(principal, rate0, fixed_payment, n)[1]
                              - balance_after(principal, low_rate, low_payment, n)[1] >= point_cost)

    initial = D(str(design['loan_math']['arm_initial_rate_pct']))
    cap_first, cap_later, cap_life = map(lambda v: D(str(v)), design['loan_math']['arm_caps_pp'])
    arm_balance, rate, paid, interest_total = principal, initial, D(0), D(0)
    pay = payment_for(principal, rate, 360)
    arm_rows = {int(r['month']): r for r in table('scenario_arm_cap_stress.csv')}
    for month in range(1, 361):
        if month == 61 or (month > 61 and (month - 61) % 12 == 0):
            rate = min(initial + cap_life, rate + (cap_first if month == 61 else cap_later))
            pay = payment_for(arm_balance, rate, 361-month)
        interest = arm_balance * rate / 1200
        arm_balance += interest - pay
        interest_total += interest
        paid += pay
        if month in arm_rows:
            row = arm_rows[month]
            for key, value in {'rate_pct': rate, 'payment': pay, 'balance': arm_balance,
                               'cumulative_payments': paid, 'cumulative_interest': interest_total}.items():
                check('arm', month, key, value, row[key])

    refinance_at = int(design['loan_math']['refinance_at_month'])
    remaining, _ = balance_after(principal, rate0, fixed_payment, refinance_at)
    fee = remaining * D(str(design['loan_math']['refinance_cost_fraction']))
    nr = D(str(design['loan_math']['refinance_rate_pct']))
    future_interest = {}
    for row in table('scenario_refinance.csv'):
        term, after = int(row['new_term_months']), int(row['months_after_refi'])
        new_payment = payment_for(remaining, nr, term)
        new_b, new_i = balance_after(remaining, nr, new_payment, after)
        old_b, old_i = balance_after(remaining, rate0, fixed_payment, after)
        future_interest[term] = balance_after(remaining, nr, new_payment, term)[1]
        values = {'refi_balance': remaining, 'upfront_cash_fee': fee,
                  'old_payment': fixed_payment, 'new_payment': new_payment,
                  'cash_saving_net_cost': (fixed_payment-new_payment)*after-fee,
                  'interest_saving_net_cost': old_i-new_i-fee,
                  'remaining_balance_extra': new_b-old_b,
                  'new_lifetime_interest': future_interest[term],
                  'old_remaining_lifetime_interest': balance_after(remaining, rate0, fixed_payment, 360-refinance_at)[1]}
        for key, value in values.items():
            check('refinance', f'{term}/{after}', key, value, row[key])

    source_hashes = []
    if args.evidence_dir:
        selected = {'JS-01', 'JS-02', 'JS-06', 'JS-29'}
        with (ROOT/'data/scenario_source_index.csv').open(newline='') as f:
            for row in csv.DictReader(f):
                if row['evidence_id'] in selected:
                    actual = hashlib.sha256((args.evidence_dir/row['path']).read_bytes()).hexdigest()
                    source_hashes.append(dict(evidence_id=row['evidence_id'], source_url=row['source_url'],
                                              sha256=actual, matches_manifest=actual == row['sha256']))

    result = dict(audit_scope='step11 synthetic financing only; step12 absent',
                  audited_commit='ff33e18ce3e781dccf5194331561c97c71285a97',
                  generated_at_utc=datetime.now(timezone.utc).isoformat(),
                  method='44-digit Decimal; monthly balance iteration; bisection to zero terminal balance; no production imports',
                  passed=all(c['passed'] for c in checks) and all(c['matches_manifest'] for c in source_hashes),
                  checks=checks, source_hashes=source_hashes,
                  summary=dict(families=['equal_payment', 'points', 'arm', 'refinance'],
                               comparison_count=len(checks), max_absolute_error=max(c['absolute_error'] for c in checks),
                               fixed_payment_per_100k=float(fixed_payment), points_monthly_saving=float(savings),
                               points_simple_cash_months=float(point_cost/savings),
                               points_interest_break_even_month=interest_break_even,
                               refinance_initial_balance=float(remaining),
                               extended_term_extra_interest=float(future_interest[360]-future_interest[324])),
                  step12_completed=False, full_step13_completed=False, eligible_for_A_C_integration=False,
                  limitations=['Synthetic inputs, not personal loan eligibility',
                               'No market equilibrium price or buy-rent break-even',
                               'No tax, discounting, prepaid interest, real closing-cost or insurance audit',
                               ('Four frozen HTML source hashes checked in this run; remaining domain originals not audited'
                                if args.evidence_dir else 'No raw source hashes checked in this run; arithmetic only')])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['passed', 'summary', 'source_hashes', 'eligible_for_A_C_integration']}, ensure_ascii=False, indent=2))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
