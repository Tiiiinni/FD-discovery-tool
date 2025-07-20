import streamlit as st
import pandas as pd
from itertools import combinations
import math

# --- Custom CSS Styling ---
st.markdown("""
    <style>
    .stApp {
        background-color: #fef6e4;
        color: #001858;
        font-family: 'Segoe UI', sans-serif;
    }
    .css-10trblm {
        color: #001858;
        font-size: 36px;
        font-weight: bold;
    }
    div.stButton > button:first-child {
        background-color: #8bd3dd;
        color: #001858;
        height: 50px;
        width: 100%;
        font-size: 18px;
        border-radius: 12px;
        transition: 0.3s;
        border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #f582ae;
        color: #001858;
    }
    .stDataFrame {
        background-color: #ffffffcc;
    }
    .stAlert {
        background-color: #fcd5ce;
        color: #001858;
    }
    </style>
""", unsafe_allow_html=True)

# --- Utility Functions ---
def normalize_data(df):
    return df.applymap(lambda x: str(x).strip().lower() if pd.notnull(x) else x)

def clean_data(df):
    return df.fillna("null")

def find_functional_dependencies(df, max_lhs_size):
    fds = []
    columns = df.columns.tolist()
    for i in range(1, max_lhs_size + 1):
        for lhs in combinations(columns, i):
            lhs = list(lhs)
            for rhs in columns:
                if rhs in lhs:
                    continue
                try:
                    grouped = df.groupby(lhs)[rhs].nunique()
                    if (grouped <= 1).all():
                        fds.append((lhs, rhs))
                except Exception:
                    continue
    return fds

def estimate_fd_checks(n_cols, max_lhs_size):
    total = 0
    for k in range(1, max_lhs_size + 1):
        n_lhs = math.comb(n_cols, k)
        n_rhs = n_cols - k
        total += n_lhs * n_rhs
    return total

# --- Streamlit App ---
st.title("Dynamic FD Discovery Tool")

uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])
df = None

if uploaded_file:
    try:
        if uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file)
        else:
            xls = pd.ExcelFile(uploaded_file)
            sheet = st.selectbox("Select sheet to load:", xls.sheet_names)
            df = pd.read_excel(uploaded_file, sheet_name=sheet, engine="openpyxl")

        if df is not None and not df.empty:
            st.write("### 1️⃣ Full Uploaded Data")
            st.dataframe(df)

            selected_columns = st.multiselect("Select columns to analyze:", df.columns.tolist(), default=df.columns.tolist())

            if selected_columns:
                df_sel = df[selected_columns].copy()
                
                # Always clean data first
                df_cleaned = clean_data(df_sel)
                st.write("### 2️⃣ Cleaned Data (missing → 'null')")
                st.dataframe(df_cleaned)

                # Normalize button
                if st.button("Normalize Data"):
                    df_normalized = normalize_data(df_cleaned)
                    st.session_state.df_ready = df_normalized  # Save to session state
                    st.session_state.show_norm = True

                # Show normalized table if already done
                if st.session_state.get("show_norm", False) and "df_ready" in st.session_state:
                    df_ready = st.session_state.df_ready
                    st.write("### 3️⃣ Normalized Data (trimmed, lowercase):")
                    st.dataframe(df_ready)

                    n_cols = len(df_ready.columns)

                    if len(df_ready) > 5000:
                        df_ready = df_ready.sample(5000, random_state=42)
                        st.info("Dataset sampled to 5,000 rows for faster processing.")

                    # Auto-limit LHS size
                    if n_cols <= 5:
                        max_lhs_size = n_cols - 1
                    elif n_cols <= 10:
                        max_lhs_size = 3
                    else:
                        max_lhs_size = 2

                    total_checks = estimate_fd_checks(n_cols, max_lhs_size)
                    st.info(f"LHS size limited to {max_lhs_size} → Estimated {total_checks:,} FD checks.")

                    SAFE_LIMIT = 10_000
                    override = False
                    if total_checks > SAFE_LIMIT:
                        st.warning(f"⚠️ High computation: ~{total_checks:,} FD checks.")
                        override = st.checkbox("Proceed anyway?")

                    if st.button("Find Functional Dependencies"):
                        if total_checks > SAFE_LIMIT and not override:
                            st.error("Aborted: too many combinations. Reduce columns or override.")
                        else:
                            with st.spinner("Analyzing..."):
                                fds = find_functional_dependencies(df_ready, max_lhs_size)

                            if fds:
                                fd_table = pd.DataFrame([( ", ".join(lhs), rhs ) for lhs, rhs in fds], columns=["LHS →", "RHS"])
                                st.write("### ✅ Discovered Functional Dependencies")
                                st.dataframe(fd_table)
                            else:
                                st.info("No functional dependencies found.")
            else:
                st.info("Please select at least one column.")
        else:
            st.warning("Uploaded file is empty.")
    except Exception as e:
        st.error(f"Error loading file: {e}")
