"""
Clean the raw Amazon furniture dataset for delivery / vehicle-loading use.

Input : raw CSV (default: the uploaded furniture_amazon_dataset.csv)
Output: ONE clean CSV with columns
        id, name, length_m, width_m, height_m, weight_kg, material, color, country_of_origin

Usage:
    python clean_furniture_dataset.py [raw_csv] [clean_csv]
"""
import ast
import re
import sys

import pandas as pd

RAW_PATH = sys.argv[1] if len(sys.argv) > 1 else "furniture_amazon_dataset.csv"
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else " furniture_clean.csv"

INCH_TO_M = 0.0254
MIN_SIDE_M = 0.05          # a package side under 5 cm is not real furniture (placeholder / accessory)
MIN_DENSITY_KG_M3 = 5      # weight far too low for the box size = wrong weight in the listing
WEIGHT_TO_KG = {"kg": 1.0, "kilogram": 1.0, "g": 0.001, "gram": 0.001,
                "lb": 0.45359237, "pound": 0.45359237, "oz": 0.028349523, "ounce": 0.028349523}

# --------------------------------------------------------------------------
# 1. ONE-WORD FURNITURE NAME
#    Step A: map the product's Amazon category (last level) to a name.
#    Step B: if the category is too generic, read the title for a keyword.
#    Anything that is not furniture (doormats, towel bars, mounts, mirrors,
#    wastebaskets, replacement parts, covers...) gets no name and is removed.
#    -> edit these tables if you want to keep/drop other product types.
# --------------------------------------------------------------------------
EXCLUDE_LEAF = {
    "Doormats", "Towel Bars", "Towel Rings", "Towel Racks", "Wastebaskets",
    "TV Wall & Ceiling Mounts", "Bed Parts", "Sofa Parts", "Recliner Parts",
    "Over the Door Shoe Organizers", "Boot & Shoe Boxes", "DVD Cases", "Toy Bags & Nets",
    "Mattress Toppers", "Hampers", "Pop-Up Laundry Hampers",
    "Wall-Mounted Mirrors", "Makeup Mirrors", "Bathroom Mirrors",
    "Wall-Mounted Vanity Mirrors", "Shower Mirrors",
}

LEAF_NAME = {
    "End Tables": "Table", "Coffee Tables": "Table", "Tables": "Table", "Folding Tables": "Table",
    "Nesting Tables": "Table", "TV Trays": "Table", "Sofa & Console Tables": "Console",
    "Ottomans": "Ottoman", "Poufs": "Pouf", "Bean Bags": "Beanbag",
    "Barstools": "Barstool", "Step Stools": "Stool",
    "Chairs": "Chair", "Home Office Desk Chairs": "Chair", "Desk Chairs": "Chair",
    "Managerial & Executive Chairs": "Chair", "Video Game Chairs": "Chair",
    "Computer Gaming Chairs": "Chair", "Folding Chairs": "Chair", "Adirondack Chairs": "Chair",
    "Home Office Desks": "Desk", "Nightstands": "Nightstand",
    "Storage Benches": "Bench", "Table Benches": "Bench",
    "Coat Racks": "Rack", "Free Standing Shoe Racks": "Rack", "Folding Shoe Racks": "Rack",
    "Wall-Mounted Wine Racks": "Rack", "Shoe Slots": "Rack",
    "Freestanding Wine Racks & Cabinets": "Rack",
    "Storage Cabinets": "Cabinet", "Bar Cabinets": "Cabinet", "Wine Cabinets": "Cabinet",
    "Shoe Cabinets": "Cabinet", "Bedroom Armoires": "Armoire",
    "Bookcases": "Bookcase", "Ladder Shelves": "Shelf",
    "Dressers": "Dresser", "Chests & Dressers": "Dresser",
    "Sofas": "Sofa", "Sofas & Couches": "Sofa",
    "Bed Frames": "Bed", "Beds": "Bed", "Box Springs": "Boxspring", "Mattresses": "Mattress",
    "Bedside Cribs": "Crib", "Storage Carts": "Cart", "Bar & Serving Carts": "Cart",
    "Mobile Storage Islands": "Island", "Storage Trunks": "Trunk",
    "Table & Chair Sets": "Set",
}

