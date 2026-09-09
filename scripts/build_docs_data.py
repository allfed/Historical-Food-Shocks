"""
Prepares JSON data files for the interactive GitHub Pages companion site
from the existing results/ CSVs and the Natural Earth shapefile.

Not part of the analysis pipeline - run once (or whenever results/ changes)
to regenerate docs/data/*.json.
"""

import json
from pathlib import Path

import country_converter as coco
import geopandas as gpd
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "docs" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_COLORS = {
    "Economic": "#F0B323",
    "Policy": "#755549",
    "Climate": "#e67f54",
    "Conflict": "#C41E3A",
    "Environmental Hazard": "#6197d0",
    "Pest/Disease": "#006B3C",
    "Infrastructure": "#8B7355",
    "Mismanagement": "#9B5A75",
    "Unknown": "#808080",
}
DEFAULT_COLOR = "#E6E6FA"


def load_map():
    # Force use of Fiona instead of pyogrio, matching src/plot_maps.py
    admin_map = gpd.read_file(
        REPO / "data" / "ne_110m_admin_0_countries.shp", engine="fiona"
    )
    admin_map = admin_map[admin_map["ADMIN"] != "Antarctica"].copy()
    admin_map["name_short"] = coco.convert(
        admin_map["ADMIN"], to="name_short", not_found=None
    )
    # simplify geometry to keep file size small, keep in WGS84 (lon/lat)
    admin_map["geometry"] = admin_map["geometry"].simplify(
        0.03, preserve_topology=True
    )
    return admin_map[["name_short", "ADMIN", "CONTINENT", "geometry"]]


def dedupe_by_name_short(df, name_col, name_short_col="name_short"):
    """
    FAO's "Area" list includes now-defunct predecessor states (e.g. "Ethiopia PDR",
    "Sudan (former)") alongside their modern successors. country_converter maps both
    to the same name_short, which would otherwise create duplicate map features.
    Keep the row whose original name IS the modern name (exact match); otherwise
    keep the first occurrence.
    """
    df = df.copy()
    df["_is_modern"] = df[name_col] == df[name_short_col]
    df = df.sort_values("_is_modern", ascending=False)
    df = df.drop_duplicates(subset=name_short_col, keep="first")
    return df.drop(columns="_is_modern")


def load_shock_data():
    df = pd.read_csv(REPO / "results" / "largest_crop_shock_by_country_with_reasons.csv")
    df["name_short"] = coco.convert(df["country"], to="name_short", not_found=None)
    df = dedupe_by_name_short(df, "country")
    return df


def load_yearly(name_short_lookup):
    """Per-country year -> % deviation series, for the country detail panel."""
    df = pd.read_csv(REPO / "results" / "yield_changes_by_countries.csv", index_col=0)
    df = df.reset_index().rename(columns={"Area": "country"})
    df["name_short"] = coco.convert(df["country"], to="name_short", not_found=None)
    df = dedupe_by_name_short(df, "country").set_index("name_short")

    series = {}
    for name_short in name_short_lookup:
        if name_short in df.index:
            row = df.loc[name_short].drop("country")
            series[name_short] = {
                str(year): (None if pd.isna(v) else round(float(v), 2))
                for year, v in row.items()
            }
    return series


def build_countries_geojson(admin_map, shock_df):
    merged = admin_map.merge(
        shock_df[
            [
                "name_short",
                "country",
                "largest_food_shock",
                "year_of_shock",
                "Category (main)",
                "Category (secondary)",
                "Reason",
                "Source",
                "Source Link",
            ]
        ],
        on="name_short",
        how="left",
    )

    features = []
    for _, row in merged.iterrows():
        category = row["Category (main)"]
        color = (
            CATEGORY_COLORS.get(category, DEFAULT_COLOR)
            if pd.notna(category)
            else None
        )
        props = {
            "name": row["ADMIN"],
            "name_short": row["name_short"],
            "continent": row["CONTINENT"],
            "shock_pct": None
            if pd.isna(row["largest_food_shock"])
            else round(float(row["largest_food_shock"]), 1),
            "shock_year": None
            if pd.isna(row["year_of_shock"])
            else int(row["year_of_shock"]),
            "category_main": None if pd.isna(category) else category,
            "category_secondary": None
            if pd.isna(row["Category (secondary)"])
            else row["Category (secondary)"],
            "reason": None if pd.isna(row["Reason"]) else str(row["Reason"]).strip(),
            "source": None if pd.isna(row["Source"]) else str(row["Source"]).strip(),
            "source_link": None
            if pd.isna(row["Source Link"])
            else str(row["Source Link"]).strip(),
            "category_color": color,
        }
        features.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": json.loads(gpd.GeoSeries([row["geometry"]]).to_json())[
                    "features"
                ][0]["geometry"],
            }
        )

    return {"type": "FeatureCollection", "features": features}


