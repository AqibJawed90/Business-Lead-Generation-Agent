import os
import pandas as pd


def export_leads(leads: list[dict], filename: str = "leads.csv") -> str:
    """Business leads ko CSV file mein save karta hai."""

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, filename)

    columns = [
        "title",
        "url",
        "domain",
        "content",
    ]

    df = pd.DataFrame(leads)

    # Missing columns ko bhi include karna
    for column in columns:
        if column not in df.columns:
            df[column] = ""

    df = df[columns]
    df.to_csv(filepath, index=False, encoding="utf-8-sig")

    return filepath
