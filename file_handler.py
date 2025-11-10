import pandas as pd
from datetime import datetime

def save_to_csv(reviews_data, filename = None):
    if filename and not filename.endswith('.csv'):
        filename += '.csv'

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{timestamp}_reviews_data.csv"

    df = pd.DataFrame(reviews_data)
    df.to_csv(filename, index=False)
    print(f"Data saved to '{filename}'.")
