"""Loads the inventory Excel file into a clean DataFrame.

The source file has a title/banner in the first few rows before the real
header row, so we skip down to where the actual table starts.
"""
import pandas as pd

EXCEL_PATH = "inventory_data.xlsx"


def load_inventory(path: str = EXCEL_PATH) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=0, header=5, usecols="B:I")
    df.columns = [
        "product_id",
        "product_name",
        "opening_stock",
        "purchase_stock_in",
        "units_sold",
        "hand_in_stock",
        "cost_price_per_unit_usd",
        "cost_price_total_usd",
    ]
    df = df.dropna(how="all").reset_index(drop=True)
    return df


def schema_description(df: pd.DataFrame) -> str:
    """Plain-text schema summary fed to the LLM so it knows what's queryable."""
    lines = ["The DataFrame is called `df` and has these columns:"]
    for col in df.columns:
        sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else "N/A"
        lines.append(f"  - {col} ({df[col].dtype}), e.g. {sample!r}")
    lines.append(f"Total rows: {len(df)}")
    return "\n".join(lines)


if __name__ == "__main__":
    df = load_inventory()
    print(df.head())
    print(schema_description(df))
