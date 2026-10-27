"""
make_orders.py
Builds orders.csv (there is NO separate items file).

Reads : furniture_clean.csv  (the furniture list, 168 pieces; it is the item table)
        locations.csv        (depot + 250 customers)
Writes: orders.csv  one row per customer order: which pieces it contains
                    (item_ids = ids from furniture_clean.csv, separated by ";"),
                    totals, and loading/unloading times.

To get the dimensions of a piece in an order, look its id up in furniture_clean.csv.
The same piece id can appear in several orders (like a product that many people buy).

Everything you may want to change is in the SETTINGS block below.
"""
import csv
import random

# ======================= SETTINGS (change these) ==========================

SEED = 42  # Same seed = same data for everybody. Change it for a different instance.

# How many furniture pieces one order can have, and how likely each count is.
# Example: [1, 2, 3, 4] with weights [40, 30, 20, 10] means 40% of orders have
# 1 piece, 30% have 2, 20% have 3, 10% have 4. Bigger orders = more demand.
ITEMS_PER_ORDER = [1, 2, 3, 4]
ITEMS_WEIGHTS   = [40, 30, 20, 10]

# ---- Loading at the depot (warehouse -> vehicle), minutes ----
# time = LOAD_BASE_MIN + LOAD_PER_KG_MIN * (total weight of the order in kg)
LOAD_BASE_MIN   = 3.0    # fixed time per order (the "3 minutes")
LOAD_PER_KG_MIN = 0.05   # extra minutes per kg (heavier order = slower). 0 = ignore weight.

# ---- Unloading at the customer (vehicle -> customer's door), minutes ----
# This is the "packing time" from the brief (the time spent at the destination).
# time = UNLOAD_BASE_MIN + UNLOAD_PER_KG_MIN * (total weight of the order in kg)
UNLOAD_BASE_MIN   = 5.0   # fixed time per order (the "5 minutes")
UNLOAD_PER_KG_MIN = 0.05  # extra minutes per kg. 0 = ignore weight.

# Input / output file names
FURNITURE_FILE = "furniture_clean.csv"
LOCATIONS_FILE = "locations.csv"
ORDERS_FILE    = "orders.csv"

# ===========================================================================


def loading_time(weight_kg):
    """Minutes to load one order into the vehicle at the depot."""
    return round(LOAD_BASE_MIN + LOAD_PER_KG_MIN * weight_kg, 1)


def unloading_time(weight_kg):
    """Minutes to unload one order at the customer (the brief's 'packing time')."""
    return round(UNLOAD_BASE_MIN + UNLOAD_PER_KG_MIN * weight_kg, 1)


def write_csv(path, rows):
    """Write a list of dicts to a CSV file; the dict keys become the header."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    rng = random.Random(SEED)  # own random generator, so the result is reproducible

    # --- read the furniture list (dimensions in metres, weight in kg) ---
    with open(FURNITURE_FILE, newline="", encoding="utf-8") as f:
        furniture = list(csv.DictReader(f))

    # --- read the customers (skip the depot, location_id 0) ---
    with open(LOCATIONS_FILE, newline="", encoding="utf-8") as f:
        customers = [r for r in csv.DictReader(f) if r["type"] == "customer"]

    orders = []

    # One order per customer. order_id is just 1..250 in the same order as customers.
    for order_id, customer in enumerate(customers, start=1):

        # Decide how many pieces this order has (random, using the weights above)
        n_items = rng.choices(ITEMS_PER_ORDER, weights=ITEMS_WEIGHTS)[0]

        # Pick that many different pieces from the furniture list (no repeats inside one order)
        picked = rng.sample(furniture, n_items)

        total_weight = 0.0
        total_volume = 0.0

        for piece in picked:
            length = float(piece["length_m"])
            width  = float(piece["width_m"])
            height = float(piece["height_m"])
            weight = float(piece["weight_kg"])

            # Volume = bounding box of the piece (slightly generous, ignores shape)
            volume = length * width * height

            total_weight += weight
            total_volume += volume

        # One row per order. location_id links the order to locations.csv.
        orders.append(dict(
            order_id=order_id,
            location_id=customer["location_id"],
            num_items=n_items,
            item_ids=";".join(p["id"] for p in picked),  # ids from furniture_clean.csv
            total_weight_kg=round(total_weight, 3),
            total_volume_m3=round(total_volume, 4),
            loading_time_min=loading_time(total_weight),      # at the depot
            packing_time_min=unloading_time(total_weight),    # at the customer
        ))

    write_csv(ORDERS_FILE, orders)
    print(f"wrote {ORDERS_FILE} ({len(orders)} rows)")


if __name__ == "__main__":
    main()