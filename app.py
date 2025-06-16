import streamlit as st
import pandas as pd

st.set_page_config(page_title="Multi-Client AP Aging")

st.title("📂 Multi-Client AP Aging → Consolidated Bill & Credit Converter")

# Initialize memory
if "bills" not in st.session_state:
    st.session_state.bills = []
if "credits" not in st.session_state:
    st.session_state.credits = []

# Upload one at a time
uploaded_file = st.file_uploader("Upload Excel Aging Report", type="xlsx")

if uploaded_file:
    class_input = st.text_input("Class for this aging:")

    if class_input:
        try:
            df = pd.read_excel(uploaded_file, sheet_name=0, header=4)

            # Rename selection column
            if "Unnamed: 9" in df.columns:
                df.rename(columns={"Unnamed: 9": "Select"}, inplace=True)

            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
            df = df[df["Date"] != "Date"]
            df = df[pd.to_datetime(df["Date"], errors="coerce").notna()]
            df.reset_index(drop=True, inplace=True)

            df = df[df["Select"].astype(str).str.lower().fillna("") == "x"]

            if df.empty:
                st.warning("No rows marked with 'x'.")
            else:
                if "Amount" in df.columns:
                    df.drop(columns=["Amount"], inplace=True)

                df["Open balance"] = df["Open balance"].replace(",", "", regex=True).astype(float)
                df["Class"] = class_input

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

                if not bills_df.empty:
                    out_bills = format_output(bills_df)
                    st.session_state.bills.append(out_bills)
                    st.success(f"{len(out_bills)} bill(s) added for class: {class_input}")
                    st.dataframe(out_bills)

                if not credits_df.empty:
                    out_credits = format_output(credits_df)
                    st.session_state.credits.append(out_credits)
                    st.success(f"{len(out_credits)} credit(s) added for class: {class_input}")
                    st.dataframe(out_credits)

                # Clear upload after success so user can upload another
                st.rerun()

        except Exception as e:
            st.error(f"Error processing file: {e}")

# Combined downloads
if st.session_state.bills:
    all_bills = pd.concat(st.session_state.bills, ignore_index=True)
    st.download_button("📥 Download All Bills", data=all_bills.to_csv(index=False).encode("utf-8-sig"), file_name="all_bills.csv", mime="text/csv")

if st.session_state.credits:
    all_credits = pd.concat(st.session_state.credits, ignore_index=True)
    st.download_button("📥 Download All Vendor Credits", data=all_credits.to_csv(index=False).encode("utf-8-sig"), file_name="all_credits.csv", mime="text/csv")

if st.button("🔁 Reset Everything"):
    st.session_state.bills = []
    st.session_state.credits = []
    st.success("Session cleared.")
