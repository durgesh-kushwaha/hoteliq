# 🏨 HotelIQ – Hotel Booking Analytics

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas)
![NumPy](https://img.shields.io/badge/NumPy-Numerical%20Computing-013243?logo=numpy)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75?logo=plotly)
![File Support](https://img.shields.io/badge/Upload-CSV%20%7C%20XLSX%20%7C%20XLS%20%7C%20TSV-green)

---

## 📌 Project Overview

**HotelIQ** is an end-to-end Hotel Booking Analytics dashboard built with Streamlit and Plotly. Upload any hotel booking dataset — regardless of column naming conventions — and the app will:

- **Auto-detect columns** (price, dates, room type, booking status, guest info, etc.)
- **Deep clean** the data (fix negative prices, strip currency symbols, normalise statuses, cap ratings)
- **Engineer features** (stay length, revenue, booking month/year/weekday, cancellation flags)
- **Show rich KPIs & interactive charts**
- Let you **download the cleaned dataset**

> 💱 **Default currency is INR (₹)** when no currency is detected in your data.

---

## 🧠 Smart Column Detection

Unlike traditional dashboards that break when column names don't match exactly, HotelIQ uses **fuzzy keyword matching** to find the right columns automatically:

| Role | Keywords Searched |
|------|------------------|
| Price | `price_per_night`, `price`, `adr`, `rate`, `cost`, `tariff` |
| Total Amount | `total_amount`, `total_price`, `total_cost`, `revenue`, `amount` |
| Check-in Date | `check_in`, `checkin`, `arrival_date` |
| Check-out Date | `check_out`, `checkout`, `departure` |
| Room Type | `room_type`, `reserved_room`, `assigned_room` |
| Booking Status | `booking_status`, `reservation_status`, `status` |
| Hotel / Property | `hotel`, `property_id`, `property` |
| Guest Rating | `rating`, `review_score`, `score` |
| ...and more | Lead time, adults, children, country, meal, etc. |

---

## 🧹 Data Cleaning (The Main Brain)

The cleaning pipeline handles real-world messy data:

| Problem | Solution |
|---------|----------|
| Prices like `$456`, `5122 USD`, `₹3000` | Extracts numeric value, detects currency |
| Negative prices (`-487`) | Converts to absolute value |
| `Error`, blank, or invalid price values | Replaced with column median |
| Inconsistent statuses (`pending`, `PENDING`, `Pending`) | Normalised to Title Case |
| Guest ratings > 5 or < 1 | Capped to [1, 5] range |
| Missing dates | Set to NaT (not silently dropped) |
| Duplicate rows | Removed automatically |
| Missing text values | Filled with "Unknown" / "Anonymous" |

---

## ⚡ Feature Engineering

| Feature | How It's Calculated |
|---------|-------------------|
| `stay_nights` | `checkout - checkin` in days, or `weekend_nights + weekday_nights` |
| `revenue` | From `total_amount` column, or `price × stay_nights` |
| `booking_month / year / weekday` | Extracted from check-in date |
| `is_weekend_booking` | True if check-in falls on Saturday/Sunday |
| `avg_daily_rate` | Alias of the detected price column |
| `is_cancelled` | Derived from booking status (if no binary column exists) |
| `revenue_lost` | Revenue of cancelled bookings |

---

## 📊 Dashboard Sections

### Key Performance Indicators (8 KPI Cards)
- Total Bookings
- Total Revenue
- Average Daily Rate
- Cancellation Rate
- Average Stay Length
- Average Guest Rating
- Room Types Count
- Properties / Hotels Count

### Interactive Visualisations
1. 📅 Monthly Booking Trends
2. 📋 Booking Status Distribution (pie + bar)
3. 💰 Revenue by Property / Hotel
4. 🛏️ Room Type Distribution (pie + bar)
5. 💵 Price Distribution (histogram + box plot by room type)
6. 📈 Revenue Over Time
7. ⭐ Guest Rating Distribution
8. ❌ Cancellation Analysis
9. 📆 Advance Booking Days vs Price (scatter)
10. 🌙 Stay Length Distribution
11. 👤 Top 10 Guests by Revenue

---

## 📂 Project Structure

```text
Hotel Booking Analytics/
├── app.py                     ← Streamlit Dashboard (the main brain)
├── data/
│   ├── raw/
│   │   └── hotel_bookings.csv
│   └── processed/
│       └── cleaned_hotel_bookings.csv
├── notebooks/
│   └── Hotel_Booking_Analysis.ipynb
├── src/
│   ├── main.py
│   ├── data_cleaning.py
│   ├── feature_engineering.py
│   ├── eda.py
│   ├── visualization.py
│   └── utils.py
├── sql/
│   └── analysis_queries.sql
├── dashboard/
│   └── power_bi_dashboard_plan.md
├── images/
├── README.md
├── requirements.txt
└── .gitignore
```

---

## 🚀 How to Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Dashboard

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually http://localhost:8501).

### Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | Standard comma-separated values |
| Excel (Modern) | `.xlsx` | Microsoft Excel 2007+ |
| Excel (Legacy) | `.xls` | Microsoft Excel 97-2003 |
| TSV | `.tsv` | Tab-separated values |
| Google Sheets | `.csv` / `.xlsx` | Export via File → Download, then upload |

---

## 🛠️ Technologies Used

| Tool | Purpose |
|------|---------|
| Python 3.x | Core language |
| Pandas | Data cleaning & manipulation |
| NumPy | Numerical operations |
| Streamlit | Interactive web dashboard |
| Plotly | Interactive charts |
| openpyxl | XLSX file support |
| xlrd | XLS file support |

---

## 🔮 Future Improvements

- Power BI Dashboard integration
- Revenue forecasting with ML
- Customer segmentation
- Dynamic pricing analysis
- Geographic booking analysis

---

## 👨‍💻 Author

**Durgesh Kushwaha**

B.Tech – Artificial Intelligence & Data Science

📧 durgeshcgc@gmail.com

---

## ⭐ If you found this project useful, consider giving it a Star!
