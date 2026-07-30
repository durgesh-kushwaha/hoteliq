# Power BI Dashboard Plan

## Dashboard Name
Hotel / Airbnb Booking Pricing & Occupancy Analytics

## Data Source
Use this cleaned file:

`data/processed/cleaned_hotel_bookings.csv`

## Main KPI Cards
- Total Bookings
- Total Revenue
- Average Daily Rate
- Cancellation Percentage
- Occupancy Percentage
- Revenue Lost
- Average Stay Length

## Recommended Dashboard Pages

### Page 1: Executive Summary
- KPI cards at the top
- Monthly bookings line chart
- Revenue by hotel bar chart
- Cancellation percentage card
- Occupancy percentage card

### Page 2: Pricing and Revenue
- Revenue by month
- Average daily rate by month
- Revenue by city
- Revenue by hotel
- Revenue lost due to cancellations

### Page 3: Occupancy and Demand
- Occupancy by month
- Weekend vs weekday bookings
- Stay length distribution
- Advance booking days distribution
- Seasonal demand by booking month

### Page 4: Customer and Room Analysis
- Room type distribution
- Bookings by market segment or city
- Average daily rate by room type
- Cancellation by room type
- Hotel comparison table

## Filters and Slicers
- Booking Year
- Booking Month
- Hotel
- City
- Room Type
- Weekend Booking
- Cancellation Status
- Market Segment

## Recommended Visuals
- Cards for main KPIs
- Line chart for monthly trends
- Bar chart for hotel and city comparison
- Pie or donut chart for room type share
- Table for top hotels and top cities
- Histogram for price distribution
- Scatter plot for advance booking days vs price

## Suggested Dashboard Colors
- Dark navy for titles
- White or light gray background
- Blue for revenue
- Green for occupied bookings
- Red for cancelled bookings
- Orange for revenue lost

## Power BI Data Preparation Notes
- Load `cleaned_hotel_bookings.csv` into Power BI.
- Check that date columns are detected as dates.
- Check that revenue, revenue_lost, average_daily_rate, and stay_length are numeric.
- Create DAX measures for total revenue, average price, cancellation percentage, and occupancy percentage.

## Suggested DAX Measures

```DAX
Total Revenue = SUM(cleaned_hotel_bookings[revenue])
```

```DAX
Total Bookings = COUNTROWS(cleaned_hotel_bookings)
```

```DAX
Average Daily Rate = AVERAGE(cleaned_hotel_bookings[average_daily_rate])
```

```DAX
Cancellation % = AVERAGE(cleaned_hotel_bookings[is_canceled])
```

```DAX
Revenue Lost = SUM(cleaned_hotel_bookings[revenue_lost])
```
