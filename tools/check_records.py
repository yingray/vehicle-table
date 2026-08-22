#!/usr/bin/env python3
"""Pre-merge gate for freshly researched vehicle records.

Research agents write one JSON file per vehicle. Run this against those files
BEFORE merging them into data/vehicles.json: a bad record is far cheaper to
reject on its own than to find inside a 149-element array.

validate.py checks the merged data file. This script checks the raw agent
output, and enforces the rules validate.py does not:

  - strict monotonic decrease of private_sale_price (METHODOLOGY requires it,
    validate.py never implemented it)
  - dealer_tradein_price below private_sale_price
  - derived fields absent (supplying them conflicts with validate.py --fix)
  - checkpoint years exactly [1, 3, 5, 7, 10] on both curves
  - assumed_km exactly 7000 * years
  - real_cost == list_price - discounts + onroad_fees
  - model and trim under 25 characters
  - sources[] present and non-empty

Usage: python3 tools/check_records.py <staging-dir>/*.json
"""
import json
import sys
from pathlib import Path

YEARS = [1, 3, 5, 7, 10]
DERIVED = ("retention_ratio", "depreciation_amount", "cumulative_cost", "cost_summary")
TOP_KEYS = {
    "id", "brand", "model", "trim", "model_year", "powertrain", "currency",
    "assumptions", "purchase", "selling_costs", "value_checkpoints",
    "maintenance", "sources", "updated_at",
}


def check(path):
    problems = []
    try:
        v = json.loads(Path(path).read_text())
    except Exception as e:
        return [f"{path}: not valid JSON: {e}"]

    vid = v.get("id", "<no id>")

    def bad(msg):
        problems.append(f"{vid}: {msg}")

    extra = set(v) - TOP_KEYS
    if extra:
        bad(f"unexpected top-level keys {sorted(extra)}")
    missing = TOP_KEYS - set(v)
    if missing:
        bad(f"missing top-level keys {sorted(missing)}")

    if Path(path).stem != vid:
        bad(f"id does not match filename {Path(path).stem}")

    for field in ("model", "trim"):
        if len(v.get(field, "")) >= 25:
            bad(f"{field} is {len(v[field])} chars, must be under 25: {v.get(field)!r}")

    p = v.get("purchase", {})
    expect = p.get("list_price", 0) - p.get("discounts", 0) + p.get("onroad_fees", 0)
    if abs(expect - p.get("real_cost", -1)) > 1:
        bad(f"real_cost={p.get('real_cost')} but list-discounts+fees={expect}")

    if not v.get("sources"):
        bad("sources[] is empty")

    vcs = v.get("value_checkpoints", [])
    if [c.get("years") for c in vcs] != YEARS:
        bad(f"value_checkpoints years {[c.get('years') for c in vcs]}, expected {YEARS}")
    prev = None
    for c in vcs:
        y = c.get("years")
        if c.get("assumed_km") != 7000 * y:
            bad(f"year {y} assumed_km={c.get('assumed_km')}, expected {7000 * y}")
        price = c.get("private_sale_price")
        if prev is not None and price >= prev:
            bad(f"year {y} private_sale_price={price} not below previous {prev}")
        prev = price
        tradein = c.get("dealer_tradein_price")
        if tradein is not None and tradein >= price:
            bad(f"year {y} dealer_tradein_price={tradein} not below private_sale={price}")
        for d in DERIVED:
            if d in c:
                bad(f"year {y} carries derived field {d}")

    mcs = v.get("maintenance", {}).get("checkpoints", [])
    if [c.get("years") for c in mcs] != YEARS:
        bad(f"maintenance years {[c.get('years') for c in mcs]}, expected {YEARS}")
    for c in mcs:
        y = c.get("years")
        if c.get("assumed_km") != 7000 * y:
            bad(f"maint year {y} assumed_km={c.get('assumed_km')}, expected {7000 * y}")
        if not c.get("period_cost"):
            bad(f"maint year {y} period_cost is zero or missing")
        for d in DERIVED:
            if d in c:
                bad(f"maint year {y} carries derived field {d}")

    for d in DERIVED:
        if d in v:
            bad(f"carries top-level derived field {d}")

    return problems


def main():
    paths = [a for a in sys.argv[1:] if a.endswith(".json")]
    if not paths:
        print(__doc__)
        sys.exit(2)
    all_problems = []
    for path in sorted(paths):
        all_problems += check(path)
    for problem in all_problems:
        print(f"FAIL  {problem}")
    print(f"\n{len(paths)} records checked, {len(all_problems)} problems")
    sys.exit(1 if all_problems else 0)


if __name__ == "__main__":
    main()
