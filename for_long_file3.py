import streamlit as st
import pandas as pd
from itertools import combinations
import math

# Custom CSS styling
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


# Functional Dependency Finder
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


# Estimate total FD checks
def estimate_fd_checks(n_cols, max_lhs_size):
    total_checks = 0
    for k in range(1, max_lhs_size + 1):
        n_lhs = math.comb(n_cols, k)
        n_rhs = n_cols - k
        total_checks += n_lhs * n_rhs
    return total_checks


# Streamlit UI
st.title("Dynamic FD Discovery Tool")

uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])
df = None

if uploaded_file:
    try:
        # Handle CSV or Excel with proper library support
        if uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file)
        else:
            try:
                xls = pd.ExcelFile(uploaded_file)
                sheet_name = st.selectbox("Select sheet to load:", options=xls.sheet_names)
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name, engine="openpyxl")
            except ImportError:
                st.error("Missing required package `openpyxl`. Please install it using `pip install openpyxl`.")
            except Exception as e:
                st.error(f"Error loading Excel file: {e}")

        if df is not None and not df.empty:
            st.write("### Full Uploaded Data")
            st.dataframe(df)

            selected_columns = st.multiselect(
                "Select columns to analyze for FDs:",
                options=df.columns.tolist(),
                default=df.columns.tolist()
            )

            if selected_columns:
                df = df[selected_columns]
                n_cols = len(selected_columns)

                MAX_ROWS = 5000
                if len(df) > MAX_ROWS:
                    df = df.sample(MAX_ROWS, random_state=42)
                    st.info(f"Dataset sampled to {MAX_ROWS} rows for faster analysis.")

                if n_cols <= 5:
                    max_lhs_size = n_cols - 1
                elif n_cols <= 10:
                    max_lhs_size = 3
                else:
                    max_lhs_size = 2

                total_checks = estimate_fd_checks(n_cols, max_lhs_size)
                st.info(f"Automatically limiting LHS size to {max_lhs_size} → estimated {total_checks:,} FD checks.")

                SAFE_LIMIT = 10_000
                override = False

                if total_checks > SAFE_LIMIT:
                    st.warning(
                        f"⚠️ Full FD discovery may be very slow ({total_checks:,} combinations)."
                    )
                    override = st.checkbox("Proceed anyway?", value=False)

                if st.button("Find Functional Dependencies"):
                    if total_checks > SAFE_LIMIT and not override:
                        st.error("FD discovery aborted. Too many combinations. Reduce columns or allow override.")
                    else:
                        with st.spinner("Analyzing..."):
                            fds = find_functional_dependencies(df, max_lhs_size)

                        if fds:
                            fd_table = pd.DataFrame(
                                [( ", ".join(lhs), rhs ) for lhs, rhs in fds ],
                                columns=["Determinant (LHS)", "Dependent (RHS)"]
                            )
                            st.write("### Discovered Functional Dependencies:")
                            st.dataframe(fd_table)
                        else:
                            st.info("No functional dependencies found.")
            else:
                st.info("Please select at least one column.")

        elif df is not None and df.empty:
            st.warning("Uploaded file is empty.")

    except Exception as e:
        st.error(f"Unexpected error: {e}")
