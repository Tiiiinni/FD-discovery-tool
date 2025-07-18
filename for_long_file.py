import streamlit as st
import pandas as pd
from itertools import combinations
import math

#  Custom CSS styling
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


#  Functional Dependency Finder
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

#  Estimate total checks
def estimate_fd_checks(n_cols, max_lhs_size):
    total_checks = 0
    for k in range(1, max_lhs_size + 1):
        n_lhs = math.comb(n_cols, k)
        n_rhs = n_cols - k
        total_checks += n_lhs * n_rhs
    return total_checks

#  Streamlit UI
st.title("Dynamic FD Discovery Tool")

uploaded_file = st.file_uploader(
    "Upload your CSV or Excel table", 
    type=["csv", "xls", "xlsx"]
)

df = None  # Initialize dataframe

if uploaded_file:
    try:
        #  Handle Excel or CSV
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            xls = pd.ExcelFile(uploaded_file)
            sheet_name = st.selectbox(
                "Select sheet to load:",
                options=xls.sheet_names
            )
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)

        if df.empty:
            st.warning("Uploaded file is empty.")
        else:
            st.write("### Full Uploaded Data")
            st.dataframe(df)

            #  Let user pick columns
            selected_columns = st.multiselect(
                "Select columns to analyze for FDs:",
                options=df.columns.tolist(),
                default=df.columns.tolist()
            )

            if selected_columns:
                df = df[selected_columns]
                n_cols = len(selected_columns)

                # Sampling for large datasets
                MAX_ROWS = 5000
                if len(df) > MAX_ROWS:
                    df = df.sample(MAX_ROWS, random_state=42)
                    st.info(f"Dataset sampled to {MAX_ROWS} rows for faster analysis.")

                #  Automatically decide LHS size
                if n_cols <= 5:
                    max_lhs_size = n_cols - 1
                elif n_cols <= 10:
                    max_lhs_size = 3
                else:
                    max_lhs_size = 2

                total_checks = estimate_fd_checks(n_cols, max_lhs_size)

                st.info(
                    f"Automatically limiting LHS size to {max_lhs_size} "
                    f"→ estimated {total_checks:,} FD checks."
                )

                #  Warn user if too big
                SAFE_LIMIT = 10_000
                override = False

                if total_checks > SAFE_LIMIT:
                    st.warning(
                        f"⚠️ Full FD discovery may be very slow "
                        f"({total_checks:,} combinations to check). "
                        f"Proceed at your own risk!"
                    )
                    override = st.checkbox(
                        "Proceed anyway with full FD discovery?",
                        value=False
                    )

                if st.button("Find Functional Dependencies"):
                    if total_checks > SAFE_LIMIT and not override:
                        st.error(
                            "FD discovery aborted for safety. "
                            "Too many combinations. "
                            "Select fewer columns or allow override."
                        )
                    else:
                        with st.spinner("Finding Functional Dependencies..."):
                            fds = find_functional_dependencies(df, max_lhs_size)

                        if fds:
                            fd_table = pd.DataFrame(
                                [( ", ".join(lhs), rhs ) for lhs, rhs in fds ],
                                columns=["Determinant (LHS)", "Dependent (RHS)"]
                            )
                            st.write("### Discovered Functional Dependencies:")
                            st.dataframe(fd_table)
                        else:
                            st.write("No functional dependencies found.")
            else:
                st.info("Please select at least one column to analyze.")

    except Exception as e:
        st.error(f" Error reading file: {e}")
