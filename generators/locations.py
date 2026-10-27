"""
make_locations.py
Builds locations.csv: the depot (location_id 0) plus the customers (1..N).

Reads : places_pool.csv  (the 1500 Budapest addresses from OpenStreetMap)
Writes: locations.csv    (rows are numbered 0..N, and this numbering is also
                          the row/column numbering of the future distances.csv)
"""
import csv
import random

# ======================= SETTINGS (change these) ==========================

N_CUSTOMERS = 250   # how many customers to pick from the pool (max = pool size)
SEED = 42           # same seed = same customers for everybody

# The depot (central warehouse). It does not come from the pool.
# lat/lon are APPROXIMATE (south-east edge of Budapest): check on a map and change.
DEPOT = dict(
    location_id=0,                  # always 0, because the distance matrix starts with it
    place_id="",                    # empty: the depot is not in the pool
    type="depot",
    lat=47.4050,
    lon=19.1100,
    street="Depot (warehouse)",
    housenumber="",
    district=23,
    full_address="Furniture central warehouse, Budapest, Hungary",
)

POOL_FILE   = "places_pool.csv"
OUTPUT_FILE = "locations.csv"

# ===========================================================================


def main():
    # read the whole pool of candidate addresses
    with open(POOL_FILE, newline="", encoding="utf-8") as f:
        pool = list(csv.DictReader(f))
    print("pool size:", len(pool))

    # pick N_CUSTOMERS different places at random (reproducible thanks to SEED)
    rng = random.Random(SEED)
    chosen = rng.sample(pool, N_CUSTOMERS)

    rows = [DEPOT]  # the depot is always the first row
    for location_id, place in enumerate(chosen, start=1):
        rows.append(dict(
            location_id=location_id,       # new numbering 1..N
            place_id=place["place_id"],    # keeps the link back to the pool
            type="customer",
            lat=place["lat"],
            lon=place["lon"],
            street=place["street"],
            housenumber=place["housenumber"],
            district=place["district"],
            full_address=place["full_address"],
        ))

    fields = ["location_id", "place_id", "type", "lat", "lon",
              "street", "housenumber", "district", "full_address"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {OUTPUT_FILE}: {len(rows)} rows (1 depot + {N_CUSTOMERS} customers)")


if __name__ == "__main__":
    main()