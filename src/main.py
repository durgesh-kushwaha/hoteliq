from data_cleaning import clean_booking_data
from eda import run_eda
from feature_engineering import add_booking_features
from utils import load_booking_data, save_processed_data, show_data_understanding
from visualization import create_all_charts


raw_folder_path = "data/raw"
processed_file_path = "data/processed/cleaned_hotel_bookings.csv"
images_folder_path = "images"


booking_data = load_booking_data(raw_folder_path)

if booking_data is not None:
    show_data_understanding(booking_data)

    cleaned_data = clean_booking_data(booking_data)

    final_data = add_booking_features(cleaned_data)

    run_eda(final_data)

    create_all_charts(final_data, images_folder_path)

    save_processed_data(final_data, processed_file_path)
else:
    print("Project stopped because no dataset was available.")
