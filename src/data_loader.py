import pandas as pd
from pathlib import Path


def load_student_data():
    """Load student academic records from the CSV file."""

    project_root = Path(__file__).resolve().parent.parent
    file_path = project_root / "data" / "student_records.csv"

    if not file_path.exists():
        raise FileNotFoundError("Student records dataset not found.")

    data = pd.read_csv(file_path)

    return data


if __name__ == "__main__":
    records = load_student_data()

    print("Student Success AI - Data Loader")
    print("--------------------------------")
    print(records.head())
    print("\nDataset loaded successfully!")