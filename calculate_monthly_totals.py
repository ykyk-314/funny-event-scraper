import pandas as pd
import os

def extract_year_month(date_column):
    """Extract year and month from a date column with format 'YYYY年MM月DD日（曜日）'"""
    return date_column.str.extract(r"(\d{4}年\d{2}月)")[0]

def calculate_monthly_totals(input_csv, output_csv):
    """Calculate monthly totals and counts for 公演日 and 購入日 based on枚数 and save to a new CSV file."""
    # Check if input file exists
    if not os.path.exists(input_csv):
        print(f"Input file '{input_csv}' does not exist.")
        return

    # Load the CSV file
    df = pd.read_csv(input_csv, encoding="utf-8-sig")

    # Extract year-month from 公演日 and 購入日
    df["公演年月"] = extract_year_month(df["公演日"])
    df["購入年月"] = extract_year_month(df["購入日"])

    df["枚数"] = pd.to_numeric(df["枚数"], errors="coerce")

    # Group by 公演年月 and 購入年月 and calculate totals and counts
    public_monthly_totals = df.groupby("公演年月").agg(
        公演日ベース合計金額=("合計金額", "sum"), 公演日ベース件数=("枚数", "sum")
    ).reset_index()
    purchase_monthly_totals = df.groupby("購入年月").agg(
        購入日ベース合計金額=("合計金額", "sum"), 購入日ベース件数=("枚数", "sum")
    ).reset_index()

    # Merge both results on 年月
    monthly_totals = pd.merge(public_monthly_totals, purchase_monthly_totals, left_on="公演年月", right_on="購入年月", how="outer").fillna(0)

    # Drop redundant column and rename
    monthly_totals.drop(columns=["購入年月"], inplace=True)
    monthly_totals.rename(columns={"公演年月": "年月"}, inplace=True)

    # Convert totals to integers (no decimals)
    monthly_totals["公演日ベース合計金額"] = monthly_totals["公演日ベース合計金額"].astype(int)
    monthly_totals["購入日ベース合計金額"] = monthly_totals["購入日ベース合計金額"].astype(int)
    monthly_totals["公演日ベース件数"] = monthly_totals["公演日ベース件数"].astype(int)
    monthly_totals["購入日ベース件数"] = monthly_totals["購入日ベース件数"].astype(int)

    # Save the result to a new CSV file
    monthly_totals.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"Monthly totals saved to '{output_csv}'.")

if __name__ == "__main__":
    # Define input and output file paths
    input_csv = "purchase_history.csv"  # Replace with the correct path if necessary
    output_csv = "monthly_totals.csv"  # Output file name

    # Execute the calculation
    calculate_monthly_totals(input_csv, output_csv)
