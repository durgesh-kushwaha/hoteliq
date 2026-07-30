import os

# Matplotlib needs a writable folder for its settings and font cache.
# This keeps the project friendly on computers where the home folder is restricted.
if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = os.path.join(os.getcwd(), ".matplotlib_cache")

if "XDG_CACHE_HOME" not in os.environ:
    os.environ["XDG_CACHE_HOME"] = os.path.join(os.getcwd(), ".cache")

import matplotlib.pyplot as plt

plt.switch_backend("Agg")


def create_images_folder(images_folder_path):
    if os.path.exists(images_folder_path) == False:
        os.makedirs(images_folder_path)


def save_monthly_bookings_chart(booking_data, images_folder_path):
    if "booking_month" in booking_data.columns:
        monthly_bookings = booking_data["booking_month"].value_counts().sort_index()

        plt.figure(figsize=(10, 5))
        plt.plot(monthly_bookings.index, monthly_bookings.values, marker="o")
        plt.title("Monthly Bookings")
        plt.xlabel("Month")
        plt.ylabel("Number of Bookings")
        plt.tight_layout()
        plt.savefig(os.path.join(images_folder_path, "monthly_bookings.png"))
        plt.close()

        highest_month = monthly_bookings.idxmax()
        print("Observation: Month", highest_month, "has the highest number of bookings.")
    else:
        print("Skipped monthly bookings chart because booking_month is missing.")


def save_revenue_by_hotel_chart(booking_data, images_folder_path):
    if "hotel" in booking_data.columns and "revenue" in booking_data.columns:
        revenue_by_hotel = booking_data.groupby("hotel")["revenue"].sum().sort_values(ascending=False)

        plt.figure(figsize=(10, 5))
        plt.bar(revenue_by_hotel.index, revenue_by_hotel.values)
        plt.title("Revenue by Hotel")
        plt.xlabel("Hotel")
        plt.ylabel("Revenue")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(images_folder_path, "revenue_by_hotel.png"))
        plt.close()

        top_hotel = revenue_by_hotel.index[0]
        print("Observation:", top_hotel, "generates the highest revenue.")
    else:
        print("Skipped revenue by hotel chart because hotel or revenue is missing.")


def save_room_type_chart(booking_data, images_folder_path):
    room_column = None

    if "reserved_room_type" in booking_data.columns:
        room_column = "reserved_room_type"
    elif "assigned_room_type" in booking_data.columns:
        room_column = "assigned_room_type"
    elif "room_type" in booking_data.columns:
        room_column = "room_type"

    if room_column is not None:
        room_counts = booking_data[room_column].value_counts()

        plt.figure(figsize=(8, 8))
        plt.pie(room_counts.values, labels=room_counts.index, autopct="%1.1f%%")
        plt.title("Room Type Distribution")
        plt.tight_layout()
        plt.savefig(os.path.join(images_folder_path, "room_type_distribution.png"))
        plt.close()

        top_room = room_counts.index[0]
        print("Observation:", top_room, "is the most booked room type.")
    else:
        print("Skipped room type chart because no room type column was found.")


def save_price_histogram(booking_data, images_folder_path):
    if "average_daily_rate" in booking_data.columns:
        plt.figure(figsize=(10, 5))
        plt.hist(booking_data["average_daily_rate"], bins=30)
        plt.title("Average Daily Rate Distribution")
        plt.xlabel("Average Daily Rate")
        plt.ylabel("Number of Bookings")
        plt.tight_layout()
        plt.savefig(os.path.join(images_folder_path, "average_daily_rate_distribution.png"))
        plt.close()

        print("Observation: This chart shows whether most bookings are low price, medium price, or high price.")
    else:
        print("Skipped price histogram because average_daily_rate is missing.")


def save_cancellation_chart(booking_data, images_folder_path):
    if "is_canceled" in booking_data.columns:
        cancellation_counts = booking_data["is_canceled"].value_counts()

        plt.figure(figsize=(8, 5))
        plt.bar(cancellation_counts.index.astype(str), cancellation_counts.values)
        plt.title("Cancellation Count")
        plt.xlabel("Cancellation Status")
        plt.ylabel("Number of Bookings")
        plt.tight_layout()
        plt.savefig(os.path.join(images_folder_path, "cancellation_count.png"))
        plt.close()

        print("Observation: This chart compares cancelled and non-cancelled bookings.")
    else:
        print("Skipped cancellation chart because is_canceled is missing.")


def save_advance_booking_scatter(booking_data, images_folder_path):
    if "advance_booking_days" in booking_data.columns and "average_daily_rate" in booking_data.columns:
        plt.figure(figsize=(10, 5))
        plt.scatter(booking_data["advance_booking_days"], booking_data["average_daily_rate"], alpha=0.5)
        plt.title("Advance Booking Days vs Average Daily Rate")
        plt.xlabel("Advance Booking Days")
        plt.ylabel("Average Daily Rate")
        plt.tight_layout()
        plt.savefig(os.path.join(images_folder_path, "advance_booking_vs_price.png"))
        plt.close()

        print("Observation: This chart helps compare early bookings with room prices.")
    else:
        print("Skipped scatter plot because advance_booking_days or average_daily_rate is missing.")


def save_price_boxplot(booking_data, images_folder_path):
    if "average_daily_rate" in booking_data.columns:
        plt.figure(figsize=(8, 5))
        plt.boxplot(booking_data["average_daily_rate"])
        plt.title("Average Daily Rate Box Plot")
        plt.xlabel("Bookings")
        plt.ylabel("Average Daily Rate")
        plt.tight_layout()
        plt.savefig(os.path.join(images_folder_path, "average_daily_rate_boxplot.png"))
        plt.close()

        print("Observation: This chart helps identify unusual high or low prices.")
    else:
        print("Skipped box plot because average_daily_rate is missing.")


def create_all_charts(booking_data, images_folder_path):
    print("\nSTARTING VISUALIZATION")

    create_images_folder(images_folder_path)
    save_monthly_bookings_chart(booking_data, images_folder_path)
    save_revenue_by_hotel_chart(booking_data, images_folder_path)
    save_room_type_chart(booking_data, images_folder_path)
    save_price_histogram(booking_data, images_folder_path)
    save_cancellation_chart(booking_data, images_folder_path)
    save_advance_booking_scatter(booking_data, images_folder_path)
    save_price_boxplot(booking_data, images_folder_path)

    print("\nVISUALIZATION COMPLETED")
