#!/usr/bin/env python3
"""Validate a vehicle-table data file and recheck all DERIVED fields.

The schema (schema/vehicle.schema.json) defines the shape; this script
enforces the arithmetic rules the schema cannot express:

  - checkpoint years are unique and ascending
  - retention_ratio      = private_sale_price / purchase.real_cost
  - depreciation_amount  = purchase.real_cost - private_sale_price
  - cumulative_cost      = running sum of period_cost
  - assumed_km sits inside years * [annual_km_low, annual_km_high] (warning)
  - cost_summary         = depreciation + cumulative maintenance + selling costs

Usage:
  python3 validate.py data/vehicles.json          # report problems, exit 1 if any error
  python3 validate.py data/vehicles.json --fix    # rewrite derived fields in place

If the `jsonschema` package is installed, the file is also validated
against the JSON Schema; otherwise that step is skipped with a note.
"""
import json
import sys
from pathlib import Path

TOL_RATIO = 0.005   # tolerance for retention_ratio comparison
TOL_MONEY = 1       # tolerance for money comparison

errors = []
warnings = []


def check(vehicle, fix):
    vid = vehicle.get("id", "<no id>")
    real_cost = vehicle["purchase"]["real_cost"]
    low = vehicle["assumptions"]["annual_km_low"]
    high = vehicle["assumptions"]["annual_km_high"]
    sell_cost = vehicle.get("selling_costs", {}).get("total", 0)

    # purchase arithmetic (warning only: user may enter real_cost directly)
    p = vehicle["purchase"]
    if "discounts" in p or "onroad_fees" in p:
        expect = p["list_price"] - p.get("discounts", 0) + p.get("onroad_fees", 0)
        if abs(expect - real_cost) > TOL_MONEY:
            warnings.append(f"{vid}: purchase.real_cost={real_cost} but list-discounts+fees={expect}")

    # value checkpoints
    vcs = vehicle["value_checkpoints"]
    years_seen = [c["years"] for c in vcs]
    if years_seen != sorted(set(years_seen)):
        errors.append(f"{vid}: value_checkpoints years must be unique and ascending, got {years_seen}")
    dep_by_year = {}
    for c in vcs:
        y = c["years"]
        if not (y * low <= c["assumed_km"] <= y * high):
            warnings.append(
                f"{vid}: year {y} assumed_km={c['assumed_km']} outside {y * low}-{y * high}"
            )
        ratio = round(c["private_sale_price"] / real_cost, 3)
        dep = real_cost - c["private_sale_price"]
        dep_by_year[y] = dep
        if fix:
            c["retention_ratio"], c["depreciation_amount"] = ratio, dep
        else:
            if abs(c.get("retention_ratio", ratio) - ratio) > TOL_RATIO:
                errors.append(f"{vid}: year {y} retention_ratio={c.get('retention_ratio')} expected {ratio}")
            if abs(c.get("depreciation_amount", dep) - dep) > TOL_MONEY:
                errors.append(f"{vid}: year {y} depreciation_amount={c.get('depreciation_amount')} expected {dep}")

    # maintenance cumulative
    mcs = vehicle["maintenance"]["checkpoints"]
    myears = [c["years"] for c in mcs]
    if myears != sorted(set(myears)):
        errors.append(f"{vid}: maintenance years must be unique and ascending, got {myears}")
    running = 0
    cum_by_year = {}
    for c in mcs:
        running += c["period_cost"]
        cum_by_year[c["years"]] = running
        if fix:
            c["cumulative_cost"] = running
        elif abs(c.get("cumulative_cost", running) - running) > TOL_MONEY:
            errors.append(f"{vid}: year {c['years']} cumulative_cost={c.get('cumulative_cost')} expected {running}")

    # cost summary (only for years present in BOTH curves)
    common = [y for y in dep_by_year if y in cum_by_year]
    expect_summary = []
    for y in common:
        total = dep_by_year[y] + cum_by_year[y] + sell_cost
        km = y * (low + high) // 2
        expect_summary.append({
            "years": y,
            "total_cost": total,
            "cost_per_year": round(total / y),
            "cost_per_km": round(total / km, 2),
        })
    if fix:
        vehicle["cost_summary"] = expect_summary
    else:
        got = vehicle.get("cost_summary", [])
        if len(got) != len(expect_summary):
            errors.append(f"{vid}: cost_summary has {len(got)} rows, expected {len(expect_summary)}")
        else:
            for g, e in zip(got, expect_summary):
                if g["years"] != e["years"] or abs(g["total_cost"] - e["total_cost"]) > TOL_MONEY:
                    errors.append(f"{vid}: cost_summary year {g['years']} total={g['total_cost']} expected {e['total_cost']}")


def main():
    args = [a for a in sys.argv[1:] if a != "--fix"]
    fix = "--fix" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(2)
    path = Path(args[0])
    data = json.loads(path.read_text())

    schema_path = Path(__file__).parent / "schema" / "vehicle.schema.json"
    try:
        import jsonschema
        jsonschema.validate(data, json.loads(schema_path.read_text()))
        print("schema: OK")
    except ImportError:
        print("schema: skipped (pip install jsonschema to enable)")
    except Exception as e:  # jsonschema.ValidationError
        errors.append(f"schema: {e}")

    for vehicle in data:
        check(vehicle, fix)

    if fix:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"fixed: derived fields rewritten in {path}")
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if not warnings and not errors:
        print("derived fields: OK")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
