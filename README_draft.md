# Dataset

Benchmark data for a furniture delivery problem (Capacitated VRP with special constraints):
one depot, 250 customers in Budapest, a mixed fleet of vans and a truck.
Both teams must use exactly these files so the final comparison is fair.

## Overview: what each file is for

| File | Purpose | What we get from it | Related files |
|---|---|---|---|
| `params.json` | Global rules of the problem | shift length, overtime multiplier, fuel price, packing mode, trip limits | none (read together with all others) |
| `vehicles.csv` | The fleet | capacity (weight, volume, cargo size), speed, fuel use, wage, maintenance cost per vehicle | `params.json` |
| `furniture_clean.csv` | The furniture list | size and weight of each piece | `orders.csv` |
| `places_pool.csv` | Candidate addresses | 1500 real Budapest addresses with coordinates | `locations.csv` |
| `locations.csv` | The depot and the customers | coordinates and address of every point, numbered 0..250 | `places_pool.csv`, `orders.csv`, `distances.csv` |
| `orders.csv` | What each customer ordered | pieces, total weight and volume, loading and unloading time | `locations.csv`, `furniture_clean.csv` |
| `distances.csv` | Distances between all points | km from every location to every other | `locations.csv` |

## How the files are connected

```
places_pool.csv --(250 picked + depot added)--> locations.csv ---------+
                                                    |                   |
                                          location_id               location_id
                                                    |                   |
furniture_clean.csv <--(item_ids)-- orders.csv      +----> distances.csv
                                                    (row i and column i = location_id i)

vehicles.csv + params.json   (independent: the fleet and the global rules)
```

| From | Column | To | Column |
|---|---|---|---|
| `orders.csv` | `location_id` | `locations.csv` | `location_id` |
| `orders.csv` | `item_ids` (several ids separated by `;`) | `furniture_clean.csv` | `id` |
| `locations.csv` | `place_id` (empty for the depot) | `places_pool.csv` | `place_id` |
| `distances.csv` | row and column ids | `locations.csv` | `location_id` |

## Files in detail

### `params.json`
- **Purpose:** the rules that belong to the whole problem and not to a single vehicle or customer. Keeping them in one place means both teams solve the same problem.
- **We get:** `shift_hours` (8), `overtime_multiplier` (2.0), `fuel_price_per_l`, `packing_mode` (1 = keep 10% free volume, 2 = box placement is part of the plan), `required_free_volume_ratio` (0.10), `min_customers_per_trip` and `max_customers_per_trip` (10 and 50), `allow_multiple_trips_per_vehicle`, `must_return_to_depot`, `loading_counts_as_work_time`, and unit labels.
- **Used for:** the cost (fuel price, overtime) and the constraints (shift, trip size, free volume).

### `vehicles.csv`
- **Purpose:** describes every vehicle in the fleet, one row per vehicle (5 now: 2 VW Caddy, 2 Mercedes Sprinter, 1 MAN TGL). The number of vehicles can be changed.
- **We get:** `max_weight_kg`, `max_volume_m3`, cargo `length/width/height`, `fuel_l_per_km`, `avg_speed_kmh`, `wage_per_h`, `maintenance_per_1000km`.
- **Used for:** capacity constraints, and the cost of a route (fuel, wage, maintenance, travel time).

### `furniture_clean.csv`
- **Purpose:** the list of furniture pieces that customers can order (168 pieces). It is the item table.
- **We get:** `id`, `name`, `length_m`, `width_m`, `height_m`, `weight_kg`, plus material, colour and country of origin.
- **Used for:** the size and weight of what is on a vehicle. Needed for packing mode 2 and for checking that long pieces fit in a vehicle.
- **Note:** the same piece id can appear in several orders.

### `places_pool.csv`
- **Purpose:** the source of customer addresses. It is only used to generate `locations.csv`, and the algorithms do not read it.
- **We get:** 1500 Budapest addresses from OpenStreetMap: `lat`, `lon`, `street`, `housenumber`, `postcode`, `district`, `full_address`.
- **Note:** it is kept in the repo unchanged, because OpenStreetMap changes over time and regenerating it would give different customers.

### `locations.csv`
- **Purpose:** the list of all points that vehicles visit: the depot and the 250 customers.
- **We get:** `location_id` (0 = depot, 1-250 = customers), `type`, `lat`, `lon`, address fields, `place_id` (link back to the pool).
- **Used for:** the numbering of everything else, and the coordinates for the visualization on a map.

### `orders.csv`
- **Purpose:** the demand. One order per customer.
- **We get:** `order_id`, `location_id` (which customer), `num_items`, `item_ids` (which pieces), `total_weight_kg`, `total_volume_m3`, `loading_time_min` (at the depot), `packing_time_min` (unloading at the customer).
- **Used for:** the load that must fit in a vehicle, and the time spent at each stop.

### `distances.csv`
- **Purpose:** distances between every pair of points, so the algorithm does not compute them again and again.
- **We get:** a 251 x 251 matrix in km. Row `i` and column `i` are `location_id` `i`.
- **Used for:** fuel cost, maintenance cost, driving time (and so wage and overtime).
- **Note:** the values are currently straight-line distance x 1.3. They can be replaced by real road distances (for example from OSRM) under the same file name and format.

## What is real and what is assumed

- **From sources:** vehicle payload, volume, fuel range and top speed; addresses and coordinates (OpenStreetMap); furniture sizes and weights (Amazon furniture sample).
- **Assumed:** fuel price, driver wages, maintenance cost, average speeds, cargo width and height of the vehicles, loading and unloading time formulas, number of pieces per order, depot position, and the road-distance factor of 1.3.

## Units

Distances in km, times in minutes (shift in hours), weights in kg, lengths in metres, volumes in m3, money in EUR.

## Scripts

Each generator has a commented `SETTINGS` block at the top and uses fixed seeds, so the same input gives the same output.

| Script | Creates |
|---|---|
| `make_vehicles.py` | `vehicles.csv` (change the number of vehicles in `FLEET`) |
| `make_locations.py` | `locations.csv` |
| `make_orders.py` | `orders.csv` |
| `make_distances.py` | `distances.csv` |
| `validate_dataset.py` | checks that all files are consistent with each other |

Run order: `make_vehicles.py`, `make_locations.py`, `make_orders.py`, `make_distances.py`, then `validate_dataset.py`.

## Credits

Addresses: (c) OpenStreetMap contributors, ODbL licence, https://www.openstreetmap.org/copyright
