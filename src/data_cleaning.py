import pandas as pd


def column_is_text(booking_data, column_name):
    column_type = str(booking_data[column_name].dtype)

    if column_type == "object":
        return True

    if column_type == "str":
        return True

    if "string" in column_type:
        return True

    return False


def column_is_number(booking_data, column_name):
    column_type = str(booking_data[column_name].dtype)

    if "int" in column_type:
        return True

    if "float" in column_type:
        return True

    return False


def column_is_date(booking_data, column_name):
    column_type = str(booking_data[column_name].dtype)

    if "datetime" in column_type:
        return True

    return False


def remove_duplicate_rows(booking_data):
    print("\nCleaning step: Remove duplicate rows")
    print("Why: Duplicate rows can count the same booking more than once.")

    rows_before = booking_data.shape[0]
    booking_data = booking_data.drop_duplicates()
    rows_after = booking_data.shape[0]

    print("Rows before:", rows_before)
    print("Rows after:", rows_after)
    print("Duplicate rows removed:", rows_before - rows_after)

    return booking_data


def clean_text_columns(booking_data):
    print("\nCleaning step: Clean text columns")
    print("Why: Extra spaces and different letter cases can create duplicate categories.")

    for column_name in booking_data.columns:
        if column_is_text(booking_data, column_name):
            booking_data[column_name] = booking_data[column_name].astype(str)
            booking_data[column_name] = booking_data[column_name].str.strip()
            booking_data[column_name] = booking_data[column_name].str.title()

            missing_text_mask = booking_data[column_name] == "Nan"
            booking_data.loc[missing_text_mask, column_name] = pd.NA

    print("Text columns were cleaned.")
    return booking_data


def convert_date_columns(booking_data):
    print("\nCleaning step: Convert date columns")
    print("Why: Date columns should be in date format for monthly and seasonal analysis.")

    for column_name in booking_data.columns:
        lower_column_name = column_name.lower()

        is_full_date_column = False

        if lower_column_name == "reservation_status_date":
            is_full_date_column = True

        if lower_column_name == "booking_date":
            is_full_date_column = True

        if lower_column_name == "arrival_date":
            is_full_date_column = True

        if is_full_date_column:
            booking_data[column_name] = pd.to_datetime(booking_data[column_name], errors="coerce")
            print("Converted to date:", column_name)

    return booking_data


def convert_numeric_columns(booking_data):
    print("\nCleaning step: Convert numeric columns")
    print("Why: Numeric columns should be numbers so Python can calculate totals and averages.")

    possible_numeric_columns = [
        "adr",
        "price",
        "stays_in_weekend_nights",
        "stays_in_week_nights",
        "adults",
        "children",
        "babies",
        "lead_time",
        "days_in_waiting_list",
        "is_canceled",
        "previous_cancellations",
        "previous_bookings_not_canceled",
        "booking_changes",
        "required_car_parking_spaces",
        "total_of_special_requests",
    ]

    for column_name in possible_numeric_columns:
        if column_name in booking_data.columns:
            booking_data[column_name] = pd.to_numeric(booking_data[column_name], errors="coerce")
            print("Converted to numeric:", column_name)

    return booking_data


def fill_missing_values(booking_data):
    print("\nCleaning step: Handle missing values")
    print("Why: Missing values can break calculations and charts.")

    for column_name in booking_data.columns:
        missing_count = booking_data[column_name].isnull().sum()

        if missing_count > 0:
            if column_is_text(booking_data, column_name):
                booking_data[column_name] = booking_data[column_name].fillna("Unknown")
                print(column_name, "- filled missing text values with Unknown.")
            elif column_is_number(booking_data, column_name):
                median_value = booking_data[column_name].median()
                booking_data[column_name] = booking_data[column_name].fillna(median_value)
                print(column_name, "- filled missing numeric values with median.")
            elif column_is_date(booking_data, column_name):
                most_common_value = booking_data[column_name].mode()

                if len(most_common_value) > 0:
                    booking_data[column_name] = booking_data[column_name].fillna(most_common_value[0])
                    print(column_name, "- filled missing date values with most common date.")
                else:
                    print(column_name, "- date values were missing, but no common date was available.")
            else:
                booking_data[column_name] = booking_data[column_name].fillna("Unknown")
                print(column_name, "- filled missing values with Unknown.")

    return booking_data


def remove_impossible_values(booking_data):
    print("\nCleaning step: Remove impossible values")
    print("Why: Negative prices, negative nights, and negative guest counts do not make business sense.")

    rows_before = booking_data.shape[0]

    possible_positive_columns = [
        "adr",
        "price",
        "average_daily_rate",
        "stays_in_weekend_nights",
        "stays_in_week_nights",
        "adults",
        "children",
        "babies",
        "lead_time",
        "days_in_waiting_list",
    ]

    for column_name in possible_positive_columns:
        if column_name in booking_data.columns:
            booking_data = booking_data[booking_data[column_name] >= 0]
            print("Checked non-negative values for:", column_name)

    rows_after = booking_data.shape[0]

    print("Rows before impossible value check:", rows_before)
    print("Rows after impossible value check:", rows_after)
    print("Rows removed:", rows_before - rows_after)

    return booking_data


def clean_booking_data(booking_data):
    print("\nSTARTING DATA CLEANING")

    booking_data = remove_duplicate_rows(booking_data)
    booking_data = clean_text_columns(booking_data)
    booking_data = convert_date_columns(booking_data)
    booking_data = convert_numeric_columns(booking_data)
    booking_data = fill_missing_values(booking_data)
    booking_data = remove_impossible_values(booking_data)

    print("\nDATA CLEANING COMPLETED")
    print("Final dataset shape:")
    print(booking_data.shape)

    return booking_data
