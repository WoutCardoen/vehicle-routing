# Vehicle Routing

A route optimizer for truck pickups between branches. A receiving branch orders articles it's short on; a truck leaves the depot, collects those articles from other branches that have them in stock, and delivers them to the receiver. The tool finds the **fastest combination of branches and pickup order**, based on real drive times.

Available as a **Streamlit web app** and as a terminal script.

## Features

- Reads stock and demand from Excel files (upload in the browser)
- Precheck: reports articles with insufficient total stock and continues with what's available
- Quantities can be split across branches (e.g. 5 from one branch, 15 from another)
- Exact optimization: tries every valid branch combination and every pickup order
- Scoring on real drive times, adjusted for trucks, plus loading time per stop
- Coordinates and drive times are cached, so the APIs are only called once

## How it works

1. **Load data:** stock per branch per article, and the order (articles, quantities, receiving branch).
2. **Precheck:** checks whether the other branches together have enough stock for each article. The receiver's own stock doesn't count.
3. **Combinations:** finds every set of branches that together can cover the order. The receiver is excluded as a pickup point.
4. **Route order:** for each set, tries every pickup order: depot → pickups → receiver.
5. **Scoring:**
   `total time = drive time × TRUCK_FACTOR + LOAD_TIME × number of pickups`
   The truck factor (default 1.2) accounts for trucks being slower than cars; the loading time (default 20 min) penalizes extra stops.
6. **Result:** the fastest route, with its branches, order and total time.

## Project structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit web interface |
| `main.py` | Terminal version |
| `config.py` | Settings: depot location, truck factor, loading time |
| `data_loader.py` | Reads the stock and demand files |
| `precheck.py` | Checks stock availability per article |
| `combination_finder.py` | Finds branch combinations that cover the order |
| `route_optimizer.py` | Coordinates, time matrix and route scoring |

## Tech stack

- **Python** with **Streamlit** for the web interface
- **pandas** / **openpyxl** to read the Excel input
- **geopy (Nominatim / OpenStreetMap)** to geocode branch addresses, free but rate-limited
- **Google Maps Distance Matrix API** (`googlemaps` package) for real drive times

## Google Cloud setup

The app needs a Google Maps API key, both in the terminal version and in Streamlit.

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Distance Matrix API**
3. Link a billing account. Google requires one even for the free tier.
4. Create an API key and set it as an environment variable (never put it in the code):
   ```
   setx GOOGLE_MAPS_KEY "your-key"
   ```
   Restart your terminal afterwards, so the variable is picked up.
5. On the first run, drive times are fetched and cached in `times.json`; coordinates are cached in `coords.json`.

The matrix grows with the square of the number of branches (20 branches = 400 pairs), so keep an eye on the free monthly quota. Delete `coords.json` and `times.json` after changing addresses or branches, so they're rebuilt.

## Run it

```
cd route_optimizer_project
pip install -r requirements.txt
```

**Web app:**
```
streamlit run app.py
```
Opens in the browser at `http://localhost:8501`. Upload a stock file and a demand file.

**Terminal:**
```
python main.py
```

**Note:** `coords.json` and `times.json` aren't included in this repo because they contain real locations. They're generated on the first run with the API key, or you can add your own in the same format.

## Limitations

- Brute force grows fast with the number of branches in a combination. Fine for typical orders (2–4 pickups), slow beyond ~8.
- Drive times are car times from Google, adjusted by a fixed truck factor rather than real truck routing.
- One receiving branch per order.

## Possible improvements

- Fetch drive times per order instead of a full matrix, for many branches
- A nearest-neighbour heuristic for large combinations
- Real truck routing instead of a fixed factor