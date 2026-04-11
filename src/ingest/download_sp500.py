from pathlib import Path
import shutil
import kagglehub

DATASET_SLUG = "gauravmehta13/sp-500-stock-prices"  # from your Kaggle screenshot
TARGET_DIR = Path("data_raw/sp500_stock_prices")

def main():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # Downloads dataset to a cached folder and returns that path
    downloaded_path = Path(kagglehub.dataset_download(DATASET_SLUG))
    print(f"Downloaded to cache: {downloaded_path}")

    # Copy all files from the downloaded path into our project folder
    # (KaggleHub may return a folder containing the csv)
    for item in downloaded_path.rglob("*"):
        if item.is_file():
            dest = TARGET_DIR / item.name
            shutil.copy2(item, dest)
            print(f"Saved: {dest}")

    print("\nDone.")
    print(f"Project raw data folder: {TARGET_DIR.resolve()}")

if __name__ == "__main__":
    main()
