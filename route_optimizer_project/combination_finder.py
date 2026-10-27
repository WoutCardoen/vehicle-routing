from itertools import combinations
from config import MAX_COMBINATION_SIZE
from precheck import get_stock


def is_feasible(branches, demand, stock):
    for artikel, vraag in demand.items():
        total_stock = sum(
            get_stock(stock, artikel, vestiging) for vestiging in branches
        )
        if total_stock < vraag:
            return False
    return True


def possible_branches_for_articles(branches, demand, stock):
    possible_branches = set()
    for artikel in demand:
        for vestiging in branches:
            if get_stock(stock, artikel, vestiging) > 0:
                possible_branches.add(vestiging)
    return possible_branches


def find_possible_combinations(branches, demand, stock, receiver):
    print("demand going into combinations:", demand)
    print("receiver:", receiver)
    possible_combinations = []
    candidate_branches = possible_branches_for_articles(branches, demand, stock)
    candidate_branches = [b for b in candidate_branches if b != receiver]
    max_size = min(MAX_COMBINATION_SIZE, len(candidate_branches))
    print("candidates:", candidate_branches)
    print("MAX_COMBINATION_SIZE:", MAX_COMBINATION_SIZE)
    for size in range(1, max_size + 1):
        for combination in combinations(candidate_branches, size):
            if is_feasible(combination, demand, stock):
                possible_combinations.append(combination)
    return possible_combinations


def is_minimal(combination, demand, stock):
    for branch in combination:
        reduced_combination = [
            candidate for candidate in combination if candidate != branch
        ]
        if is_feasible(reduced_combination, demand, stock):
            return False
    return True


def trimmed_combinations(possible_combinations, demand, stock):
    trimmed = []
    for combination in possible_combinations:
        if is_minimal(combination, demand, stock):
            trimmed.append(combination)
    return trimmed
