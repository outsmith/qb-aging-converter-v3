import streamlit as st
import pandas as pd

st.set_page_config(page_title="Multi-Client AP Aging")

st.title("📂 Multi-Client AP Aging → Consolidated Bill & Credit Converter")

# ---------- SESSION STATE SETUP ----------
if "bills" not in st.session_state:
    st.session_state.bills = []
if "credits" not in st.session_state:
    st.session_state.credits = []
if "reset_uploader" not in st.session_state:
    st.session_state.reset_uploader = 0
if "ready_for_class" not in st.session_state:
    st.session_state.ready_for_class = False
if "upload_complete" not in st.session_state:
    st.session_state.upload_complete = False
if "custom_class" not in st.session_state:
    st.session_state.custom_class = ""
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None


# ---------- PROCESSING FUNCTION ----------
def process_uploaded_file(class_input):
    uploaded_file = st.session_state.uploaded_file

    if not uploaded_file or not class_input:
        return

    try:
        df = pd.read_excel(uploaded_file, sheet_name=0, header=4)

        if "Unnamed: 9" in df.columns:
            df.rename(columns={"Unnamed: 9": "Select"}, inplace=True)

        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df = df[df["Date"] != "Date"]
        df = df[pd.to_datetime(df["Date"], errors="coerce").notna()]
        df.reset_index(drop=True, inplace=True)

        df = df[df["Select"].astype(str).str.lower().fillna("") == "x"]

        if df.empty:
            st.warning("No rows marked with 'x'.")
            return

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
            st.session_state.bills.append(format_output(bills_df))
            st.success(f"{len(bills_df)} bill(s) added for class: {class_input}")

        if not credits_df.empty:
            st.session_state.credits.append(format_output(credits_df))
            st.success(f"{len(credits_df)} credit(s) added for class: {class_input}")

        # Reset for next round
        st.session_state.uploaded_file = None
        st.session_state.custom_class = ""
        st.session_state.ready_for_class = False
        st.session_state.upload_complete = True
        st.session_state.reset_uploader += 1

    except Exception as e:
        st.error(f"Error processing file: {e}")


# ---------- FILE UPLOADER ----------
if st.session_state.bills or st.session_state.credits:
    st.markdown("### ➕ Add another AP aging report?")

uploaded_file = st.file_uploader(
    "Upload Excel Aging Report",
    type="xlsx",
    key="file_upload_" + str(st.session_state.reset_uploader)
)

if uploaded_file:
    st.session_state.uploaded_file = uploaded_file
    st.session_state.ready_for_class = True


# ---------- CLASS SELECTION ----------
if st.session_state.ready_for_class:
    selected_class = st.selectbox(
        "Select class for this aging:",
        options=["Auto Perfection", "KHI", "Land Quest", "Other"],
        key="selected_class_" + str(st.session_state.reset_uploader)
    )

    if selected_class == "Other":
        st.text_input(
            "Enter custom class name:",
            key="custom_class_" + str(st.session_state.reset_uploader),
            on_change=lambda: process_uploaded_file(
                st.session_state.get("custom_class_" + str(st.session_state.reset_uploader), "").strip()
            )
        )
    else:
        process_uploaded_file(selected_class)


# ---------- LIVE PREVIEW ----------
if st.session_state.bills:
    st.subheader("🧾 All Bills Added So Far")
    all_bills = pd.concat(st.session_state.bills, ignore_index=True)
    st.dataframe(all_bills)

if st.session_state.credits:
    st.subheader("📘 All Vendor Credits Added So Far")
    all_credits = pd.concat(st.session_state.credits, ignore_index=True)
    st.dataframe(all_credits)


# ---------- DOWNLOAD BUTTONS ----------
if st.session_state.bills:
    st.download_button(
        "📥 Download All Bills",
        data=all_bills.to_csv(index=False).encode("utf-8-sig"),
        file_name="all_bills.csv",
        mime="text/csv"
    )

if st.session_state.credits:
    st.download_button(
        "📥 Download All Vendor Credits",
        data=all_credits.to_csv(index=False).encode("utf-8-sig"),
        file_name="all_credits.csv",
        mime="text/csv"
    )


# ---------- RESET EVERYTHING ----------
if st.button("🔁 Reset Everything"):
    st.session_state.bills = []
    st.session_state.credits = []
    st.session_state.uploaded_file = None
    st.session_state.reset_uploader = 0
    st.session_state.ready_for_class = False
    st.session_state.upload_complete = False
    st.session_state.custom_class = ""
    st.success("Session cleared.")
