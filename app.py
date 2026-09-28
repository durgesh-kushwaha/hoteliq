"""
🏨 Hotel Booking Analytics – Streamlit Dashboard
Author: Durgesh Kushwaha

Upload a hotel-booking file (CSV, Excel, XLS, XLSX, TSV, Google Sheets export)
→ auto-clean → explore KPIs & charts → download cleaned data.
"""

import io
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ─────────────────────────── File Reader ───────────────────────────
# Supported extensions and their corresponding reader functions.
SUPPORTED_EXTENSIONS = ["csv", "xlsx", "xls", "tsv"]


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Read an uploaded file into a DataFrame.

    Supports: .csv, .tsv, .xlsx, .xls
    Google Sheets export: export as .csv or .xlsx and upload.
    """
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        # Try common encodings that handle phone-generated CSVs
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, encoding=encoding)
            except (UnicodeDecodeError, Exception):
                continue
        # Last-resort: ignore errors
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="utf-8", errors="ignore")

    elif filename.endswith(".tsv") or filename.endswith(".txt"):
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, sep="\t")

    elif filename.endswith(".xlsx"):
        uploaded_file.seek(0)
        return pd.read_excel(uploaded_file, engine="openpyxl")

    elif filename.endswith(".xls"):
        uploaded_file.seek(0)
        try:
            return pd.read_excel(uploaded_file, engine="xlrd")
        except Exception:
            # Some .xls files are actually .xlsx; retry with openpyxl
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file, engine="openpyxl")

    else:
        # Fallback: try CSV first, then Excel
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file)
        except Exception:
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file)

# Path to the bundled sample dataset (relative to this file)
SAMPLE_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw", "hotel_bookings.csv")

# ─────────────────────────── Page Config ───────────────────────────
st.set_page_config(
    page_title="Hotel Booking Analytics",
    page_icon="🏨",
    layout="wide",
)

# ─────────────────────────── Custom CSS ────────────────────────────
st.markdown(
    """
    <style>
    /* KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem 1rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 14px rgba(0,0,0,0.15);
    }
    .kpi-card h2 { margin: 0; font-size: 1.8rem; }
    .kpi-card p  { margin: 0; font-size: 0.95rem; opacity: 0.9; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS  (ported from src/)
# ═══════════════════════════════════════════════════════════════════

# ──── Type checkers ────
def _is_text(df, col):
    t = str(df[col].dtype)
    return t == "object" or "string" in t


def _is_number(df, col):
    t = str(df[col].dtype)
    return "int" in t or "float" in t


def _is_date(df, col):
    return "datetime" in str(df[col].dtype)


# ──── Data Cleaning ────
def clean_booking_data(df):
    """Run the full cleaning pipeline; return (cleaned_df, log_messages)."""
    log = []

    # 1. Duplicates
    before = df.shape[0]
    df = df.drop_duplicates()
    removed = before - df.shape[0]
    log.append(f"✅ Removed **{removed}** duplicate rows (was {before}, now {df.shape[0]})")

    # 2. Text columns – strip & title-case
    for col in df.columns:
        if _is_text(df, col):
            df[col] = df[col].astype(str).str.strip().str.title()
            df.loc[df[col] == "Nan", col] = pd.NA
    log.append("✅ Cleaned text columns (stripped whitespace, title-cased)")

    # 3. Date columns
    date_keywords = ["reservation_status_date", "booking_date", "arrival_date"]
    for col in df.columns:
        if col.lower() in date_keywords:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            log.append(f"✅ Converted **{col}** to datetime")

    # 4. Numeric columns
    numeric_candidates = [
        "adr", "price", "stays_in_weekend_nights", "stays_in_week_nights",
        "adults", "children", "babies", "lead_time", "days_in_waiting_list",
        "is_canceled", "previous_cancellations", "previous_bookings_not_canceled",
        "booking_changes", "required_car_parking_spaces", "total_of_special_requests",
    ]
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    log.append("✅ Ensured numeric columns have correct type")

    # 5. Missing values
    for col in df.columns:
        n_miss = df[col].isnull().sum()
        if n_miss > 0:
            if _is_text(df, col):
                df[col] = df[col].fillna("Unknown")
            elif _is_number(df, col):
                df[col] = df[col].fillna(df[col].median())
            elif _is_date(df, col):
                mode_vals = df[col].mode()
                if len(mode_vals) > 0:
                    df[col] = df[col].fillna(mode_vals[0])
            else:
                df[col] = df[col].fillna("Unknown")
    log.append("✅ Filled missing values (text→'Unknown', numeric→median, date→mode)")

    # 6. Impossible values
    positive_cols = [
        "adr", "price", "average_daily_rate",
        "stays_in_weekend_nights", "stays_in_week_nights",
        "adults", "children", "babies", "lead_time", "days_in_waiting_list",
    ]
    before = df.shape[0]
    for col in positive_cols:
        if col in df.columns:
            df = df[df[col] >= 0]
    removed = before - df.shape[0]
    log.append(f"✅ Removed **{removed}** rows with impossible negative values")

    return df, log


# ──── Feature Engineering ────
def add_booking_features(df):
    """Add derived columns; return (df, log_messages)."""
    log = []

    # Stay length
    if "stays_in_weekend_nights" in df.columns and "stays_in_week_nights" in df.columns:
        df["stay_length"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
        log.append("🔧 Created **stay_length**")

    # Date features
    date_col = None
    for c in ["reservation_status_date", "booking_date", "arrival_date"]:
        if c in df.columns:
            date_col = c
            break

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["booking_month"] = df[date_col].dt.month
        df["booking_year"] = df[date_col].dt.year
        df["booking_weekday"] = df[date_col].dt.day_name()
        log.append(f"🔧 Created **booking_month**, **booking_year**, **booking_weekday** from *{date_col}*")
    elif "arrival_date_month" in df.columns and "arrival_date_year" in df.columns:
        df["booking_month"] = df["arrival_date_month"]
        df["booking_year"] = df["arrival_date_year"]
        log.append("🔧 Created **booking_month** & **booking_year** from arrival columns")

    # Weekend booking
    if "booking_weekday" in df.columns:
        df["weekend_booking"] = "No"
        df.loc[df["booking_weekday"].isin(["Saturday", "Sunday"]), "weekend_booking"] = "Yes"
        log.append("🔧 Created **weekend_booking**")

    # Revenue
    price_col = "adr" if "adr" in df.columns else ("price" if "price" in df.columns else None)
    if price_col and "stay_length" in df.columns:
        df["revenue"] = df[price_col] * df["stay_length"]
        log.append("🔧 Created **revenue**")

    # Revenue lost
    if "revenue" in df.columns and "is_canceled" in df.columns:
        df["revenue_lost"] = 0.0
        df.loc[df["is_canceled"] == 1, "revenue_lost"] = df.loc[df["is_canceled"] == 1, "revenue"]
        log.append("🔧 Created **revenue_lost**")

    # Advance booking days
    if "lead_time" in df.columns:
        df["advance_booking_days"] = df["lead_time"]
        log.append("🔧 Created **advance_booking_days**")

    # Occupancy indicator
    if "is_canceled" in df.columns:
        df["occupancy_indicator"] = "Occupied"
        df.loc[df["is_canceled"] == 1, "occupancy_indicator"] = "Not Occupied"
        log.append("🔧 Created **occupancy_indicator**")

    # Average daily rate alias
    if "adr" in df.columns:
        df["average_daily_rate"] = df["adr"]
        log.append("🔧 Created **average_daily_rate** (alias of adr)")
    elif "price" in df.columns:
        df["average_daily_rate"] = df["price"]
        log.append("🔧 Created **average_daily_rate** (alias of price)")

    return df, log


# ──── Resolve helper columns used in charts ────
def _room_col(df):
    for c in ["reserved_room_type", "assigned_room_type", "room_type"]:
        if c in df.columns:
            return c
    return None


# ═══════════════════════════════════════════════════════════════════
# STREAMLIT APP
# ═══════════════════════════════════════════════════════════════════

st.title("🏨 Hotel Booking Analytics")
st.caption("Upload your hotel booking file (CSV, Excel, XLS, Google Sheets export) → clean, explore, and download the results.")

# ─────────────────────── Sidebar – Upload ──────────────────────────
with st.sidebar:
    st.header("📂 Load Dataset")

    st.markdown("**Option 1 — Try instantly**")
    use_sample = st.button("📦 Use Sample Dataset", use_container_width=True)

    st.markdown("**Option 2 — Upload your own**")
    uploaded_file = st.file_uploader(
        "Choose a file (CSV, Excel, XLS, TSV)",
        type=SUPPORTED_EXTENSIONS,
        help=(
            "Supports: .csv, .xlsx, .xls, .tsv files.  \n"
            "**Google Sheets:** File → Download as .csv or .xlsx, then upload here."
        ),
    )

    st.markdown("---")
    st.markdown(
        "**Made by Durgesh Kushwaha**  \n"
        "B.Tech – AI & Data Science"
    )

# ──── Decide which data source to use ────
if use_sample:
    st.session_state["data_source"] = "sample"
if uploaded_file is not None:
    st.session_state["data_source"] = "upload"
    st.session_state["uploaded_file"] = uploaded_file

data_source = st.session_state.get("data_source")

# ─────────────────── Guard: nothing selected yet ───────────────────
if data_source is None:
    st.info("👈 **Upload a file** (CSV, Excel, XLS, TSV) or click **Use Sample Dataset** to get started.")
    st.markdown(
        """
        ### How it works
        1. **Click "Use Sample Dataset"** to explore with the built-in hotel bookings data, **or upload your own file** (CSV, XLSX, XLS, TSV, or Google Sheets export).
        2. The app **automatically cleans** the data (removes duplicates, fixes missing values, etc.).
        3. **Feature engineering** adds useful columns like *revenue*, *stay_length*, *booking_month*, etc.
        4. Explore **KPI cards** and **interactive charts**.
        5. **Download** the cleaned dataset when you're done!
        """
    )
    st.stop()

# ─────────────────────── Load raw data ─────────────────────────────
if data_source == "sample":
    if not os.path.exists(SAMPLE_CSV_PATH):
        st.error("❌ Sample dataset not found. Please upload a file instead.")
        st.stop()
    raw_df = pd.read_csv(SAMPLE_CSV_PATH)
    source_label = "hotel_bookings.csv (Sample)"
else:
    uploaded_file = st.session_state.get("uploaded_file")
    try:
        raw_df = read_uploaded_file(uploaded_file)
    except Exception as e:
        st.error(
            f"❌ **Could not read the file.** Please make sure it is a valid "
            f"CSV, XLSX, XLS, or TSV file.\n\n"
            f"**Error:** `{e}`"
        )
        st.stop()
    source_label = uploaded_file.name

st.success(f"✅ Loaded **{source_label}** — {raw_df.shape[0]:,} rows × {raw_df.shape[1]} columns")

# ─────────────────────── Data Preview ──────────────────────────────
with st.expander("🔍 Raw Data Preview", expanded=False):
    st.dataframe(raw_df.head(20), use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Data Types**")
        st.dataframe(raw_df.dtypes.rename("dtype").to_frame(), use_container_width=True)
    with col_b:
        st.markdown("**Missing Values**")
        miss = raw_df.isnull().sum()
        miss = miss[miss > 0]
        if miss.empty:
            st.write("No missing values 🎉")
        else:
            st.dataframe(miss.rename("missing").to_frame(), use_container_width=True)

# ─────────────────────── Cleaning ──────────────────────────────────
st.header("🧹 Data Cleaning")
cleaned_df, clean_log = clean_booking_data(raw_df.copy())
for msg in clean_log:
    st.markdown(msg)

# ─────────────────────── Feature Engineering ───────────────────────
st.header("⚡ Feature Engineering")
final_df, feat_log = add_booking_features(cleaned_df.copy())
for msg in feat_log:
    st.markdown(msg)

st.markdown(f"**Final dataset:** {final_df.shape[0]:,} rows × {final_df.shape[1]} columns")

# ─────────────────────── Cleaned Data Preview ──────────────────────
with st.expander("📋 Cleaned Data Preview", expanded=False):
    st.dataframe(final_df.head(20), use_container_width=True)

# ─────────────────────── Download Button ───────────────────────────
st.header("📥 Download Cleaned Data")
csv_buffer = io.BytesIO()
final_df.to_csv(csv_buffer, index=False)
csv_buffer.seek(0)
st.download_button(
    label="⬇️  Download Cleaned CSV",
    data=csv_buffer,
    file_name="cleaned_hotel_bookings.csv",
    mime="text/csv",
)

# ═══════════════════════════════════════════════════════════════════
# KPI SECTION
# ═══════════════════════════════════════════════════════════════════
st.header("📌 Key Performance Indicators")

total_bookings = final_df.shape[0]
total_revenue = final_df["revenue"].sum() if "revenue" in final_df.columns else None
avg_adr = final_df["average_daily_rate"].mean() if "average_daily_rate" in final_df.columns else None
cancel_rate = (final_df["is_canceled"].mean() * 100) if "is_canceled" in final_df.columns else None

kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.markdown(
        f'<div class="kpi-card"><p>Total Bookings</p><h2>{total_bookings:,}</h2></div>',
        unsafe_allow_html=True,
    )

with kpi_cols[1]:
    val = f"${total_revenue:,.0f}" if total_revenue is not None else "N/A"
    st.markdown(
        f'<div class="kpi-card"><p>Total Revenue</p><h2>{val}</h2></div>',
        unsafe_allow_html=True,
    )

with kpi_cols[2]:
    val = f"${avg_adr:,.2f}" if avg_adr is not None else "N/A"
    st.markdown(
        f'<div class="kpi-card"><p>Avg Daily Rate</p><h2>{val}</h2></div>',
        unsafe_allow_html=True,
    )

with kpi_cols[3]:
    val = f"{cancel_rate:.1f}%" if cancel_rate is not None else "N/A"
    st.markdown(
        f'<div class="kpi-card"><p>Cancellation Rate</p><h2>{val}</h2></div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
# CHARTS SECTION
# ═══════════════════════════════════════════════════════════════════
st.header("📊 Visualizations")

# Helper: month name mapping
MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

# ─── 1. Monthly Bookings ───
if "booking_month" in final_df.columns:
    st.subheader("📅 Monthly Booking Trends")
    monthly = final_df["booking_month"].value_counts().sort_index().reset_index()
    monthly.columns = ["Month", "Bookings"]
    monthly["Month Name"] = monthly["Month"].map(MONTH_NAMES)
    fig = px.line(
        monthly, x="Month Name", y="Bookings",
        markers=True, title="Number of Bookings per Month",
        labels={"Month Name": "Month", "Bookings": "Number of Bookings"},
    )
    fig.update_layout(xaxis=dict(categoryorder="array", categoryarray=list(MONTH_NAMES.values())))
    st.plotly_chart(fig, use_container_width=True)

# ─── 2. Revenue by Hotel ───
if "hotel" in final_df.columns and "revenue" in final_df.columns:
    st.subheader("💰 Revenue by Hotel")
    rev_hotel = final_df.groupby("hotel")["revenue"].sum().sort_values(ascending=False).reset_index()
    rev_hotel.columns = ["Hotel", "Revenue"]
    fig = px.bar(
        rev_hotel, x="Hotel", y="Revenue", color="Hotel",
        title="Total Revenue by Hotel Type",
        labels={"Revenue": "Total Revenue ($)"},
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── 3. Room Type Distribution ───
room_c = _room_col(final_df)
if room_c:
    st.subheader("🛏️ Room Type Distribution")
    room_counts = final_df[room_c].value_counts().reset_index()
    room_counts.columns = ["Room Type", "Count"]
    fig = px.pie(
        room_counts, names="Room Type", values="Count",
        title="Booking Share by Room Type", hole=0.35,
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── 4. ADR Distribution (Histogram) ───
if "average_daily_rate" in final_df.columns:
    st.subheader("💵 Average Daily Rate Distribution")
    fig = px.histogram(
        final_df, x="average_daily_rate", nbins=40,
        title="Distribution of Average Daily Rate",
        labels={"average_daily_rate": "Average Daily Rate ($)"},
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── 5. ADR Box Plot ───
if "average_daily_rate" in final_df.columns:
    st.subheader("📦 Average Daily Rate – Box Plot")
    if "hotel" in final_df.columns:
        fig = px.box(
            final_df, x="hotel", y="average_daily_rate", color="hotel",
            title="ADR by Hotel Type",
            labels={"average_daily_rate": "Average Daily Rate ($)", "hotel": "Hotel"},
        )
    else:
        fig = px.box(
            final_df, y="average_daily_rate",
            title="ADR Box Plot",
            labels={"average_daily_rate": "Average Daily Rate ($)"},
        )
    st.plotly_chart(fig, use_container_width=True)

# ─── 6. Cancellation Count ───
if "is_canceled" in final_df.columns:
    st.subheader("❌ Cancellation Count")
    cancel_counts = final_df["is_canceled"].value_counts().reset_index()
    cancel_counts.columns = ["Status", "Count"]
    cancel_counts["Status"] = cancel_counts["Status"].map({0: "Not Cancelled", 1: "Cancelled"})
    fig = px.bar(
        cancel_counts, x="Status", y="Count", color="Status",
        title="Cancelled vs Not Cancelled Bookings",
        color_discrete_map={"Not Cancelled": "#2ecc71", "Cancelled": "#e74c3c"},
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── 7. Advance Booking vs Price (Scatter) ───
if "advance_booking_days" in final_df.columns and "average_daily_rate" in final_df.columns:
    st.subheader("📆 Advance Booking Days vs Price")
    sample = final_df.sample(min(5000, len(final_df)), random_state=42)
    fig = px.scatter(
        sample, x="advance_booking_days", y="average_daily_rate",
        opacity=0.45,
        title="Does Booking Earlier Affect Price?",
        labels={
            "advance_booking_days": "Advance Booking Days",
            "average_daily_rate": "Average Daily Rate ($)",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── Extra: Occupancy breakdown ───
if "occupancy_indicator" in final_df.columns:
    st.subheader("🏨 Occupancy Breakdown")
    occ = final_df["occupancy_indicator"].value_counts().reset_index()
    occ.columns = ["Status", "Count"]
    fig = px.pie(
        occ, names="Status", values="Count",
        title="Occupied vs Not Occupied",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────── Footer ────────────────────────────────────
st.markdown("---")
st.markdown(
    "Made with ❤️ by **Durgesh Kushwaha** · "
    "B.Tech – AI & Data Science"
)
