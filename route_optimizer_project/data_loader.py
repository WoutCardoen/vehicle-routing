import pandas as pd


def load_stock(path):
    df = pd.read_excel(r"C:\Users\woutc\OneDrive\Documenten\code\vehicle routing\LQUA.XLSX")
    columns = [
        "Artikel",
        "Vestiging",
        "voorraad beschikbaar",
        "naam vestiging",
        "plaats",
        "straat",
    ]
    df = df[columns]

    stock = (
        df.groupby(["Artikel", "Vestiging"])["voorraad beschikbaar"]
        .sum()
        .to_dict()
    )
    branch_info = (
        df.drop_duplicates(subset="Vestiging")
        .set_index("Vestiging")[["naam vestiging", "plaats", "straat"]]
        .to_dict(orient="index")
    )
    return stock, branch_info


def load_demand(path):
    df = pd.read_excel(r"C:\Users\woutc\OneDrive\Documenten\code\vehicle routing\demand.XLSX")
    demand = df.groupby("Artikel")["vraag"].sum()
    demand = demand[demand != 0]
    receiver = int(df["Vestiging"].iloc[0])
    return demand.to_dict(), receiver
