def get_stock(stock, artikel, vestiging):
    return stock.get((artikel, vestiging), 0)



def global_precheck(branch_info, demand, stock, receiver):
    insufficient_stock = {}
    updated_demand = {}

    for artikel, vraag in demand.items():
        total_stock = sum(
            get_stock(stock, artikel, vestiging) 
            for vestiging in branch_info
            if vestiging != receiver  # Exclude the receiver from stock calculation
        )
        if total_stock < vraag:
            insufficient_stock[artikel] = {
                "vraag": vraag,
                "totaal_voorraad": total_stock,
            }
        else:
            updated_demand[artikel] = vraag

    return updated_demand, insufficient_stock