# generic categories: decide from the title, with an optional default
GENERIC_LEAF_DEFAULT = {
    "Furniture": None, "Game & Recreation Room Furniture": None, "Bathroom Sets": None,
    "Bookcases, Cabinets & Shelves": "Shelf", "Over-the-Toilet Storage": "Shelf",
    "Vanities & Vanity Benches": "Vanity",
    "Turntables": None, "Supply Organizers": None, "Toy Chests & Organizers": None,
    "Living Room Sets": "Set",
}

# ordered: first match wins
TITLE_RULES = [
    (r"bar ?stool|counter stool", "Barstool"), (r"ottoman", "Ottoman"), (r"\bstool", "Stool"),
    (r"\bbench", "Bench"), (r"\bpouf", "Pouf"), (r"bean ?bag", "Beanbag"), (r"\bchairs?\b", "Chair"),
    (r"\bsofa|couch|loveseat", "Sofa"), (r"night ?stand|bedside table", "Nightstand"),
    (r"\bdesk\b", "Desk"), (r"book ?case|book ?shelf", "Bookcase"), (r"\bvanity", "Vanity"),
    (r"armoire", "Armoire"), (r"cabinet", "Cabinet"), (r"dresser|chest of drawers", "Dresser"),
    (r"\bchest\b", "Chest"), (r"shel(f|ves)|etagere", "Shelf"), (r"\btables?\b", "Table"),
    (r"\brack", "Rack"), (r"\bcart\b", "Cart"), (r"\bbed\b", "Bed"),
]

# covers / slipcovers / spare parts are not the furniture itself
NOT_FURNITURE_TITLE = re.compile(
    r"\bcover only\b|unstuffed|slip ?covers?|(pouf|ottoman|bean ?bag|chair|sofa|couch|seat)\s+covers?\b"
    r"|\bcovers? (for|only)\b|replacement|support leg"
    r"|stuffed animal storage|stuffable|unfilled|no filler"
    r"|remote (control )?(holder|caddy)|mattress (bag|cover|protector)|bag for moving"
    r"|cosmetic|lipstick|leveling glides?|desk decor|wood block sign|clip-on tray|arm clip tray|shoe slot"
    r"|water bottle organizer", re.I)


