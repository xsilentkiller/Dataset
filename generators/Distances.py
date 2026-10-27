"""
make_distances.py
Builds distances.csv: the road distance in km between every pair of locations.

Reads : locations.csv   (depot = location_id 0, customers = 1..N)
Writes: distances.csv   (square matrix; row i and column i are location_id i)

This is the OFFLINE ESTIMATE: straight-line (haversine) distance multiplied by a
winding factor, because real roads are longer than the straight line.
Later it can be replaced by real road distances (e.g. from OSRM) with the SAME
file name and format, so the algorithms do not need any change.

Reading it in Python:  pandas.read_csv("distances.csv", index_col=0)
    distance from location 3 to location 17  ->  df.loc[3, "17"]
"""
import csv
import math

# ======================= SETTINGS (change these) ==========================

# Road distance = straight-line distance * WINDING_FACTOR.
# 1.3 is a common value for a city. Budapest has the Danube and few bridges,
# so some real pairs are much longer; use real road distances if you need that.
WINDING_FACTOR = 1.3

DECIMALS = 3   # decimals in km (3 = metre precision)

LOCATIONS_FILE = "locations.csv"
OUTPUT_FILE    = "distances.csv"

EARTH_RADIUS_KM = 6371.0088   # mean radius of the Earth

# ===========================================================================


def haversine_km(lat1, lon1, lat2, lon2):
    """Straight-line distance in km between two lat/lon points on the Earth."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def main():
    # read all locations, in the order of location_id (0 = depot)
    with open(LOCATIONS_FILE, newline="", encoding="utf-8") as f:
        locs = sorted(csv.DictReader(f), key=lambda r: int(r["location_id"]))
    ids = [int(r["location_id"]) for r in locs]
    coords = [(float(r["lat"]), float(r["lon"])) for r in locs]
    n = len(locs)

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["from_id"] + ids)          # header: column = destination id
        for i in range(n):
            row = [ids[i]]                          # first cell: row = origin id
            for j in range(n):
                if i == j:
                    row.append(0.0)                 # a place to itself is 0 km
                else:
                    d = haversine_km(*coords[i], *coords[j]) * WINDING_FACTOR
                    row.append(round(d, DECIMALS))
            writer.writerow(row)

    print(f"wrote {OUTPUT_FILE}: {n} x {n} matrix (winding factor {WINDING_FACTOR})")


if __name__ == "__main__":
    main()