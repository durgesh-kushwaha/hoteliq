def show_total_bookings(booking_data):
    total_bookings = booking_data.shape[0]
    print("\nTotal bookings:", total_bookings)
    print("This shows the total number of booking records in the dataset.")


def show_monthly_bookings(booking_data):
    if "booking_month" in booking_data.columns:
        monthly_bookings = booking_data["booking_month"].value_counts().sort_index()
        print("\nMonthly bookings")
        print(monthly_bookings)
        print("This shows which months have more bookings.")
    else:
        print("\nSkipped monthly bookings because booking_month is missing.")


def show_total_revenue(booking_data):
    if "revenue" in booking_data.columns:
        total_revenue = booking_data["revenue"].sum()
        print("\nTotal revenue:", total_revenue)
        print("This shows the total estimated revenue from bookings.")
    else:
        print("\nSkipped total revenue because revenue is missing.")


def show_average_price(booking_data):
    if "average_daily_rate" in booking_data.columns:
        average_price = booking_data["average_daily_rate"].mean()
        print("\nAverage daily rate:", average_price)
        print("This shows the average price per night.")
    else:
        print("\nSkipped average price because average_daily_rate is missing.")


def show_room_type_distribution(booking_data):
    room_column = None

    if "reserved_room_type" in booking_data.columns:
        room_column = "reserved_room_type"
    elif "assigned_room_type" in booking_data.columns:
        room_column = "assigned_room_type"
    elif "room_type" in booking_data.columns:
        room_column = "room_type"

    if room_column is not None:
        room_distribution = booking_data[room_column].value_counts()
        print("\nRoom type distribution")
        print(room_distribution)
        print("This shows which room types are booked most often.")
    else:
        print("\nSkipped room type distribution because no room type column was found.")


def show_city_distribution(booking_data):
    city_column = None

    if "city" in booking_data.columns:
        city_column = "city"
    elif "market_segment" in booking_data.columns:
        city_column = "market_segment"

    if city_column is not None:
        city_distribution = booking_data[city_column].value_counts().head(10)
        print("\nCity or segment distribution")
        print(city_distribution)
        print("This shows the top locations or customer segments.")
    else:
        print("\nSkipped city distribution because no city or segment column was found.")


def show_cancellation_rate(booking_data):
    if "is_canceled" in booking_data.columns:
        cancellation_rate = booking_data["is_canceled"].mean() * 100
        print("\nCancellation rate:", cancellation_rate)
        print("This shows what percentage of bookings were cancelled.")
    else:
        print("\nSkipped cancellation rate because is_canceled is missing.")


def show_occupancy_rate(booking_data):
    if "occupancy_indicator" in booking_data.columns:
        occupancy_counts = booking_data["occupancy_indicator"].value_counts()
        print("\nOccupancy counts")
        print(occupancy_counts)
        print("This shows how many bookings were occupied or not occupied.")
    else:
        print("\nSkipped occupancy because occupancy_indicator is missing.")


def show_hotel_comparison(booking_data):
    if "hotel" in booking_data.columns and "revenue" in booking_data.columns:
        hotel_revenue = booking_data.groupby("hotel")["revenue"].sum().sort_values(ascending=False)
        print("\nRevenue by hotel")
        print(hotel_revenue)
        print("This compares hotels by estimated revenue.")
    elif "hotel" in booking_data.columns:
        hotel_bookings = booking_data["hotel"].value_counts()
        print("\nBookings by hotel")
        print(hotel_bookings)
        print("This compares hotels by booking count.")
    else:
        print("\nSkipped hotel comparison because hotel column is missing.")


def run_eda(booking_data):
    print("\nSTARTING EXPLORATORY DATA ANALYSIS")

    show_total_bookings(booking_data)
    show_monthly_bookings(booking_data)
    show_total_revenue(booking_data)
    show_average_price(booking_data)
    show_room_type_distribution(booking_data)
    show_city_distribution(booking_data)
    show_cancellation_rate(booking_data)
    show_occupancy_rate(booking_data)
    show_hotel_comparison(booking_data)

    print("\nEDA COMPLETED")
