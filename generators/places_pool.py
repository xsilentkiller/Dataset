import csv, json, os, random, time, requests

random.seed(42)
N_POOL = 1500
PER_DISTRICT = 100          # max addresses fetched per district
os.makedirs("dataset/cache", exist_ok=True)

MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
HEADERS = {
    "User-Agent": "ELTE-CI-furniture-routing-project/1.0 (student project)",
    "Accept": "application/json",
}

def fetch_district(d):
    cache = f"dataset/cache/district_{d:02d}.json"
    if os.path.exists(cache):                       # reuse earlier result
        with open(cache, encoding="utf-8") as f:
            return json.load(f)

    query = f"""
    [out:json][timeout:120];
    area["ISO3166-2"="HU-BU"]->.bp;
    nwr["addr:housenumber"]["addr:street"]["addr:postcode"~"^1{d:02d}[0-9]$"](area.bp);
    out center tags {PER_DISTRICT};
    """
    for attempt in range(6):
        url = MIRRORS[attempt % len(MIRRORS)]
        try:
            r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=150)
            if r.status_code == 200:
                els = r.json()["elements"]
                with open(cache, "w", encoding="utf-8") as f:
                    json.dump(els, f)
                return els
            print(f"district {d}: {r.status_code} from {url}, waiting...")
        except requests.RequestException as ex:
            print(f"district {d}: {ex} from {url}, waiting...")
        time.sleep(20 * (attempt + 1))
    print(f"district {d}: giving up")
    return []

seen, places = set(), []
for d in range(1, 24):
    els = fetch_district(d)
    print(f"district {d}: {len(els)} elements")
    for e in els:
        t = e["tags"]
        lat = e.get("lat") or e.get("center", {}).get("lat")
        lon = e.get("lon") or e.get("center", {}).get("lon")
        if lat is None:
            continue
        key = (t["addr:street"], t["addr:housenumber"], t["addr:postcode"])
        if key in seen:
            continue
        seen.add(key)
        places.append(dict(
            lat=round(lat, 6), lon=round(lon, 6),
            street=t["addr:street"], housenumber=t["addr:housenumber"],
            postcode=t["addr:postcode"], district=d,
            suburb=t.get("addr:suburb", ""),
            city="Budapest", country="Hungary",
        ))
    time.sleep(3)                                   # be polite between requests

print("total unique addresses:", len(places))
pool = random.sample(places, min(N_POOL, len(places)))
for i, p in enumerate(pool, start=1):
    p["place_id"] = i
    p["full_address"] = f'{p["street"]} {p["housenumber"]}, {p["postcode"]} Budapest, Hungary'

fields = ["place_id", "lat", "lon", "street", "housenumber", "postcode",
          "district", "suburb", "city", "country", "full_address"]
with open("dataset/places_pool.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(pool)
print("wrote", len(pool), "places")