# --------------------------------------------------------------------------
# 1b. SPECIFIC TYPE NAME  (e.g. Chair -> Office Chair / Gaming Chair / Dining Chair)
#     rules are checked top to bottom, first match wins:
#     (where to look, regex, name)   where = "leaf" (Amazon category) or "title"
#     if nothing matches, the default name for that group is used.
# --------------------------------------------------------------------------
SUBTYPES = {
    "Chair": ([
        ("title", r"conference", "Conference Chair"),
        ("title", r"saucer", "Saucer Chair"),
        ("title", r"floor chair", "Floor Chair"),
        ("leaf", r"adirondack", "Adirondack Chair"),
        ("leaf", r"gaming|video game", "Gaming Chair"),
        ("leaf", r"office|desk chair|managerial", "Office Chair"),
        ("title", r"recliner", "Recliner Chair"),
        ("title", r"dining|parsons|side chair", "Dining Chair"),
        ("title", r"folding", "Folding Chair"),
        ("title", r"gaming chair|gamer", "Gaming Chair"),
        ("title", r"office chair|desk chair|task chair|computer chair", "Office Chair"),
        ("title", r"accent|lounge|barrel|lazy|occ?asional|reading", "Accent Chair"),
    ], "Chair"),
    "Table": ([
        ("title", r"tv tray|tray table|snack tray", "Tray Table"),
        ("title", r"workbench", "Workbench"),
        ("leaf", r"coffee tables", "Coffee Table"),
        ("leaf", r"nesting", "Nesting Table"),
        ("leaf", r"end tables", "End Table"),
        ("leaf", r"folding tables", "Folding Table"),
        ("title", r"camping|folding table", "Folding Table"),
        ("title", r"bar table|pub table|bistro", "Bar Table"),
        ("title", r"dining|extendable|leaf table|kitchen table", "Dining Table"),
        ("title", r"outdoor|patio", "Outdoor Table"),
    ], "Table"),
    "Ottoman": ([
        ("title", r"storage", "Storage Ottoman"),
        ("title", r"foot ?stool|foot ?rest", "Footstool"),
        ("title", r"vanity", "Vanity Stool"),
    ], "Ottoman"),
    "Barstool": ([("title", r"counter", "Counter Stool")], "Bar Stool"),
    "Stool": ([
        ("leaf", r"step stools", "Step Stool"), ("title", r"step stool", "Step Stool"),
        ("title", r"folding|camping", "Folding Stool"),
        ("title", r"vanity|makeup", "Vanity Stool"),
    ], "Stool"),
    "Cabinet": ([
        ("title", r"dresser|chest of drawers", "Dresser"),
        ("leaf", r"shoe", "Shoe Cabinet"),
        ("leaf", r"toilet", "Bathroom Cabinet"),
        ("title", r"wine|bar server", "Wine Cabinet"),
        ("title", r"corner", "Corner Cabinet"),
        ("title", r"\bwall\b", "Wall Cabinet"),
    ], "Storage Cabinet"),
    "Rack": ([
        ("leaf", r"coat", "Coat Rack"),
        ("leaf", r"shoe", "Shoe Rack"),
        ("leaf", r"wine", "Wine Rack"),
        ("title", r"coat|hall tree", "Coat Rack"),
        ("title", r"clothing|garment|clothes", "Clothes Rack"),
        ("title", r"shoe", "Shoe Rack"),
    ], "Rack"),
    "Bench": ([
        ("title", r"shoe", "Shoe Bench"),
        ("leaf", r"table benches", "Dining Bench"),
        ("title", r"storage", "Storage Bench"),
        ("leaf", r"storage benches", "Storage Bench"),
    ], "Bench"),
    "Nightstand": ([("title", r"floating|wall mounted", "Floating Nightstand")], "Nightstand"),
    "Desk": ([
        ("title", r"gaming", "Gaming Desk"),
        ("title", r"folding|foldable", "Folding Desk"),
        ("title", r"computer", "Computer Desk"),
    ], "Desk"),
    "Shelf": ([
        ("title", r"ladder|blanket", "Ladder Shelf"),
        ("leaf", r"toilet", "Bathroom Shelf"),
        ("title", r"toilet|bathroom", "Bathroom Shelf"),
    ], "Shelf"),
    "Cart": ([
        ("leaf", r"serving", "Bar Cart"),
        ("title", r"kitchen", "Kitchen Cart"),
    ], "Storage Cart"),
    "Sofa": ([("title", r"sectional", "Sectional Sofa"), ("title", r"loveseat", "Loveseat")], "Sofa"),
    "Bed": ([("title", r"frame", "Bed Frame")], "Bed"),
    "Vanity": ([
        ("title", r"bench|stool", "Vanity Stool"),
        ("title", r"bathroom|sink", "Bathroom Vanity"),
    ], "Vanity"),
    "Set": ([("title", r"dining|kitchen", "Dining Set")], "Table Set"),
    "Beanbag": ([], "Bean Bag"), "Boxspring": ([], "Box Spring"), "Crib": ([], "Bedside Crib"),
    "Trunk": ([], "Storage Trunk"), "Island": ([], "Kitchen Island"), "Console": ([], "Console Table"),
}


