import hashlib
import os
import urllib.request

import pandas as pd
import pandas_indexing as pix

INFILLING_DB_RECORD_ID = "20566343"
INFILLING_DB_FILENAME = "infiling-db_202512021030_202512071232_202511040855_202511040855.parquet.gzip"
INFILLING_DB_MD5 = "afc2ba861338f406c7111738cce4c877"
INFILLING_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "infilling")

MARKER_DB_PATH = "/home/maritsandstad/gitrepos/rcmip-phase-3-scenariomip/ScenarioMIP/scenariomip_scenarios_for_scms.csv"
HISTORY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "historical_emissions_from_emissions_harmonisation_Feb2026.csv"
)

LEAD_VARIABLE = "Emissions|CO2|Energy and Industrial Processes"
MAJOR_SPECIES = [
    "Emissions|BC",
    "Emissions|CH4",
    "Emissions|CO",
    "Emissions|N2O",
    "Emissions|NH3",
    "Emissions|NOx",
    "Emissions|OC",
    "Emissions|Sulfur",
    "Emissions|VOC",
    "Emissions|CO2|AFOLU",
]
INFILLING_START_YEAR = 2023
INFILLING_END_YEAR = 2100
INDEX_COLUMNS = ["model", "scenario", "region", "variable", "unit"]


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_infilling_db(target_dir=INFILLING_DB_DIR):
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, INFILLING_DB_FILENAME)
    if os.path.exists(path) and _md5(path) == INFILLING_DB_MD5:
        return path
    url = f"https://zenodo.org/records/{INFILLING_DB_RECORD_ID}/files/{INFILLING_DB_FILENAME}?download=1"
    print(f"Downloading infilling database from {url}")
    urllib.request.urlretrieve(url, path)
    checksum = _md5(path)
    if checksum != INFILLING_DB_MD5:
        os.remove(path)
        raise ValueError(f"md5 mismatch for {INFILLING_DB_FILENAME}: {checksum} != {INFILLING_DB_MD5}")
    return path


def _to_timeseries_frame(df):
    """Return df indexed by INDEX_COLUMNS with int year columns, dropping any other index levels."""
    if not isinstance(df.index, pd.MultiIndex):
        df = df.set_index([c for c in df.columns if not _is_year(c)])
    df = df.reset_index([n for n in df.index.names if n not in INDEX_COLUMNS], drop=True)
    df = df.reorder_levels(INDEX_COLUMNS)
    df.columns = [int(float(c)) for c in df.columns]
    return df.sort_index(axis="columns")


def _is_year(col):
    try:
        float(col)
    except (TypeError, ValueError):
        return False
    return True


def _restrict_years(df, start=INFILLING_START_YEAR, end=INFILLING_END_YEAR):
    return df.loc[:, [c for c in df.columns if start <= c <= end]]


def load_infilling_db(path=None):
    """Return (silicone_db, wmo_db) from the Zenodo infilling database, without the major species."""
    if path is None:
        path = download_infilling_db()
    db = _restrict_years(_to_timeseries_frame(pd.read_parquet(path)))
    db = db.loc[~pix.isin(variable=MAJOR_SPECIES)]
    wmo_locator = pix.ismatch(model="WMO**")
    velders_locator = pix.ismatch(model="Velders**")
    return db.loc[~wmo_locator & ~velders_locator], db.loc[wmo_locator]


def load_marker_db(path=MARKER_DB_PATH):
    db = _restrict_years(_to_timeseries_frame(pd.read_csv(path)))
    return db.loc[pix.isin(variable=[LEAD_VARIABLE, *MAJOR_SPECIES])]


def load_history(path=HISTORY_PATH):
    return _to_timeseries_frame(pd.read_csv(path))


def load_infilling_inputs(marker_db_path=MARKER_DB_PATH, history_path=HISTORY_PATH, infilling_db_path=None):
    silicone_db, wmo_db = load_infilling_db(infilling_db_path)
    return {
        "marker_db": load_marker_db(marker_db_path),
        "silicone_db": silicone_db,
        "wmo_db": wmo_db,
        "history": load_history(history_path),
    }


if __name__ == "__main__":
    silicone_db, wmo_db = load_infilling_db()
    print(f"Silicone DB: {len(silicone_db)} rows, years {silicone_db.columns.min()}-{silicone_db.columns.max()}")
    print(sorted(silicone_db.pix.unique("variable")))
    print(f"WMO DB: {len(wmo_db)} rows")
    print(sorted(wmo_db.pix.unique("variable")))
