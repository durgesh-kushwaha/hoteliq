import pandas as pd


def create_stay_length(booking_data):
    if "stays_in_weekend_nights" in booking_data.columns and "stays_in_week_nights" in booking_data.columns:
        booking_data["stay_length"] = booking_data["stays_in_weekend_nights"] + booking_data["stays_in_week_nights"]
        print("Created feature: stay_length")
    else:
        print("Skipped stay_length because required night columns are missing.")

    return booking_data


def create_booking_date_features(booking_data):
    date_column = None

    if "reservation_status_date" in booking_data.columns:
        date_column = "reservation_status_date"
    elif "booking_date" in booking_data.columns:
        date_column = "booking_date"
    elif "arrival_date" in booking_data.columns:
        date_column = "arrival_date"

    if date_column is not None:
        booking_data[date_column] = pd.to_datetime(booking_data[date_column], errors="coerce")
        booking_data["booking_month"] = booking_data[date_column].dt.month
        booking_data["booking_year"] = booking_data[date_column].dt.year
        booking_data["booking_weekday"] = booking_data[date_column].dt.day_name()
        print("Created booking month, year, and weekday from:", date_column)
    elif "arrival_date_month" in booking_data.columns and "arrival_date_year" in booking_data.columns:
        booking_data["booking_month"] = booking_data["arrival_date_month"]
        booking_data["booking_year"] = booking_data["arrival_date_year"]
        print("Created booking month and year from arrival columns.")
        print("Skipped booking weekday because a full date column is missing.")
    else:
        print("Skipped booking date features because no usable date columns were found.")

    return booking_data


def create_weekend_booking(booking_data):
    if "booking_weekday" in booking_data.columns:
        booking_data["weekend_booking"] = "No"

        saturday_rows = booking_data["booking_weekday"] == "Saturday"
        sunday_rows = booking_data["booking_weekday"] == "Sunday"

        booking_data.loc[saturday_rows, "weekend_booking"] = "Yes"
        booking_data.loc[sunday_rows, "weekend_booking"] = "Yes"
        print("Created feature: weekend_booking")
    else:
        print("Skipped weekend_booking because booking_weekday is missing.")

    return booking_data


def create_revenue(booking_data):
    if "adr" in booking_data.columns and "stay_length" in booking_data.columns:
        booking_data["revenue"] = booking_data["adr"] * booking_data["stay_length"]
        print("Created feature: revenue")
    elif "price" in booking_data.columns and "stay_length" in booking_data.columns:
        booking_data["revenue"] = booking_data["price"] * booking_data["stay_length"]
        print("Created feature: revenue")
    else:
        print("Skipped revenue because price/ADR and stay length columns are missing.")

    return booking_data


def create_revenue_lost(booking_data):
    if "revenue" in booking_data.columns and "is_canceled" in booking_data.columns:
        booking_data["revenue_lost"] = 0.0

        canceled_rows = booking_data["is_canceled"] == 1
        booking_data.loc[canceled_rows, "revenue_lost"] = booking_data.loc[canceled_rows, "revenue"]
        print("Created feature: revenue_lost")
    else:
        print("Skipped revenue_lost because revenue or is_canceled is missing.")

    return booking_data


def create_advance_booking_days(booking_data):
    if "lead_time" in booking_data.columns:
        booking_data["advance_booking_days"] = booking_data["lead_time"]
        print("Created feature: advance_booking_days")
    else:
        print("Skipped advance_booking_days because lead_time is missing.")

    return booking_data


def create_occupancy_indicator(booking_data):
    if "is_canceled" in booking_data.columns:
        booking_data["occupancy_indicator"] = "Occupied"

        canceled_rows = booking_data["is_canceled"] == 1
        booking_data.loc[canceled_rows, "occupancy_indicator"] = "Not Occupied"
        print("Created feature: occupancy_indicator")
    elif "status" in booking_data.columns:
        booking_data["occupancy_indicator"] = booking_data["status"]
        print("Created feature: occupancy_indicator from status")
    else:
        print("Skipped occupancy_indicator because cancellation/status columns are missing.")

    return booking_data


def create_average_daily_rate(booking_data):
    if "adr" in booking_data.columns:
        booking_data["average_daily_rate"] = booking_data["adr"]
        print("Created feature: average_daily_rate")
    elif "price" in booking_data.columns:
        booking_data["average_daily_rate"] = booking_data["price"]
        print("Created feature: average_daily_rate")
    else:
        print("Skipped average_daily_rate because adr or price is missing.")

    return booking_data


def add_booking_features(booking_data):
    print("\nSTARTING FEATURE ENGINEERING")

    booking_data = create_stay_length(booking_data)
    booking_data = create_booking_date_features(booking_data)
    booking_data = create_weekend_booking(booking_data)
    booking_data = create_revenue(booking_data)
    booking_data = create_revenue_lost(booking_data)
    booking_data = create_advance_booking_days(booking_data)
    booking_data = create_occupancy_indicator(booking_data)
    booking_data = create_average_daily_rate(booking_data)

    print("\nFEATURE ENGINEERING COMPLETED")
    print("Dataset shape after feature engineering:")
    print(booking_data.shape)

    return booking_data