def build_category_summary(shock_df, admin_map):
    df = shock_df.merge(
        admin_map[["name_short", "CONTINENT"]], on="name_short", how="left"
    )
    df = df.dropna(subset=["Category (main)"])
    df["decade"] = (df["year_of_shock"] // 10 * 10).astype("Int64")

    by_continent = (
        df.groupby(["CONTINENT", "Category (main)"]).size().reset_index(name="count")
    )
    by_decade = (
        df.groupby(["decade", "Category (main)"]).size().reset_index(name="count")
    )
    overall = df["Category (main)"].value_counts().reset_index()
    overall.columns = ["category", "count"]

    return {
        "colors": CATEGORY_COLORS,
        "overall": overall.to_dict(orient="records"),
        "by_continent": [
            {
                "continent": r["CONTINENT"],
                "category": r["Category (main)"],
                "count": int(r["count"]),
            }
            for _, r in by_continent.iterrows()
        ],
        "by_decade": [
            {
                "decade": int(r["decade"]),
                "category": r["Category (main)"],
                "count": int(r["count"]),
            }
            for _, r in by_decade.iterrows()
            if pd.notna(r["decade"])
        ],
    }


def build_headline_stats(shock_df):
    freq = pd.read_csv(REPO / "results" / "historical_frequency_results.csv", index_col=0)
    yearly_cols = pd.read_csv(
        REPO / "results" / "yield_changes_by_countries.csv", index_col=0, nrows=0
    ).columns
    year_min, year_max = int(yearly_cols[0]), int(yearly_cols[-1])

    n_countries_with_data = shock_df["largest_food_shock"].notna().sum()
    n_severe = (shock_df["largest_food_shock"] <= -20).sum()
    any_country = freq.loc["Any Country"]

    worst = shock_df.loc[shock_df["largest_food_shock"].idxmin()]

    return {
        "n_countries": int(n_countries_with_data),
        "n_severe_shocks": int(n_severe),
        "year_min": year_min,
        "year_max": year_max,
        "years_with_a_shock_somewhere": int(any_country["years_with_events"]),
        "total_years_covered": year_max - year_min + 1,
        "total_country_shock_events": int(any_country["total_events"]),
        "avg_shocks_per_year": round(float(any_country["avg_events_per_year"]), 1),
        "spotlight": {
            "country": worst["country"],
            "name_short": worst["name_short"],
            "pct": round(float(worst["largest_food_shock"]), 1),
            "year": int(worst["year_of_shock"]),
            "category": worst["Category (main)"]
            if pd.notna(worst["Category (main)"])
            else None,
            "reason": str(worst["Reason"]).strip() if pd.notna(worst["Reason"]) else None,
            "source": str(worst["Source"]).strip() if pd.notna(worst["Source"]) else None,
            "source_link": str(worst["Source Link"]).strip()
            if pd.notna(worst["Source Link"])
            else None,
        },
    }


def build_decade_shock_counts(admin_map, threshold=-5):
    """
    For each country, count how many years per decade its production fell more than
    `threshold` percent below trend (matches the shock definition used elsewhere in
    the analysis, see README "Shock threshold values"). Powers the decade-by-decade
    small-multiple maps.
    """
    df = pd.read_csv(REPO / "results" / "yield_changes_by_countries.csv", index_col=0)
    df = df.reset_index().rename(columns={"Area": "country"})
    df["name_short"] = coco.convert(df["country"], to="name_short", not_found=None)
    df = dedupe_by_name_short(df, "country").set_index("name_short")
    df = df.drop(columns="country")

    year_cols = [c for c in df.columns]
    decades = sorted({int(y) // 10 * 10 for y in year_cols})

    counts = {}
    for name_short, row in df.iterrows():
        by_decade = {}
        for decade in decades:
            years_in_decade = [y for y in year_cols if int(y) // 10 * 10 == decade]
            n_shocks = int((row[years_in_decade] < threshold).sum())
            if n_shocks:
                by_decade[str(decade)] = n_shocks
        if by_decade:
            counts[name_short] = by_decade

    decade_spans = {}
    for decade in decades:
        years_in_decade = [int(y) for y in year_cols if int(y) // 10 * 10 == decade]
        decade_spans[str(decade)] = [min(years_in_decade), max(years_in_decade)]

    return {
        "threshold": threshold,
        "decades": [str(d) for d in decades],
        "decade_spans": decade_spans,
        "counts": counts,
    }


def main():
    admin_map = load_map()
    shock_df = load_shock_data()

    geojson = build_countries_geojson(admin_map, shock_df)
    (OUT_DIR / "countries.geojson").write_text(json.dumps(geojson))

    category_summary = build_category_summary(shock_df, admin_map)
    (OUT_DIR / "category_summary.json").write_text(json.dumps(category_summary, indent=2))

    yearly = load_yearly(shock_df["name_short"].dropna().unique())
    (OUT_DIR / "yearly_by_country.json").write_text(json.dumps(yearly))

    stats = build_headline_stats(shock_df)
    (OUT_DIR / "headline_stats.json").write_text(json.dumps(stats, indent=2))

    decade_counts = build_decade_shock_counts(admin_map)
    (OUT_DIR / "decade_shock_counts.json").write_text(json.dumps(decade_counts))

    print("Wrote:")
    for f in OUT_DIR.glob("*.json"):
        print(f" -", f, f.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
