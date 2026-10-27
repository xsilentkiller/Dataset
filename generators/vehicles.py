"""
make_vehicles.py
Builds vehicles.csv: one row per vehicle, with all its specs.

To change the fleet: edit FLEET (how many of each model).
To change a model's specs or costs: edit the MODELS table.
Run again afterwards to regenerate vehicles.csv.
"""
import csv

# ======================= SETTINGS (change these) ==========================

# How many vehicles of each model. The model names must match MODELS below.
FLEET = {"caddy": 2, "sprinter": 2, "man_tgl": 1}

# Specs per model. "(assumed)" means it was NOT in the brief, so it is my guess.
MODELS = {
    "caddy": dict(
        model="VW Caddy Cargo SWB",
        max_weight_kg=680,                 # payload (from spec)
        max_volume_m3=3.1,                 # load volume (from spec)
        cargo_length_m=1.80,               # (assumed) chosen so L*W*H is about 3.1 m3
        cargo_width_m=1.55,                # (assumed)
        cargo_height_m=1.11,               # (assumed)
        fuel_l_per_km=round((4.5 + 6.2) / 2 / 100, 4),  # midpoint of 4.5-6.2 L/100km, as L/km
        top_speed_kmh=178,                 # from spec, not used for travel time
        avg_speed_kmh=50,                  # (assumed) speed used for travel time in the city
        wage_per_h=12.0,                   # (assumed) driver wage, EUR per hour
        maintenance_per_1000km=80.0,       # (assumed) EUR per 1000 km
    ),
    "sprinter": dict(
        model="Mercedes Sprinter 315 CDI L2H2",
        max_weight_kg=1231,
        max_volume_m3=10.5,
        cargo_length_m=3.27,               # (assumed) fits 10.5 m3
        cargo_width_m=1.78,                # (assumed)
        cargo_height_m=1.80,               # (assumed)
        fuel_l_per_km=round((9.0 + 9.1) / 2 / 100, 4),  # midpoint of 9.0-9.1 L/100km
        top_speed_kmh=161,
        avg_speed_kmh=48,                  # (assumed)
        wage_per_h=13.0,                   # (assumed)
        maintenance_per_1000km=120.0,      # (assumed)
    ),
    "man_tgl": dict(
        model="MAN TGL 12.190 box",
        max_weight_kg=5480,
        max_volume_m3=42.7,
        cargo_length_m=7.20,               # (assumed) the 9.20 m in the spec is the whole truck
        cargo_width_m=2.42,                # (assumed)
        cargo_height_m=2.45,               # (assumed)
        fuel_l_per_km=round((18 + 24) / 2 / 100, 4),    # midpoint of 18-24 L/100km
        top_speed_kmh=100,
        avg_speed_kmh=40,                  # (assumed)
        wage_per_h=16.0,                   # (assumed)
        maintenance_per_1000km=250.0,      # (assumed)
    ),
}

OUTPUT_FILE = "vehicles.csv"

# ===========================================================================


def main():
    rows = []
    vehicle_id = 1  # vehicle IDs run 1, 2, 3, ... in the order of FLEET

    for type_id, count in FLEET.items():
        for _ in range(count):
            # vehicle_id and type_id first, then all the specs of that model
            rows.append(dict(vehicle_id=vehicle_id, type_id=type_id, **MODELS[type_id]))
            vehicle_id += 1

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {OUTPUT_FILE} with {len(rows)} vehicles")


if __name__ == "__main__":
    main()