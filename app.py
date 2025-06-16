import streamlit as st
import pandas as pd

st.set_page_config(page_title="Multi-Client AP Aging to CSV")

st.title("📂 Multi-Client AP Aging → Consolidated Bill & Credit Converter")

# Session-state storage
if "bills" not in st.session_state:
    st.session_state.bills = []
if "credits" not in st.session_state:
    st.session_state.credits = []

uploaded_file = st.file_uploader("Upload Excel Aging Report", type="xlsx")

if uploaded_file:
    class_input = st.text_input("Class?", key=f"class_{uploaded_file.name}")
    
    if class_input:
        try:
            df = pd.read_excel(uploaded_file, sheet_name=0, header=4)

            # Rename 'Unnamed: 9' to 'Select' if needed
            if "Unnamed: 9" in df.columns:
                df.rename(columns={"Unnamed: 9": "Select"}, inplace=True)

            # Drop extra Unnamed or index columns
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

            # Remove header rows or junk
            df = df[df["Date"] != "Date"]
            df = df[pd.to_datetime(df["Date"], errors="coerce").notna()]
            df.reset_index(drop=True, inplace=True)

            # Filter to selected rows
            df = df[df["Select"].astype(str).str.lower().fillna("") == "x"]

            if df.empty:
                st.warning(f"No selected rows with 'x' in '{uploaded_file.name}'")
            else:
                # Drop 'Amount' column if exists
                if "Amount" in df.columns:
                    df.drop(columns=["Amount"], inplace=True)

                df["Open balance"] = df["Open balance"].replace(",", "", regex=True).astype(float)

                # Add Class column
                df["Class"] = class_input

                # Split
                bills_df = df[df["Open balance"] > 0].copy()
                credits_df = df[df["Open balance"] < 0].copy()

                def format_output(d):
                    d = d.rename(columns={
                        "Date": "BillDate",
                        "Due date": "DueDate",
                        "Open balance": "Amount",
                        "Num": "RefNumber"
                    })
                    d = d[["Vendor display name", "BillDate", "DueDate", "Amount", "RefNumber", "Class"]]
                    d = d.rename(columns={"Vendor display name": "Vendor"})
                    d["BillDate"] = pd.to_datetime(d["BillDate"], errors="coerce").dt.strftime("%m/%d/%Y")
                    d["DueDate"] = pd.to_datetime(d["DueDate"], errors="coerce").dt.strftime("%m/%d/%Y")
                    return d

                st.success(f"Processed {uploaded_file.name} for class: {class_input}")

                if not bills_df.empty:
                    formatted_bills = format_output(bills_df)
                    st.session_state.bills.append(formatted_bills)
                    st.dataframe(formatted_bills)

                if not credits_df.empty:
                    formatted_credits = format_output(credits_df)
                    st.session_state.credits.append(formatted_credits)
                    st.dataframe(formatted_credits)

        except Exception as e:
            st.error(f"Error: {e}")

# After uploads, offer consolidated downloads
if st.session_state.bills:
    all_bills = pd.concat(st.session_state.bills, ignore_index=True)
    csv_bills = all_bills.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 Download Consolidated Bills CSV", data=csv_bills, file_name="all_bills.csv", mime="text/csv")

if st.session_state.credits:
    all_credits = pd.concat(st.session_state.credits, ignore_index=True)
    csv_credits = all_credits.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 Download Consolidated Credits CSV", data=csv_credits, file_name="all_credits.csv", mime="text/csv")

# Reset button
if st.button("🔁 Reset Session"):
    st.session_state.bills = []
    st.session_state.credits = []
    st.success("Session cleared.")
