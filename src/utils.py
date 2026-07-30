import os

import pandas as pd


def find_data_file(raw_folder_path):
    """Find the first CSV or Excel file inside the raw data folder."""

    if os.path.exists(raw_folder_path) == False:
        print("The raw data folder does not exist.")
        return None

    file_names = os.listdir(raw_folder_path)

    for file_name in file_names:
        lower_file_name = file_name.lower()

        if lower_file_name.endswith(".csv"):
            return os.path.join(raw_folder_path, file_name)

        if lower_file_name.endswith(".xlsx"):
            return os.path.join(raw_folder_path, file_name)

        if lower_file_name.endswith(".xls"):
            return os.path.join(raw_folder_path, file_name)

    return None


def load_booking_data(raw_folder_path):
    """Load a CSV or Excel file without changing the original file."""

    data_file_path = find_data_file(raw_folder_path)

    if data_file_path is None:
        print("No CSV or Excel file was found inside data/raw/.")
        print("Please place the raw hotel or Airbnb booking dataset there.")
        return None

    print("Dataset found:")
    print(data_file_path)

    lower_file_path = data_file_path.lower()

    if lower_file_path.endswith(".csv"):
        booking_data = pd.read_csv(data_file_path)
        print("The dataset was loaded as a CSV file.")
        return booking_data

    if lower_file_path.endswith(".xlsx") or lower_file_path.endswith(".xls"):
        booking_data = pd.read_excel(data_file_path)
        print("The dataset was loaded as an Excel file.")
        return booking_data

    print("The file type is not supported.")
    return None


def show_data_understanding(booking_data):
    """Print simple information to understand the dataset."""

    print("\nFIRST 5 ROWS")
    print(booking_data.head())
    print("These rows show what the dataset looks like at the beginning.")

    print("\nLAST 5 ROWS")
    print(booking_data.tail())
    print("These rows show what the dataset looks like at the end.")

    print("\nDATA SHAPE")
    print(booking_data.shape)
    print("The first number is rows. The second number is columns.")

    print("\nCOLUMN NAMES")
    print(booking_data.columns)
    print("These are the available fields in the dataset.")

    print("\nDATA TYPES")
    print(booking_data.dtypes)
    print("Data types help us know which columns are text, numbers, or dates.")

    print("\nMISSING VALUES")
    print(booking_data.isnull().sum())
    print("Missing values show where information is not available.")

    print("\nDUPLICATE ROWS")
    duplicate_count = booking_data.duplicated().sum()
    print(duplicate_count)
    print("Duplicate rows may repeat the same booking more than once.")

    print("\nBASIC STATISTICS")
    print(booking_data.describe(include="all"))
    print("Basic statistics summarize numeric and text columns.")


def save_processed_data(booking_data, output_file_path):
    """Save the cleaned dataset into the processed folder."""

    output_folder = os.path.dirname(output_file_path)

    if os.path.exists(output_folder) == False:
        os.makedirs(output_folder)

    booking_data.to_csv(output_file_path, index=False)
    print("\nCleaned data saved here:")
    print(output_file_path)
