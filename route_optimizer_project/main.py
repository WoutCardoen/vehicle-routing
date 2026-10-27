from combination_finder import find_possible_combinations, trimmed_combinations
from config import DEMAND_FILE, STOCK_FILE
from data_loader import load_demand, load_stock
from precheck import global_precheck
from route_optimizer import build_coords, find_optimal_combinations ,build_time_matrix


def main():
    stock, branch_info = load_stock(STOCK_FILE)
    demand, receiver = load_demand(DEMAND_FILE)
    demand, shortfalls = global_precheck(branch_info, demand, stock, receiver)
    possible_combinations = find_possible_combinations(
        branch_info, demand, stock, receiver
    )
    minimal_combinations = trimmed_combinations(
        possible_combinations, demand, stock
    )
    coords = build_coords(branch_info)
    times = build_time_matrix(coords)
    optimal = find_optimal_combinations(minimal_combinations, times, receiver)
    print(f"Optimal combinations: {optimal}")

if __name__ == "__main__":
    main()
