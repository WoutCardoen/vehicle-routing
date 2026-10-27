import time
import json
from itertools import permutations
import googlemaps 
import os
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from config import HOME, HOME_COORDS, TRUCK_FACTOR, LOAD_TIME


def build_coords(branch_info):
    # already geocoded before -> load from file
    print(">>> build_coords: checking for coords.json")
    if os.path.exists("coords.json"):
        with open("coords.json") as f:
            data = json.load(f)
        coords = {int(k) if k.isdigit() else k: tuple(v) for k, v in data.items()}
        coords[HOME] = HOME_COORDS
        return coords

    # first time -> geocode each branch once
    geocoder = Nominatim(user_agent="sncb_route_tool", timeout=10)
    coords = {}
    for vestiging, info in branch_info.items():
        query = f"{info['straat']}, {info['plaats']}, Belgium"
        location = geocoder.geocode(query)
        if location:
            coords[vestiging] = (location.latitude, location.longitude)
        else:
            print("NIET gevonden:", vestiging, query)
        time.sleep(1)

    coords[HOME] = HOME_COORDS
    print(">>> build_coords stored HOME as:", repr(HOME))

    # save so we never geocode again
    with open("coords.json", "w") as f:
        json.dump({str(k): v for k, v in coords.items()}, f)
    print("Geocoding done, saved to coords.json")
    return coords


def travel_time_between_branches(branch1, branch2, times):
    return times.get((branch1, branch2), times.get((branch2, branch1), float("inf")))

def total_travel_time(combination, times, receiver):
    lowest_time = float("inf")
    for permutation in permutations(combination):
        route = [HOME] + list(permutation) + [receiver]
        total_time = sum(
            travel_time_between_branches(route[index], route[index + 1], times)
            for index in range(len(route) - 1))
        total_time = total_time * TRUCK_FACTOR + LOAD_TIME * len(combination)
        lowest_time = min(lowest_time, total_time)
    return lowest_time


def find_optimal_combinations(combinations_to_check, times, receiver):
    if not combinations_to_check:
        print("No feasible combinations found (try raising MAX_COMBINATION_SIZE)")
        return {}
    optimal_combinations = {}
    lowest_time = float("inf")
    print("biggest combination size:", max(len(c) for c in combinations_to_check))
    for combination in combinations_to_check:
        route_time = total_travel_time(combination, times, receiver)
        if route_time < lowest_time:
            lowest_time = route_time
            optimal_combinations = {combination: route_time}
        elif route_time == lowest_time:
            optimal_combinations[combination] = route_time
    return optimal_combinations

def build_time_matrix(coords, filename="times.json"): #the building of the time matrix is disabled, because of api costs
    # --- cache path: file already exists, load it, no Google call ---
    if os.path.exists(filename):
        print("loading time matrix from file")
        with open(filename, "r") as f:
            string_keyed = json.load(f)

        times = {}
        for key, minutes in string_keyed.items():
            b1_str, b2_str = key.split("|")
            b1 = int(b1_str) if b1_str.isdigit() else b1_str
            b2 = int(b2_str) if b2_str.isdigit() else b2_str
            times[(b1, b2)] = minutes
        return times

    # --- no cache: build it from Google (disabled for now) ---
    # print("building time matrix")
    # gmaps = googlemaps.Client(
    #     key=os.environ["GOOGLE_MAPS_KEY"],
    #     retry_over_query_limit=False,
    # )
    # points = list(coords.keys())
    # latlngs = [coords[p] for p in points]
    # times = {}
    # for start in range(0, len(points), 5):          # origins in chunks of 5
    #     origin_chunk = latlngs[start:start + 5]
    #     origin_keys = points[start:start + 5]
    #     result = gmaps.distance_matrix(
    #         origins=origin_chunk,
    #         destinations=latlngs,                    # all destinations every time
    #         mode="driving",
    #     )
    #     for i, row in enumerate(result["rows"]):
    #         for j, cell in enumerate(row["elements"]):
    #             if cell["status"] == "OK":
    #                 times[(origin_keys[i], points[j])] = cell["duration"]["value"] / 60
    #             else:
    #                 print("geen route:", origin_keys[i], "->", points[j])
    # # --- save to cache so next run skips Google ---
    # string_keyed = {}
    # for (b1, b2), minutes in times.items():
    #     string_keyed[f"{b1}|{b2}"] = minutes
    # with open(filename, "w") as f:
    #     json.dump(string_keyed, f)
    # return times
    raise FileNotFoundError("times.json not found and Google build is disabled")


def get_route_path(route, coords):
    gmaps = googlemaps.Client(
        key=os.environ["GOOGLE_MAPS_KEY"],
        retry_over_query_limit=False,
    )
    origin = coords[route[0]]           # depot
    destination = coords[route[-1]]     # receiver
    waypoints = [coords[stop] for stop in route[1:-1]]   # the pickups, in order

    result = gmaps.directions(
        origin=origin,
        destination=destination,
        waypoints=waypoints,
        optimize_waypoints=False,        # keep YOUR order, don't let Google reorder
        mode="driving",
    )

    # decode the road-following polyline into lat/lon points
    points = googlemaps.convert.decode_polyline(
        result[0]["overview_polyline"]["points"]
    )
    return [[p["lat"], p["lng"]] for p in points]