def specific_name(base, leaf, title):
    rules, default = SUBTYPES.get(base, ([], base))
    leaf_l, title_l = leaf.lower(), title.lower()
    for where, pattern, name in rules:
        if re.search(pattern, leaf_l if where == "leaf" else title_l):
            return name
    return default


def leaf_category(cat_str):
    try:
        cats = ast.literal_eval(cat_str)
        return cats[-1] if cats else ""
    except (ValueError, SyntaxError):
        return ""


def furniture_name(leaf, title):
    t = title.lower()
    if NOT_FURNITURE_TITLE.search(t) or leaf in EXCLUDE_LEAF:
        return None
    if leaf in LEAF_NAME:
        return LEAF_NAME[leaf]
    for pattern, name in TITLE_RULES:
        if re.search(pattern, t):
            return name
    return GENERIC_LEAF_DEFAULT.get(leaf)


# --------------------------------------------------------------------------
# 2. SIZE (metres) from package_dimensions  (all values in the file are inches)
#    'D' (depth) is treated as length. Unlabelled "30 x 28 x 27 inches" is read
#    in the order given as length x width x height.
#    Rows with fewer than 3 dimensions cannot be used for loading -> removed.
# --------------------------------------------------------------------------
LABELLED = re.compile(r"(\d+(?:\.\d+)?)\s*(?:\"|”|''|inches|inch|in)?\s*([LDWH])\b", re.I)
NUMBER = re.compile(r"\d+(?:\.\d+)?")


def parse_dimensions(text):
    if not isinstance(text, str):
        return (None, None, None)
    found = {}
    for num, label in LABELLED.findall(text):
        key = {"L": "length", "D": "length", "W": "width", "H": "height"}[label.upper()]
        found.setdefault(key, float(num))
    if len(found) == 3:
        vals = (found["length"], found["width"], found["height"])
    else:
        nums = [float(n) for n in NUMBER.findall(text)]
        if len(nums) != 3:
            return (None, None, None)
        vals = tuple(nums)  # unlabelled: length x width x height
    return tuple(round(v * INCH_TO_M, 3) for v in vals)


# --------------------------------------------------------------------------
# 3. WEIGHT (kg) from the 'specifications' text ("Item Weight: 2.7 pounds")
# --------------------------------------------------------------------------
WEIGHT_PATTERNS = [
    re.compile(r"[\"']Item Weight:\s*([\d.,]+)\s*([A-Za-z]+)", re.I),
    re.compile(r"[\"']Weight:\s*([\d.,]+)\s*([A-Za-z]+)", re.I),
    re.compile(r"[\"']Package Weight:\s*([\d.,]+)\s*([A-Za-z]+)", re.I),
]


def parse_weight_kg(spec):
    if not isinstance(spec, str):
        return None
    for pattern in WEIGHT_PATTERNS:
        m = pattern.search(spec)
        if not m:
            continue
        try:
            value = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        unit = m.group(2).lower().rstrip("s")
        if unit in WEIGHT_TO_KG:
            return round(value * WEIGHT_TO_KG[unit], 3)
    return None


# --------------------------------------------------------------------------
# 4. MATERIAL / COLOR / COUNTRY: use the column, fall back to specifications,
#    tidy the text, fill what is still missing with "Unknown".
# --------------------------------------------------------------------------
def spec_value(spec, keys):
    if not isinstance(spec, str):
        return None
    for key in keys:
        m = re.search(r"[\"']" + re.escape(key) + r":\s*([^'\"\]]+)", spec, re.I)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return None


