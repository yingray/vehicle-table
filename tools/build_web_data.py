#!/usr/bin/env python3
"""Build the browser data files for index.html from data/vehicles.json.

The source file is ~3.7 MB because every estimate carries a long provenance
note. The page only needs a small subset to draw the ranking, the table and the
charts, so this script splits the data in two:

  web/car-data.js    compact records, loaded on first paint
  web/car-detail.js  provenance text, imported only when a detail panel opens

Run it after every change to data/vehicles.json:

    python3 tools/build_web_data.py

Two fields the page needs do not exist in the schema and are derived here:
`body` (車體型式) comes from an explicit model table, and `band` (價格帶) comes
from real_cost. The model table is explicit on purpose — a new model must be
classified by a person, so an unknown model stops the build.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "vehicles.json"
OUT_DIR = ROOT / "web"

# 車體型式. The ranking page groups by these five values only, so a coupé that
# is really a sports car goes to 跑車 and a tall hatch that is really a people
# mover goes to MPV. Keyed by the exact `model` field.
BODY_BY_MODEL = {
    # SUV
    "RAV4": "SUV",
    "bZ4X": "SUV",
    "Urban Cruiser": "SUV",
    "Land Cruiser": "SUV",
    "NX200": "SUV",
    "NX350": "SUV",
    "NX350h": "SUV",
    "NX450h+": "SUV",
    "RX350": "SUV",
    "RX350h": "SUV",
    "RX450h+": "SUV",
    "RX500h": "SUV",
    "Tiguan": "SUV",
    "GLC200": "SUV",
    "GLA": "SUV",
    "GLB": "SUV",
    "GLE": "SUV",
    "EQA": "SUV",
    "EQB": "SUV",
    "EQE SUV": "SUV",
    "X1": "SUV",
    "X2": "SUV",
    "X3": "SUV",
    "X5": "SUV",
    "X6": "SUV",
    "iX": "SUV",
    "iX1": "SUV",
    "iX2": "SUV",
    "iX3": "SUV",
    "Q2": "SUV",
    "Q3": "SUV",
    "Q4 e-tron": "SUV",
    "Q5": "SUV",
    "Q6 e-tron": "SUV",
    "Q7": "SUV",
    "Q8": "SUV",
    "XC40": "SUV",
    "XC60": "SUV",
    "XC90": "SUV",
    "EX30": "SUV",
    "EX40": "SUV",
    "EC40": "SUV",
    "EX90": "SUV",
    "Cayenne": "SUV",
    "Model Y": "SUV",
    "Model X": "SUV",
    "Range Rover Evoque": "SUV",
    "Range Rover Velar": "SUV",
    "Range Rover Sport": "SUV",
    "Range Rover": "SUV",
    # 房車
    "ES300h": "房車",
    "ES500e": "房車",
    "IS300h": "房車",
    "LS500h": "房車",
    "Camry": "房車",
    "Crown": "房車",
    "Prius PHEV": "房車",
    "Model 3": "房車",
    "Model S": "房車",
    "A3 Sportback": "房車",
    "A5": "房車",
    "A6": "房車",
    "A6 e-tron": "房車",
    "A7 Sportback": "房車",
    "A8": "房車",
    "1 Series": "房車",
    "2 Series Gran Coupé": "房車",
    "3 Series": "房車",
    "5 Series": "房車",
    "7 Series": "房車",
    "i4": "房車",
    "i5": "房車",
    "A-Class": "房車",
    "C-Class": "房車",
    "CLA": "房車",
    "E-Class": "房車",
    "EQE": "房車",
    "S-Class": "房車",
    "EQS": "房車",
    # 旅行車
    "V60": "旅行車",
    "C-Class Estate": "旅行車",
    "E-Class Estate": "旅行車",
    "CLA Shooting Brake": "旅行車",
    "3 Series Touring": "旅行車",
    "5 Series Touring": "旅行車",
    "i5 Touring": "旅行車",
    "A5 Avant": "旅行車",
    "A6 Avant": "旅行車",
    "A6 Avant e-tron": "旅行車",
    # MPV
    "Alphard": "MPV",
    "Sienna": "MPV",
    "LM350h": "MPV",
    "Multivan": "MPV",
    "V250d": "MPV",
    "B-Class": "MPV",
    "2 Series Active Tourer": "MPV",
    # 跑車
    "GR86": "跑車",
    "GR Yaris": "跑車",
    "GR Supra": "跑車",
    "2 Series Coupé": "跑車",
    "4 Series": "跑車",
    "CLE": "跑車",
    "Z4": "跑車",
}

POWERTRAIN_LABEL = {
    "gasoline": "汽油",
    "diesel": "柴油",
    "hybrid": "油電",
    "phev": "插電油電",
    "bev": "純電",
}

# 價格帶, cut on real_cost (what the buyer actually pays), not on list price.
PRICE_BANDS = [
    (1_000_000, "100萬以下"),
    (2_000_000, "100–200萬"),
    (3_000_000, "200–300萬"),
    (4_000_000, "300–400萬"),
]
TOP_BAND = "400萬以上"


def band_of(real_cost: int) -> str:
    for ceiling, label in PRICE_BANDS:
        if real_cost < ceiling:
            return label
    return TOP_BAND


def body_of(model: str) -> str:
    try:
        return BODY_BY_MODEL[model]
    except KeyError:
        raise SystemExit(
            f"unknown model {model!r}: add it to BODY_BY_MODEL in {Path(__file__).name}"
        )


def powertrain_of(powertrain: str) -> str:
    try:
        return POWERTRAIN_LABEL[powertrain]
    except KeyError:
        raise SystemExit(f"unknown powertrain {powertrain!r}")


def compact(car: dict) -> dict:
    """One car, reduced to what the page draws."""
    purchase = car["purchase"]
    real = purchase["real_cost"]
    sell = car["selling_costs"]["total"]
    maintenance = {m["years"]: m for m in car["maintenance"]["checkpoints"]}

    checkpoints = []
    for point in car["value_checkpoints"]:
        years = point["years"]
        maint = maintenance[years]
        private = point["private_sale_price"]
        trade = point["dealer_tradein_price"]
        cumulative = maint["cumulative_cost"]
        checkpoints.append(
            {
                "y": years,
                "km": point["assumed_km"],
                "resalePriv": private,
                "resaleTrade": trade,
                # 自售 carries the selling costs; 車商收購 does not, because the
                # dealer handles the transfer in one go.
                "costPriv": real - private + cumulative + sell,
                "costTrade": real - trade + cumulative,
                "maintCum": cumulative,
                "maintPeriod": maint["period_cost"],
                "conf": point["confidence"],
                "items": maint["major_items"],
            }
        )

    return {
        "id": car["id"],
        "brand": car["brand"],
        "model": car["model"],
        "trim": car["trim"],
        "year": car["model_year"],
        "pt": powertrain_of(car["powertrain"]),
        "body": body_of(car["model"]),
        "band": band_of(real),
        "list": purchase["list_price"],
        "disc": purchase["discounts"],
        "fees": purchase["onroad_fees"],
        "real": real,
        "sell": sell,
        "cps": checkpoints,
    }


def detail(car: dict) -> dict:
    """One car, reduced to the provenance the detail panel shows."""
    return {
        "assumptions": car["assumptions"]["notes"],
        "cpSources": [
            {
                "y": point["years"],
                "conf": point["confidence"],
                "as_of": point["as_of"],
                "source": point["source"],
            }
            for point in car["value_checkpoints"]
        ],
        "maintSources": [
            {"y": point["years"], "source": point["source"]}
            for point in car["maintenance"]["checkpoints"]
        ],
        # The schema makes `url` optional, and a record that names a source it
        # could not open honestly leaves it out. Render those as plain text.
        "sources": [
            {"name": s["name"], "url": s.get("url", ""), "note": s.get("note", "")}
            for s in car["sources"]
        ],
    }


def write_module(path: Path, banner: str, body: str) -> None:
    path.write_text(
        f"// GENERATED by tools/build_web_data.py from data/vehicles.json — do not edit.\n"
        f"// {banner}\n{body}",
        encoding="utf-8",
    )
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.0f} KB")


def main() -> int:
    cars = json.loads(SOURCE.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(exist_ok=True)

    compacted = [compact(car) for car in cars]
    meta = {
        "count": len(cars),
        "updated": max(car["updated_at"] for car in cars),
        "sourceCount": sum(len(car["sources"]) for car in cars),
    }
    dump = lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    write_module(
        OUT_DIR / "car-data.js",
        "Compact records for the ranking, the table and the charts.",
        f"export const CARS = {dump(compacted)};\nexport const META = {dump(meta)};\n",
    )
    write_module(
        OUT_DIR / "car-detail.js",
        "Provenance text, imported only when a detail panel opens.",
        f"export const DETAILS = {dump({car['id']: detail(car) for car in cars})};\n",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
