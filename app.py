"""
🏨 HotelIQ – Hotel Booking Analytics Dashboard
Author : Durgesh Kushwaha
Email  : durgeshcgc@gmail.com

Upload any hotel-booking file (CSV / Excel / TSV)
→ smart column detection → deep clean → rich KPIs & charts → download.
"""

import io
import os
import re
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ═══════════════════════════════════════════════════════════════════════
# 1. CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

SUPPORTED_EXTENSIONS = ["csv", "xlsx", "xls", "tsv"]
SAMPLE_CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "raw", "hotel_bookings.csv"
)

# Default currency when nothing is mentioned in the dataset
DEFAULT_CURRENCY = "₹"
DEFAULT_CURRENCY_NAME = "INR"

# Month names for chart labels
MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


# ═══════════════════════════════════════════════════════════════════════
# 2. FILE READER – handles CSV, Excel, TSV with encoding fallbacks
# ═══════════════════════════════════════════════════════════════════════

def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Read an uploaded file into a DataFrame.

    Supports .csv, .tsv, .xlsx, .xls files.
    Google Sheets: export as .csv or .xlsx first.
    """
    name = uploaded_file.name.lower()

    if name.endswith(".csv"):
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, encoding=encoding)
            except Exception:
                continue
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="utf-8", errors="ignore")

    elif name.endswith(".tsv") or name.endswith(".txt"):
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, sep="\t")

    elif name.endswith(".xlsx"):
        uploaded_file.seek(0)
        return pd.read_excel(uploaded_file, engine="openpyxl")

    elif name.endswith(".xls"):
        uploaded_file.seek(0)
        try:
            return pd.read_excel(uploaded_file, engine="xlrd")
        except Exception:
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file, engine="openpyxl")

    else:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file)
        except Exception:
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file)


# ═══════════════════════════════════════════════════════════════════════
# 3. SMART COLUMN DETECTION
#    Instead of hardcoding column names, we search for them by keywords.
#    This means datasets with columns named "Price_Per_Night", "adr",
#    "room_price", "cost", etc. will all be found automatically.
# ═══════════════════════════════════════════════════════════════════════

def _normalise(name: str) -> str:
    """Lowercase, strip, replace separators with underscores."""
    return re.sub(r"[\s\-\.]+", "_", str(name).strip().lower())


def _find_column(df, keywords: list[str], exclude: list[str] | None = None) -> str | None:
    """Find the first column whose normalised name contains any keyword.

    Parameters
    ----------
    df       : DataFrame to search
    keywords : list of lowercase substrings to look for (e.g. ["price", "rate", "adr"])
    exclude  : optional list of column names to skip (already assigned to another role)

    Returns the *original* column name, or None.
    """
    exclude = exclude or []
    for col in df.columns:
        if col in exclude:
            continue
        norm = _normalise(col)
        for kw in keywords:
            if kw in norm:
                return col
    return None


def detect_columns(df) -> dict:
    """Return a mapping of semantic roles → actual column names.

    Roles detected:
        price       – nightly price / ADR
        total       – total amount / revenue for the booking
        checkin     – check-in date
        checkout    – check-out date
        room        – room type
        status      – booking status (confirmed / cancelled / …)
        hotel       – hotel name / property
        guest       – guest name
        rating      – guest rating / review score
        booking_id  – unique booking identifier
        cancelled   – binary is_canceled flag
        lead_time   – advance booking days
        stay_wkend  – weekend nights
        stay_week   – weekday nights
        adults      – number of adults
        children    – number of children
        country     – country
        meal        – meal type
        arrival_month – arrival month name
        arrival_year  – arrival year
    """
    found = {}

    # Order matters – assign more specific columns first to avoid collisions
    search = [
        ("booking_id", ["booking_id", "reservation_id", "id"]),
        ("guest",      ["guest_name", "customer_name", "guest_id"]),
        ("checkin",    ["check_in", "checkin", "arrival_date_day"]),
        ("checkout",   ["check_out", "checkout", "departure"]),
        ("room",       ["room_type", "reserved_room", "assigned_room"]),
        ("price",      ["price_per_night", "price", "adr", "rate", "cost", "tariff"]),
        ("total",      ["total_amount", "total_price", "total_cost", "revenue", "amount"]),
        ("status",     ["booking_status", "reservation_status", "status"]),
        ("hotel",      ["hotel", "property_id", "property"]),
        ("rating",     ["rating", "review_score", "score"]),
        ("cancelled",  ["is_cancel", "canceled", "cancelled"]),
        ("lead_time",  ["lead_time", "advance_booking", "days_before"]),
        ("stay_wkend", ["weekend_night"]),
        ("stay_week",  ["week_night"]),
        ("adults",     ["adult"]),
        ("children",   ["child", "babies"]),
        ("country",    ["country", "nationality"]),
        ("meal",       ["meal"]),
        ("arrival_month", ["arrival_date_month"]),
        ("arrival_year",  ["arrival_date_year"]),
    ]

    assigned = []  # columns already assigned – avoid double-matching
    for role, keywords in search:
        col = _find_column(df, keywords, exclude=assigned)
        if col is not None:
            found[role] = col
            assigned.append(col)

    return found


# ═══════════════════════════════════════════════════════════════════════
# 4. SMART PRICE PARSER
#    Handles:  "$456"  "5122 USD"  "₹3000"  "Error"  -487  None
# ═══════════════════════════════════════════════════════════════════════

# Regex to pull a number (possibly negative) out of a string with currency noise
_PRICE_RE = re.compile(r"[^\d.\-]*(-?\d+\.?\d*)")

# Known currency symbols and codes – we detect them to set the label
_CURRENCY_SYMBOLS = {
    "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR",
    "usd": "USD", "eur": "EUR", "gbp": "GBP", "inr": "INR",
}


def parse_price_column(series: pd.Series) -> tuple[pd.Series, str]:
    """Clean a price column and figure out which currency the data uses.

    Returns
    -------
    cleaned : pd.Series of float (NaN for unparsable)
    currency_symbol : str like '₹' or '$'
    """
    detected_currency = None

    def _parse_one(val):
        nonlocal detected_currency

        if pd.isna(val):
            return np.nan

        # Already a plain number
        if isinstance(val, (int, float)):
            return float(val)

        text = str(val).strip().lower()

        # Detect currency from the text
        if detected_currency is None:
            for marker, code in _CURRENCY_SYMBOLS.items():
                if marker in text:
                    detected_currency = code
                    break

        # Try to extract the numeric part
        m = _PRICE_RE.search(str(val))
        if m:
            return float(m.group(1))

        return np.nan

    cleaned = series.apply(_parse_one)

    # Pick a display symbol
    symbol_map = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹"}
    if detected_currency and detected_currency in symbol_map:
        symbol = symbol_map[detected_currency]
    else:
        symbol = DEFAULT_CURRENCY  # INR by default

    return cleaned, symbol


# ═══════════════════════════════════════════════════════════════════════
# 5. DATA CLEANING – the main brain
# ═══════════════════════════════════════════════════════════════════════

def clean_booking_data(df, col_map: dict) -> tuple[pd.DataFrame, list[str], str]:
    """Deep-clean the DataFrame.

    Returns
    -------
    df          : cleaned DataFrame
    log         : list of human-readable log messages
    currency    : currency symbol to use in charts (e.g. '₹')
    """
    log = []
    currency = DEFAULT_CURRENCY

    # ── Step 1: Remove exact duplicate rows ───────────────────────────
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    log.append(f"✅ Removed **{removed}** duplicate rows  (was {before:,} → now {len(df):,})")

    # ── Step 2: Standardise column names (strip whitespace) ───────────
    df.columns = [c.strip() for c in df.columns]

    # ── Step 3: Clean PRICE columns (price_per_night, total_amount, adr …)
    #    - Strip currency symbols like $ ₹ and suffixes like "USD"
    #    - Convert "Error" / gibberish → NaN
    #    - Make negative prices positive (absolute value)
    #    - Fill remaining NaN with median
    for role in ("price", "total"):
        col = col_map.get(role)
        if col and col in df.columns:
            cleaned_series, detected = parse_price_column(df[col])
            if detected != DEFAULT_CURRENCY:
                currency = detected
            df[col] = cleaned_series

            # Turn negatives into positives
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                df[col] = df[col].abs()
                log.append(f"✅ Fixed **{neg_count}** negative values in **{col}** (took absolute value)")

            # Fill NaN with median of the clean values
            n_missing = df[col].isna().sum()
            if n_missing > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                log.append(f"✅ Filled **{n_missing}** missing values in **{col}** with median ({median_val:,.0f})")
            else:
                log.append(f"✅ Cleaned **{col}** – no missing values")

    log.append(f"💱 Currency detected: **{currency}** (default is {DEFAULT_CURRENCY_NAME})")

    # ── Step 4: Clean BOOKING STATUS – normalise casing ───────────────
    status_col = col_map.get("status")
    if status_col and status_col in df.columns:
        df[status_col] = df[status_col].astype(str).str.strip().str.title()
        # Map common variants
        status_map = {
            "Nan": "Unknown", "None": "Unknown", "": "Unknown",
            "No Show": "No Show", "Noshow": "No Show",
            "Cancelled": "Cancelled", "Canceled": "Cancelled",
            "Cancel": "Cancelled",
        }
        df[status_col] = df[status_col].replace(status_map)
        n_unknown = (df[status_col] == "Unknown").sum()
        log.append(f"✅ Standardised **{status_col}** to title-case ({n_unknown} unknowns)")

    # ── Step 5: Clean DATE columns ────────────────────────────────────
    for role in ("checkin", "checkout"):
        col = col_map.get(role)
        if col and col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            n_bad = df[col].isna().sum()
            if n_bad > 0:
                log.append(f"⚠️ **{col}**: {n_bad} dates could not be parsed (set to NaT)")
            else:
                log.append(f"✅ Parsed **{col}** as datetime")

    # ── Step 6: Clean ROOM TYPE column – normalise casing ─────────────
    room_col = col_map.get("room")
    if room_col and room_col in df.columns:
        df[room_col] = df[room_col].astype(str).str.strip().str.title()
        df.loc[df[room_col].isin(["Nan", "None", ""]), room_col] = "Unknown"
        log.append(f"✅ Standardised **{room_col}** to title-case")

    # ── Step 7: Clean GUEST RATING – cap to 1-5 range ─────────────────
    rating_col = col_map.get("rating")
    if rating_col and rating_col in df.columns:
        df[rating_col] = pd.to_numeric(df[rating_col], errors="coerce")
        out_of_range = ((df[rating_col] < 1) | (df[rating_col] > 5)).sum()
        df[rating_col] = df[rating_col].clip(1, 5)
        n_miss = df[rating_col].isna().sum()
        if n_miss > 0:
            median_rating = df[rating_col].median()
            df[rating_col] = df[rating_col].fillna(median_rating)
        if out_of_range > 0:
            log.append(f"✅ Capped **{out_of_range}** out-of-range ratings in **{rating_col}** to [1–5]")
        else:
            log.append(f"✅ **{rating_col}** looks good (range 1–5)")

    # ── Step 8: Clean HOTEL / PROPERTY column ─────────────────────────
    hotel_col = col_map.get("hotel")
    if hotel_col and hotel_col in df.columns:
        df[hotel_col] = df[hotel_col].astype(str).str.strip().str.title()
        df.loc[df[hotel_col].isin(["Nan", "None", ""]), hotel_col] = "Unknown"

    # ── Step 9: Clean GUEST NAME ──────────────────────────────────────
    guest_col = col_map.get("guest")
    if guest_col and guest_col in df.columns:
        df[guest_col] = df[guest_col].astype(str).str.strip().str.title()
        df.loc[df[guest_col].isin(["Nan", "None", ""]), guest_col] = "Anonymous"

    # ── Step 10: Clean CANCELLED flag ─────────────────────────────────
    cancel_col = col_map.get("cancelled")
    if cancel_col and cancel_col in df.columns:
        df[cancel_col] = pd.to_numeric(df[cancel_col], errors="coerce").fillna(0).astype(int)

    # ── Step 11: Clean other numeric columns ──────────────────────────
    for role in ("lead_time", "stay_wkend", "stay_week", "adults", "children"):
        col = col_map.get(role)
        if col and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            neg = (df[col] < 0).sum()
            if neg > 0:
                df[col] = df[col].abs()
            n_miss = df[col].isna().sum()
            if n_miss > 0:
                df[col] = df[col].fillna(0)

    # ── Step 12: Fill any remaining NaN in text columns ───────────────
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("Unknown")

    log.append(f"✅ Final cleaned dataset: **{len(df):,}** rows × **{len(df.columns)}** columns")
    return df, log, currency


# ═══════════════════════════════════════════════════════════════════════
# 6. FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════════════

def add_features(df, col_map: dict) -> tuple[pd.DataFrame, list[str]]:
    """Create derived columns for richer analysis."""
    log = []

    checkin = col_map.get("checkin")
    checkout = col_map.get("checkout")
    price_col = col_map.get("price")
    total_col = col_map.get("total")
    status_col = col_map.get("status")

    # ── Stay length (nights) ──────────────────────────────────────────
    # Method A: from check-in / check-out dates
    if checkin and checkout and checkin in df.columns and checkout in df.columns:
        df["stay_nights"] = (df[checkout] - df[checkin]).dt.days
        # Negative stay = data error (checkout before checkin) → make positive
        df["stay_nights"] = df["stay_nights"].abs()
        # Zero stay → at least 1 night
        df.loc[df["stay_nights"] == 0, "stay_nights"] = 1
        # NaT differences → NaN → fill with median
        med = df["stay_nights"].median()
        df["stay_nights"] = df["stay_nights"].fillna(med if pd.notna(med) else 1).astype(int)
        log.append("🔧 Created **stay_nights** from check-in / check-out dates")

    # Method B: from weekend + week night columns (classic hotel_bookings.csv format)
    elif col_map.get("stay_wkend") and col_map.get("stay_week"):
        wk = col_map["stay_wkend"]
        wd = col_map["stay_week"]
        if wk in df.columns and wd in df.columns:
            df["stay_nights"] = df[wk] + df[wd]
            df.loc[df["stay_nights"] == 0, "stay_nights"] = 1
            log.append("🔧 Created **stay_nights** from weekend + weekday nights")

    # ── Revenue (estimated) ───────────────────────────────────────────
    # If we have a total column, use that directly as revenue
    if total_col and total_col in df.columns:
        df["revenue"] = df[total_col]
        log.append(f"🔧 Using **{total_col}** as **revenue**")
    elif price_col and "stay_nights" in df.columns and price_col in df.columns:
        df["revenue"] = df[price_col] * df["stay_nights"]
        log.append("🔧 Created **revenue** = price × stay_nights")

    # ── Booking date features ─────────────────────────────────────────
    date_src = None
    for role in ("checkin", "checkout"):
        c = col_map.get(role)
        if c and c in df.columns and pd.api.types.is_datetime64_any_dtype(df[c]):
            date_src = c
            break

    if date_src:
        df["booking_month"] = df[date_src].dt.month
        df["booking_year"] = df[date_src].dt.year
        df["booking_weekday"] = df[date_src].dt.day_name()
        log.append(f"🔧 Created **booking_month / year / weekday** from *{date_src}*")
    elif col_map.get("arrival_month") and col_map.get("arrival_year"):
        am = col_map["arrival_month"]
        ay = col_map["arrival_year"]
        if am in df.columns:
            df["booking_month"] = df[am]
        if ay in df.columns:
            df["booking_year"] = df[ay]
        log.append("🔧 Created **booking_month / year** from arrival columns")

    # ── Weekend booking flag ──────────────────────────────────────────
    if "booking_weekday" in df.columns:
        df["is_weekend_booking"] = df["booking_weekday"].isin(["Saturday", "Sunday"])
        log.append("🔧 Created **is_weekend_booking** flag")

    # ── Cancellation helpers ──────────────────────────────────────────
    cancel_col = col_map.get("cancelled")
    if cancel_col and cancel_col in df.columns:
        if "revenue" in df.columns:
            df["revenue_lost"] = 0.0
            mask = df[cancel_col] == 1
            df.loc[mask, "revenue_lost"] = df.loc[mask, "revenue"]
            log.append("🔧 Created **revenue_lost** for cancelled bookings")

    # Derive is_cancelled from status column if no binary column exists
    if status_col and status_col in df.columns and cancel_col not in df.columns:
        df["is_cancelled"] = df[status_col].str.lower().str.contains("cancel", na=False).astype(int)
        col_map["cancelled"] = "is_cancelled"
        log.append("🔧 Created **is_cancelled** from booking status")

    # ── Advance booking days ──────────────────────────────────────────
    lead = col_map.get("lead_time")
    if lead and lead in df.columns:
        df["advance_booking_days"] = df[lead]
        log.append("🔧 Created **advance_booking_days**")

    # ── Average daily rate alias ──────────────────────────────────────
    if price_col and price_col in df.columns:
        df["avg_daily_rate"] = df[price_col]
        log.append(f"🔧 Created **avg_daily_rate** (alias of *{price_col}*)")

    return df, log


# ═══════════════════════════════════════════════════════════════════════
# 7. STREAMLIT PAGE SETUP
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="HotelIQ – Booking Analytics", page_icon="🏨", layout="wide")

# ── Custom CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
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
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# 8. SIDEBAR
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("📂 Load Dataset")

    st.markdown("**Option 1 — Try instantly**")
    use_sample = st.button("📦 Use Sample Dataset", use_container_width=True)

    st.markdown("**Option 2 — Upload your own**")
    uploaded_file = st.file_uploader(
        "Choose a file (CSV, Excel, XLS, TSV)",
        type=SUPPORTED_EXTENSIONS,
        help=(
            "Supports: .csv, .xlsx, .xls, .tsv files.\n\n"
            "**Google Sheets:** File → Download as .csv or .xlsx, then upload here."
        ),
    )

    st.markdown("---")
    st.markdown(
        "**Made by Durgesh Kushwaha**  \n"
        "B.Tech – AI & Data Science  \n"
        "📧 durgeshcgc@gmail.com"
    )


# ═══════════════════════════════════════════════════════════════════════
# 9. DATA SOURCE SELECTION
# ═══════════════════════════════════════════════════════════════════════

st.title("🏨 HotelIQ – Hotel Booking Analytics")
st.caption("Upload your hotel booking file → smart cleaning → rich insights → download.")

if use_sample:
    st.session_state["data_source"] = "sample"
if uploaded_file is not None:
    st.session_state["data_source"] = "upload"
    st.session_state["uploaded_file"] = uploaded_file

data_source = st.session_state.get("data_source")

if data_source is None:
    st.info("👈 **Upload a file** or click **Use Sample Dataset** to get started.")
    st.markdown("""
    ### How it works
    1. **Upload any hotel booking file** (CSV, XLSX, XLS, TSV) — or try the built-in sample.
    2. The app **auto-detects columns** (price, dates, room type, status …) regardless of naming.
    3. **Deep cleaning** fixes currency symbols, negative prices, inconsistent statuses, and more.
    4. Explore **KPI cards** and **interactive Plotly charts**.
    5. **Download** the cleaned dataset when you're done!

    > 💡 The app uses **INR (₹)** as the default currency if none is detected in your data.
    """)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════
# 10. LOAD RAW DATA
# ═══════════════════════════════════════════════════════════════════════

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
        st.error(f"❌ **Could not read the file.** Error: `{e}`")
        st.stop()
    source_label = uploaded_file.name

st.success(f"✅ Loaded **{source_label}** — {raw_df.shape[0]:,} rows × {raw_df.shape[1]} columns")


# ── Raw Data Preview ──────────────────────────────────────────────────
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


# ═══════════════════════════════════════════════════════════════════════
# 11. SMART COLUMN DETECTION
# ═══════════════════════════════════════════════════════════════════════

col_map = detect_columns(raw_df)

with st.expander("🧠 Auto-Detected Columns", expanded=False):
    if col_map:
        det_data = [{"Role": role.replace("_", " ").title(), "Column Found": col} for role, col in col_map.items()]
        st.dataframe(pd.DataFrame(det_data), use_container_width=True, hide_index=True)
    else:
        st.warning("Could not auto-detect any columns. The dashboard will still try to show what it can.")


# ═══════════════════════════════════════════════════════════════════════
# 12. CLEANING
# ═══════════════════════════════════════════════════════════════════════

st.header("🧹 Data Cleaning")
cleaned_df, clean_log, currency = clean_booking_data(raw_df.copy(), col_map)
for msg in clean_log:
    st.markdown(msg)


# ═══════════════════════════════════════════════════════════════════════
# 13. FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════════════

st.header("⚡ Feature Engineering")
final_df, feat_log = add_features(cleaned_df.copy(), col_map)
for msg in feat_log:
    st.markdown(msg)

st.markdown(f"**Final dataset:** {final_df.shape[0]:,} rows × {final_df.shape[1]} columns")

with st.expander("📋 Cleaned Data Preview", expanded=False):
    st.dataframe(final_df.head(20), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════
# 14. DOWNLOAD
# ═══════════════════════════════════════════════════════════════════════

st.header("📥 Download Cleaned Data")
csv_buf = io.BytesIO()
final_df.to_csv(csv_buf, index=False)
csv_buf.seek(0)
st.download_button(
    label="⬇️  Download Cleaned CSV",
    data=csv_buf,
    file_name="cleaned_hotel_bookings.csv",
    mime="text/csv",
)


# ═══════════════════════════════════════════════════════════════════════
# 15. KEY PERFORMANCE INDICATORS
# ═══════════════════════════════════════════════════════════════════════

st.header("📌 Key Performance Indicators")

# ── Calculate KPIs dynamically ────────────────────────────────────────
total_bookings = len(final_df)

# Revenue – from the engineered 'revenue' column, or fall back to total / price col
total_revenue = None
if "revenue" in final_df.columns:
    total_revenue = final_df["revenue"].sum()
elif col_map.get("total") and col_map["total"] in final_df.columns:
    total_revenue = final_df[col_map["total"]].sum()
elif col_map.get("price") and col_map["price"] in final_df.columns:
    total_revenue = final_df[col_map["price"]].sum()

# Average daily rate
avg_rate = None
if "avg_daily_rate" in final_df.columns:
    avg_rate = final_df["avg_daily_rate"].mean()
elif col_map.get("price") and col_map["price"] in final_df.columns:
    avg_rate = final_df[col_map["price"]].mean()

# Cancellation rate
cancel_rate = None
cancel_key = col_map.get("cancelled")
status_key = col_map.get("status")
if cancel_key and cancel_key in final_df.columns:
    cancel_rate = final_df[cancel_key].mean() * 100
elif status_key and status_key in final_df.columns:
    n_cancelled = final_df[status_key].str.lower().str.contains("cancel", na=False).sum()
    cancel_rate = (n_cancelled / len(final_df)) * 100

# Average stay nights
avg_stay = None
if "stay_nights" in final_df.columns:
    avg_stay = final_df["stay_nights"].mean()

# ── Render KPI cards ──────────────────────────────────────────────────
kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.markdown(
        f'<div class="kpi-card"><p>Total Bookings</p><h2>{total_bookings:,}</h2></div>',
        unsafe_allow_html=True,
    )

with kpi_cols[1]:
    val = f"{currency}{total_revenue:,.0f}" if total_revenue is not None else "N/A"
    st.markdown(
        f'<div class="kpi-card"><p>Total Revenue</p><h2>{val}</h2></div>',
        unsafe_allow_html=True,
    )

with kpi_cols[2]:
    val = f"{currency}{avg_rate:,.0f}" if avg_rate is not None else "N/A"
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

# Second row of KPIs
kpi2 = st.columns(4)

with kpi2[0]:
    val = f"{avg_stay:.1f} nights" if avg_stay is not None else "N/A"
    st.markdown(
        f'<div class="kpi-card"><p>Avg Stay Length</p><h2>{val}</h2></div>',
        unsafe_allow_html=True,
    )

with kpi2[1]:
    rating_col = col_map.get("rating")
    avg_rating = final_df[rating_col].mean() if (rating_col and rating_col in final_df.columns) else None
    val = f"{avg_rating:.1f} / 5 ⭐" if avg_rating is not None else "N/A"
    st.markdown(
        f'<div class="kpi-card"><p>Avg Guest Rating</p><h2>{val}</h2></div>',
        unsafe_allow_html=True,
    )

with kpi2[2]:
    room_col = col_map.get("room")
    n_rooms = final_df[room_col].nunique() if (room_col and room_col in final_df.columns) else None
    val = str(n_rooms) if n_rooms is not None else "N/A"
    st.markdown(
        f'<div class="kpi-card"><p>Room Types</p><h2>{val}</h2></div>',
        unsafe_allow_html=True,
    )

with kpi2[3]:
    hotel_col = col_map.get("hotel")
    n_hotels = final_df[hotel_col].nunique() if (hotel_col and hotel_col in final_df.columns) else None
    val = str(n_hotels) if n_hotels is not None else "N/A"
    st.markdown(
        f'<div class="kpi-card"><p>Properties / Hotels</p><h2>{val}</h2></div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# 16. CHARTS – each one gracefully skipped if data is unavailable
# ═══════════════════════════════════════════════════════════════════════

st.header("📊 Visualizations")

chart_count = 0  # track how many charts we actually render

# ── 1. Monthly Booking Trends ─────────────────────────────────────────
if "booking_month" in final_df.columns:
    st.subheader("📅 Monthly Booking Trends")
    monthly = final_df["booking_month"].value_counts().sort_index().reset_index()
    monthly.columns = ["Month", "Bookings"]

    # Handle numeric months → names
    if monthly["Month"].dtype in ("int64", "float64"):
        monthly["Month Name"] = monthly["Month"].map(MONTH_NAMES)
        x_col = "Month Name"
        cat_order = list(MONTH_NAMES.values())
    else:
        monthly["Month Name"] = monthly["Month"]
        x_col = "Month Name"
        cat_order = None

    fig = px.bar(
        monthly, x=x_col, y="Bookings",
        title="Number of Bookings per Month",
        labels={x_col: "Month", "Bookings": "Bookings"},
        color="Bookings",
        color_continuous_scale="Viridis",
    )
    if cat_order:
        fig.update_layout(xaxis=dict(categoryorder="array", categoryarray=cat_order))
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    chart_count += 1


# ── 2. Booking Status Distribution ────────────────────────────────────
status_col = col_map.get("status")
if status_col and status_col in final_df.columns:
    st.subheader("📋 Booking Status Distribution")
    status_counts = final_df[status_col].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(
            status_counts, names="Status", values="Count",
            title="Booking Status Breakdown", hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            status_counts, x="Status", y="Count", color="Status",
            title="Booking Status Counts",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig, use_container_width=True)
    chart_count += 1


# ── 3. Revenue by Hotel / Property ────────────────────────────────────
hotel_col = col_map.get("hotel")
if hotel_col and hotel_col in final_df.columns and "revenue" in final_df.columns:
    st.subheader("💰 Revenue by Property / Hotel")
    rev_hotel = final_df.groupby(hotel_col)["revenue"].sum().sort_values(ascending=False).head(15).reset_index()
    rev_hotel.columns = ["Hotel", "Revenue"]
    fig = px.bar(
        rev_hotel, x="Hotel", y="Revenue", color="Hotel",
        title=f"Top 15 – Total Revenue by Hotel ({currency})",
        labels={"Revenue": f"Revenue ({currency})"},
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    chart_count += 1


# ── 4. Room Type Distribution ─────────────────────────────────────────
room_col = col_map.get("room")
if room_col and room_col in final_df.columns:
    st.subheader("🛏️ Room Type Distribution")
    room_counts = final_df[room_col].value_counts().reset_index()
    room_counts.columns = ["Room Type", "Count"]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(
            room_counts, names="Room Type", values="Count",
            title="Booking Share by Room Type", hole=0.35,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            room_counts, x="Room Type", y="Count", color="Room Type",
            title="Room Type Counts",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    chart_count += 1


# ── 5. Price Distribution (Histogram + Box) ──────────────────────────
price_col = col_map.get("price")
if price_col and price_col in final_df.columns:
    st.subheader(f"💵 Price Distribution ({price_col})")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(
            final_df, x=price_col, nbins=40,
            title=f"Distribution of {price_col}",
            labels={price_col: f"Price ({currency})"},
            color_discrete_sequence=["#667eea"],
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if room_col and room_col in final_df.columns:
            fig = px.box(
                final_df, x=room_col, y=price_col, color=room_col,
                title=f"Price by Room Type",
                labels={price_col: f"Price ({currency})", room_col: "Room Type"},
            )
            fig.update_layout(showlegend=False)
        else:
            fig = px.box(
                final_df, y=price_col,
                title=f"Price Box Plot",
                labels={price_col: f"Price ({currency})"},
            )
        st.plotly_chart(fig, use_container_width=True)
    chart_count += 1


# ── 6. Revenue Over Time ─────────────────────────────────────────────
if "booking_month" in final_df.columns and "revenue" in final_df.columns:
    st.subheader("📈 Revenue Over Time")

    if "booking_year" in final_df.columns:
        # Group by year + month
        rev_time = final_df.groupby(["booking_year", "booking_month"])["revenue"].sum().reset_index()
        rev_time.columns = ["Year", "Month", "Revenue"]
        if rev_time["Month"].dtype in ("int64", "float64"):
            rev_time["Month Name"] = rev_time["Month"].map(MONTH_NAMES)
        else:
            rev_time["Month Name"] = rev_time["Month"]
        rev_time["Period"] = rev_time["Year"].astype(str) + " " + rev_time["Month Name"].astype(str)
        fig = px.bar(
            rev_time, x="Period", y="Revenue",
            title=f"Monthly Revenue Trend ({currency})",
            labels={"Revenue": f"Revenue ({currency})"},
            color="Revenue", color_continuous_scale="Viridis",
        )
        fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-45)
    else:
        rev_time = final_df.groupby("booking_month")["revenue"].sum().reset_index()
        rev_time.columns = ["Month", "Revenue"]
        if rev_time["Month"].dtype in ("int64", "float64"):
            rev_time["Month Name"] = rev_time["Month"].map(MONTH_NAMES)
        else:
            rev_time["Month Name"] = rev_time["Month"]
        fig = px.bar(
            rev_time, x="Month Name", y="Revenue",
            title=f"Revenue by Month ({currency})",
            labels={"Revenue": f"Revenue ({currency})"},
            color="Revenue", color_continuous_scale="Viridis",
        )
        fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    chart_count += 1


# ── 7. Guest Rating Distribution ─────────────────────────────────────
rating_col = col_map.get("rating")
if rating_col and rating_col in final_df.columns:
    st.subheader("⭐ Guest Rating Distribution")
    fig = px.histogram(
        final_df, x=rating_col, nbins=10,
        title="Distribution of Guest Ratings",
        labels={rating_col: "Rating (1–5)"},
        color_discrete_sequence=["#f39c12"],
    )
    st.plotly_chart(fig, use_container_width=True)
    chart_count += 1


# ── 8. Cancellation Analysis ─────────────────────────────────────────
cancel_col = col_map.get("cancelled")
if cancel_col and cancel_col in final_df.columns:
    st.subheader("❌ Cancellation Analysis")
    cancel_counts = final_df[cancel_col].value_counts().reset_index()
    cancel_counts.columns = ["Status", "Count"]
    cancel_counts["Status"] = cancel_counts["Status"].map({0: "Not Cancelled", 1: "Cancelled"})
    cancel_counts = cancel_counts.dropna(subset=["Status"])
    fig = px.bar(
        cancel_counts, x="Status", y="Count", color="Status",
        title="Cancelled vs Not Cancelled",
        color_discrete_map={"Not Cancelled": "#2ecc71", "Cancelled": "#e74c3c"},
    )
    st.plotly_chart(fig, use_container_width=True)
    chart_count += 1


# ── 9. Advance Booking vs Price ───────────────────────────────────────
if "advance_booking_days" in final_df.columns and price_col and price_col in final_df.columns:
    st.subheader("📆 Advance Booking Days vs Price")
    sample_size = min(5000, len(final_df))
    sample = final_df.sample(sample_size, random_state=42)
    fig = px.scatter(
        sample, x="advance_booking_days", y=price_col,
        opacity=0.45,
        title="Does Booking Earlier Affect Price?",
        labels={
            "advance_booking_days": "Advance Booking Days",
            price_col: f"Price ({currency})",
        },
        color_discrete_sequence=["#667eea"],
    )
    st.plotly_chart(fig, use_container_width=True)
    chart_count += 1


# ── 10. Stay Length Distribution ──────────────────────────────────────
if "stay_nights" in final_df.columns:
    st.subheader("🌙 Stay Length Distribution")
    fig = px.histogram(
        final_df, x="stay_nights", nbins=30,
        title="Distribution of Stay Length (Nights)",
        labels={"stay_nights": "Nights"},
        color_discrete_sequence=["#1abc9c"],
    )
    st.plotly_chart(fig, use_container_width=True)
    chart_count += 1


# ── 11. Top Guests by Revenue ─────────────────────────────────────────
guest_col = col_map.get("guest")
if guest_col and guest_col in final_df.columns and "revenue" in final_df.columns:
    non_anon = final_df[final_df[guest_col] != "Anonymous"]
    if len(non_anon) > 0:
        st.subheader("👤 Top 10 Guests by Revenue")
        top_guests = non_anon.groupby(guest_col)["revenue"].sum().sort_values(ascending=False).head(10).reset_index()
        top_guests.columns = ["Guest", "Revenue"]
        fig = px.bar(
            top_guests, x="Revenue", y="Guest", orientation="h",
            title=f"Top 10 Guests by Revenue ({currency})",
            labels={"Revenue": f"Revenue ({currency})"},
            color="Revenue", color_continuous_scale="Viridis",
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        chart_count += 1


# ── Fallback: if no charts were rendered ──────────────────────────────
if chart_count == 0:
    st.info("No charts could be generated. Please check that your dataset has price, date, or status columns.")


# ═══════════════════════════════════════════════════════════════════════
# 17. FOOTER
# ═══════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    "Made with ❤️ by **Durgesh Kushwaha** · "
    "B.Tech – AI & Data Science · "
    "📧 durgeshcgc@gmail.com"
)
