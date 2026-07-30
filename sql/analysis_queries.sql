-- Hotel Booking Analytics
-- Table: cleaned_hotel_bookings

SELECT
    SUM(revenue) AS total_revenue
FROM cleaned_hotel_bookings;


SELECT
    city,
    SUM(revenue) AS total_revenue
FROM cleaned_hotel_bookings
GROUP BY city
ORDER BY total_revenue DESC;


SELECT
    hotel,
    SUM(revenue) AS total_revenue
FROM cleaned_hotel_bookings
GROUP BY hotel
ORDER BY total_revenue DESC;


SELECT
    booking_year,
    booking_month,
    COUNT(*) AS total_bookings
FROM cleaned_hotel_bookings
GROUP BY booking_year, booking_month
ORDER BY booking_year, booking_month;


SELECT
    AVG(average_daily_rate) AS average_daily_rate
FROM cleaned_hotel_bookings;


SELECT
    hotel,
    COUNT(*) AS total_bookings
FROM cleaned_hotel_bookings
GROUP BY hotel
ORDER BY total_bookings DESC
LIMIT 10;


SELECT
    city,
    COUNT(*) AS total_bookings
FROM cleaned_hotel_bookings
GROUP BY city
ORDER BY total_bookings DESC
LIMIT 10;


SELECT
    ROUND(
        SUM(is_canceled) * 100.0 / COUNT(*),
        2
    ) AS cancellation_percentage
FROM cleaned_hotel_bookings;


SELECT
    ROUND(
        (COUNT(*) - SUM(is_canceled)) * 100.0 / COUNT(*),
        2
    ) AS occupancy_percentage
FROM cleaned_hotel_bookings;


SELECT
    reserved_room_type,
    COUNT(*) AS total_bookings,
    AVG(average_daily_rate) AS average_daily_rate,
    SUM(revenue) AS total_revenue
FROM cleaned_hotel_bookings
GROUP BY reserved_room_type
ORDER BY total_bookings DESC;


SELECT
    SUM(revenue_lost) AS total_revenue_lost
FROM cleaned_hotel_bookings;


SELECT
    weekend_booking,
    COUNT(*) AS total_bookings,
    SUM(revenue) AS total_revenue
FROM cleaned_hotel_bookings
GROUP BY weekend_booking
ORDER BY total_bookings DESC;