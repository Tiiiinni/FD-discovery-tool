import streamlit as st
import pandas as pd
from itertools import combinations

#  Custom CSS styling
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f8ff;
    }

    .css-10trblm {
        color: #1e3d59;
        font-size: 36px;
        font-weight: bold;
    }

    div.stButton > button:first-child {
        background-color: #ff5733;
        color: white;
        height: 50px;
        width: 100%;
        font-size: 18px;
        border-radius: 12px;
        transition: 0.3s;
    }

    div.stButton > button:first-child:hover {
        background-color: #c70039;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

#  FD finding function (no LHS limit)
def find_functional_dependencies(df):
    fds = []
    columns = df.columns.tolist()
    
    for i in range(1, len(columns)):
        for lhs in combinations(columns, i):
            lhs = list(lhs)
            for rhs in columns:
                if rhs in lhs:
                    continue
                grouped = df.groupby(lhs)[rhs].nunique()
                if (grouped <= 1).all():
                    fds.append((lhs, rhs))
    return fds

# Streamlit UI
st.title("FD Discovery Tool")

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
            st.write("### Preview of Uploaded Data")
            st.dataframe(df.head())

            #  Let user pick columns
            selected_columns = st.multiselect(
                "Select columns to analyze for FDs:",
                options=df.columns.tolist(),
                default=df.columns.tolist()
            )

            if selected_columns:
                df = df[selected_columns]

                #  Sampling for large datasets
                MAX_ROWS = 10000
                if len(df) > MAX_ROWS:
                    df = df.sample(MAX_ROWS, random_state=42)
                    st.info(f"Dataset sampled to {MAX_ROWS} rows for faster analysis.")

                if st.button("Find Functional Dependencies"):
                    fds = find_functional_dependencies(df)
                    
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
        st.error(f"Error reading file: {e}")