def tidy_text(value, kind):
    if not isinstance(value, str) or not value.strip():
        return "Unknown"
    v = re.sub(r"\s+", " ", value.strip())
    if kind == "color":
        v = re.sub(r"\b(set|pack|pc|pcs|piece|pieces)\b( of)?\s*\d*", "", v, flags=re.I).strip(" ,-/")
        v = re.sub(r"^\d+\s*", "", v).strip()
        if not re.search(r"[A-Za-z]{3,}", v) or re.fullmatch(r"[A-Za-z]?\d+[A-Za-z0-9-]*", v):
            return "Unknown"  # model codes such as "A5589"
    if v.isupper() and len(v) <= 4:          # USA, MDF ...
        return v
    if v.islower() or v.isupper():
        v = v.title()
    return re.sub(r"\b(Mdf|Pvc|Abs|Pu|Pp)\b", lambda m: m.group(1).upper(), v)


def main():
    raw = pd.read_csv(RAW_PATH)
    log = {"raw rows": len(raw)}

    # remove duplicate products (asin is the unique Amazon product id)
    df = raw.drop_duplicates(subset="asin").copy()
    log["after removing duplicate asin"] = len(df)

    # one-word furniture name
    df["leaf"] = df["categories"].apply(leaf_category)
    df["base"] = [furniture_name(l, t) for l, t in zip(df["leaf"], df["title"])]
    df = df[df["base"].notna()]
    df["name"] = [specific_name(b, l, t) for b, l, t in zip(df["base"], df["leaf"], df["title"])]
    log["after keeping furniture only"] = len(df)

    # dimensions + weight
    dims = df["package_dimensions"].apply(parse_dimensions)
    df["length_m"], df["width_m"], df["height_m"] = (dims.str[0], dims.str[1], dims.str[2])
    df["weight_kg"] = df["specifications"].apply(parse_weight_kg)
    df = df.dropna(subset=["length_m", "width_m", "height_m", "weight_kg"])
    df = df[(df[["length_m", "width_m", "height_m", "weight_kg"]] > 0).all(axis=1)]
    log["after requiring size + weight"] = len(df)

    # plausibility checks (scraped data contains placeholders such as 1" x 1" x 1")
    dim_cols = ["length_m", "width_m", "height_m"]
    df = df[(df[dim_cols].min(axis=1) >= MIN_SIDE_M)]
    log[f"after removing a side < {MIN_SIDE_M} m"] = len(df)
    density = df["weight_kg"] / (df["length_m"] * df["width_m"] * df["height_m"])
    df = df[density >= MIN_DENSITY_KG_M3]
    log[f"after removing density < {MIN_DENSITY_KG_M3} kg/m3"] = len(df)

    # material / color / country
    df["material"] = [tidy_text(m if isinstance(m, str) else spec_value(s, ["Material", "Frame Material"]), "material")
                      for m, s in zip(df["material"], df["specifications"])]
    df["color"] = [tidy_text(c if isinstance(c, str) else spec_value(s, ["Color"]), "color")
                   for c, s in zip(df["color"], df["specifications"])]
    df["country_of_origin"] = [tidy_text(c if isinstance(c, str) else spec_value(s, ["Country of Origin"]), "country")
                               for c, s in zip(df["country_of_origin"], df["specifications"])]

    # new id (asin is dropped); width of the number follows the row count
    df = df.reset_index(drop=True)
    pad = max(3, len(str(len(df))))
    df["id"] = ["fid" + str(i + 1).zfill(pad) for i in range(len(df))]

    out = df[["id", "name", "length_m", "width_m", "height_m", "weight_kg",
              "material", "color", "country_of_origin"]]
    out.to_csv(OUT_PATH, index=False)

    for k, v in log.items():
        print(f"{k:35s}{v}")
    print(f"{'final rows':35s}{len(out)}  -> {OUT_PATH}")
    print("\nName counts:\n", out["name"].value_counts().to_string())
    print("\nSummary:\n", out[["length_m", "width_m", "height_m", "weight_kg"]].describe().round(3).to_string())
    print("\nUnknown share:\n", (out[["material", "color", "country_of_origin"]] == "Unknown").mean().round(2).to_string())


if __name__ == "__main__":
    main()