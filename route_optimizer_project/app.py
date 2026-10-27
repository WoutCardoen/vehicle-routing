import streamlit as st
import pydeck as pdk
from route_optimizer import get_route_path
from data_loader import load_stock, load_demand
from precheck import global_precheck
from combination_finder import find_possible_combinations, trimmed_combinations
from route_optimizer import build_coords, build_time_matrix, find_optimal_combinations
from config import HOME

st.set_page_config(
    page_title="Truck Route Optimizer",
    page_icon="truck",
    layout="wide",
)

# ---------------------------------------------------------------
# Sidebar: inputs live here so the main area is all results
# ---------------------------------------------------------------
with st.sidebar:
    st.header("Inputs")
    st.caption("Upload the two exports, then the route appears on the right.")

    stock_file = st.file_uploader("Stock file (LQUA export)", type=["xlsx"])
    demand_file = st.file_uploader("Demand file", type=["xlsx"])

    st.divider()
    st.caption(
        "The truck leaves Mechelen, collects the ordered articles from other "
        "branches, and delivers to the branch that placed the order."
    )

# ---------------------------------------------------------------
# Main area
# ---------------------------------------------------------------
st.title("Truck Route Optimizer")

if not (stock_file and demand_file):
    st.info("Upload a stock file and a demand file in the sidebar to plan a route.")
    st.stop()

# --- load ---
stock, branch_info = load_stock(stock_file)
demand, receiver = load_demand(demand_file)

# Keep letters separate from branch IDs used by the route calculation.
def branch_letter(index):
    letters = ""
    while index >= 0:
        index, remainder = divmod(index, 26)
        letters = chr(ord("A") + remainder) + letters
        index -= 1
    return letters


# --- precheck: split satisfiable demand from shortfalls ---
demand, shortfalls = global_precheck(branch_info, demand, stock, receiver)
for artikel, info in shortfalls.items():
    demand[artikel] = info["totaal_voorraad"]

# --- optimise ---
possible = find_possible_combinations(branch_info, demand, stock, receiver)
minimal = trimmed_combinations(possible, demand, stock)

coords = build_coords(branch_info)
times = build_time_matrix(coords)
optimal = find_optimal_combinations(minimal, times, receiver)

# Normalize cached IDs to integers before sorting for stable letters.
branch_ids = sorted(int(branch_id) for branch_id in coords if branch_id != HOME)
branch_labels = {
    branch_id: f"Testvestiging {branch_letter(index)}"
    for index, branch_id in enumerate(branch_ids)
}


def display_name(branch_id):
    return branch_labels[int(branch_id)]


# ---------------------------------------------------------------
# Results
# ---------------------------------------------------------------
st.subheader(f"Order for branch {display_name(receiver)}")

top = st.columns(3)
top[0].metric("Articles ordered", len(demand))
top[1].metric("Short articles", len(shortfalls))

if not optimal:
    top[2].metric("Route", "-")
    st.error(
        "No route covers this order. The branches other than "
        f"{display_name(receiver)} can't supply every article. Reduce the demand "
        "or check stock levels."
    )
    st.stop()

pickups = list(optimal.keys())[0]
total_time = list(optimal.values())[0]
route = [HOME] + list(pickups) + [receiver]

if st.button("Show route on map"):
    path = get_route_path(route, coords)

    # Keep the depot label unnumbered and list it only once.
    stops = []
    stop_number = 0
    depot_added = False
    for stop in route:
        if stop == HOME:
            if depot_added:
                continue
            label = "Mechelen depot"
            tooltip = label
            pixel_offset = [-35, -24]
            depot_added = True
        else:
            stop_number += 1
            name = display_name(stop)
            label = f"{stop_number}. {name}"
            tooltip = name
            horizontal_offset = 20 if stop_number % 2 else -20
            vertical_offset = -24 if stop_number % 2 else 24
            pixel_offset = [horizontal_offset, vertical_offset]
        stops.append({
            "lat": coords[stop][0],
            "lon": coords[stop][1],
            "label": label,
            "tooltip": tooltip,
            "pixel_offset": pixel_offset,
        })

    line_layer = pdk.Layer(
        "PathLayer",
        data=[{"path": [[lon, lat] for lat, lon in path]}],
        get_path="path",
        get_width=4,
        get_color=[0, 100, 200],
        width_min_pixels=3,
    )
    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=stops,
        get_position=["lon", "lat"],
        get_radius=1200,
        get_fill_color=[200, 30, 30],
    )
    text_layer = pdk.Layer(
        "TextLayer",
        data=stops,
        get_position=["lon", "lat"],
        get_text="label",
        get_size=14,
        get_color=[255, 255, 255],
        get_pixel_offset="pixel_offset",
    )
    st.pydeck_chart(pdk.Deck(
        layers=[line_layer, point_layer, text_layer],
        initial_view_state=pdk.ViewState(
            latitude=coords[HOME][0],
            longitude=coords[HOME][1],
            zoom=7,
        ),
        tooltip={"text": "{tooltip}"},
    ))
top[2].metric("Total time", f"{round(total_time)} min")

st.divider()

left, right = st.columns([2, 3])

with left:
    st.markdown("**Pickup branches**")
    st.caption(f"{len(pickups)} stop(s), in visiting order")
    for i, branch in enumerate(pickups, start=1):
        st.markdown(f"{i}. **{display_name(branch)}**")

with right:
    st.markdown("**Full route**")
    route = [HOME] + list(pickups) + [receiver]
    labels = []
    for stop in route:
        if stop == HOME:
            labels.append("Mechelen depot (start)")
        elif stop == receiver:
            labels.append(f"{display_name(stop)} (deliver)")
        else:
            labels.append(f"Pickup {display_name(stop)}")
    st.markdown("  \n v  \n".join(labels))

if shortfalls:
    st.divider()
    with st.expander(f"{len(shortfalls)} article(s) short across all branches"):
        st.caption(
            "Taking the full available amount for these - the order can't be "
            "filled completely."
        )
        for artikel, info in shortfalls.items():
            st.write(
                f"{artikel}: ordered {info['vraag']}, "
                f"available {info['totaal_voorraad']}"
            )