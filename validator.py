"""
validate_dataset.py
Checks that all dataset files are consistent with each other.
Run from the dataset folder:  python validate_dataset.py
Exit code 0 = everything OK, 1 = at least one check failed.
"""
import json
import sys

import numpy as np
import pandas as pd

errors = []


def check(condition, message):
    """Print OK/FAIL for one check and remember failures."""
    print(("OK    " if condition else "FAIL  ") + message)
    if not condition:
        errors.append(message)


# ----------------------------- load all files -----------------------------
params    = json.load(open("params.json"))
vehicles  = pd.read_csv("vehicles.csv")
furniture = pd.read_csv("furniture_clean.csv")
pool      = pd.read_csv("places_pool.csv")
locations = pd.read_csv("locations.csv")
orders    = pd.read_csv("orders.csv")
dist      = pd.read_csv("distances.csv", index_col=0)

# ------------------------------- params.json ------------------------------
required = ["shift_hours", "overtime_multiplier", "fuel_price_per_l", "packing_mode",
            "required_free_volume_ratio", "min_customers_per_trip",
            "max_customers_per_trip", "depot_id", "num_customers"]
check(all(k in params for k in required), "params.json has all required keys")

# --------------------------------- ids ------------------------------------
check(vehicles.vehicle_id.is_unique, "vehicle_id is unique")
check(furniture.id.is_unique, "furniture id is unique")
check(pool.place_id.is_unique, "place_id is unique in places_pool.csv")
check(locations.location_id.is_unique, "location_id is unique")
check(orders.order_id.is_unique, "order_id is unique")

# ------------------------------ locations ---------------------------------
depot = locations[locations.type == "depot"]
cust  = locations[locations.type == "customer"]
check(len(depot) == 1 and int(depot.location_id.iloc[0]) == params["depot_id"],
      "exactly one depot, with the location_id from params.json")
check(len(cust) == params["num_customers"], "number of customers matches params.json")
check(sorted(locations.location_id) == list(range(len(locations))),
      "location_id runs 0..N without gaps")
check(cust.place_id.astype(int).isin(pool.place_id).all(),
      "every customer place_id exists in places_pool.csv")

# -------------------------------- orders ----------------------------------
check(orders.location_id.isin(cust.location_id).all(), "every order points to a customer")
check(orders.location_id.is_unique and len(orders) == len(cust), "one order per customer")

item_lists = orders.item_ids.str.split(";")
check(item_lists.explode().isin(furniture.id).all(), "every item id exists in furniture_clean.csv")
check((item_lists.str.len() == orders.num_items).all(), "num_items matches item_ids")

f = furniture.set_index("id")
w = item_lists.apply(lambda l: f.loc[l, "weight_kg"].sum())
v = item_lists.apply(lambda l: (f.loc[l, "length_m"] * f.loc[l, "width_m"] * f.loc[l, "height_m"]).sum())
check(np.allclose(w, orders.total_weight_kg, atol=0.01), "order total weights match the pieces")
check(np.allclose(v, orders.total_volume_m3, atol=0.001), "order total volumes match the pieces")

# ------------------------------- distances --------------------------------
n = len(locations)
check(dist.shape == (n, n), f"distance matrix is {n} x {n}")
check(list(dist.index) == list(locations.location_id) and
      [int(c) for c in dist.columns] == list(locations.location_id),
      "distance matrix ids match location_id order")
M = dist.values
check(np.allclose(M, M.T), "distance matrix is symmetric")
check((np.diag(M) == 0).all(), "diagonal is zero")
check((M[~np.eye(n, dtype=bool)] > 0).all(), "all other distances are positive")

# ----------------------------- feasibility --------------------------------
# Each order must fit in the biggest vehicle (weight, volume) and each piece must
# fit in at least one vehicle by its dimensions (longest side vs. cargo space).
big = vehicles.sort_values("max_volume_m3").iloc[-1]
check((orders.total_weight_kg <= big.max_weight_kg).all() and
      (orders.total_volume_m3 <= big.max_volume_m3 * (1 - params["required_free_volume_ratio"])).all(),
      "every single order fits in the largest vehicle")

dims = furniture[["length_m", "width_m", "height_m"]].apply(sorted, axis=1, result_type="expand")  # small, mid, large
cargo = vehicles[["cargo_length_m", "cargo_width_m", "cargo_height_m"]].apply(sorted, axis=1, result_type="expand")
fits_any = np.zeros(len(furniture), dtype=bool)
for _, c in cargo.iterrows():
    fits_any |= ((dims[0] <= c[0]) & (dims[1] <= c[1]) & (dims[2] <= c[2])).values
check(fits_any.all(), "every furniture piece fits (by dimensions) in at least one vehicle")

total_vol = orders.total_volume_m3.sum()
cap_vol = vehicles.max_volume_m3.sum() * (1 - params["required_free_volume_ratio"])
print(f"INFO  total demand {total_vol:.1f} m3, fleet capacity per round {cap_vol:.1f} m3 "
      f"-> at least {int(np.ceil(total_vol / cap_vol))} trips per vehicle")

print()
if errors:
    print(f"{len(errors)} check(s) FAILED")
    sys.exit(1)
print("All checks passed")