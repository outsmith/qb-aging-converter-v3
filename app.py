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
if "show_upload_ui" not in st.session_state:
    st.session_state.show_upload_ui = True


# ---------- PROCESSING FUNCTION ----------
def process_uploaded_file(uploaded_file, class_input):
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

        # Reset upload interface and force rerun
        st.session_state.show_upload_ui = False
        st.session_state.reset_uploader += 1
        st.experimental_rerun()

    except Exception as e:
        st.error(f"Error processing file: {e}")


# ---------- UPLOAD INTERFACE ----------
if st.session_state.bills or st.session_state.credits:
    st.markdown("### ➕ Add another AP aging report?")

if st.session_state.show_upload_ui:

    upload_key = "uploader_" + str(st.session_state.reset_uploader)
    class_key = "class_choice_" + str(st.session_state.reset_uploader)
    custom_key = "custom_input_" + str(st.session_state.reset_uploader)

    uploaded_file = st.file_uploader("Upload Excel Aging Report", type="xlsx", key=upload_key)

    if uploaded_file:
        selected_class = st.radio(
            "Select class for this aging:",
            options=["Auto Perfection", "KHI", "Land Quest", "Other"],
            key=class_key,
            horizontal=True
        )

        custom_class = ""
        if selected_class == "Other":
            custom_class = st.text_input("Enter custom class name:", key=custom_key)

        if st.button("✅ Submit Aging"):
            if selected_class == "Other":
                if not custom_class.strip():
                    st.warning("Please enter a custom class name.")
                else:
                    process_uploaded_file(uploaded_file, custom_class.strip())
            else:
                process_uploaded_file(uploaded_file, selected_class)

else:
    if st.button("➕ Add Another Aging"):
        st.session_state.show_upload_ui = True


# ---------- LIVE PREVIEW ----------
if st.session_state.bills:
    st.subheader("🧾 All Bills Added So Far")
    all_bills = pd.concat(st.session_state.bills, ignore_index=True)
    st.dataframe(all_bills)

if st.session_state.credits:
    st.subheader("📘 All Vendor Credits Added So Far")
    all_credits = pd.concat(st.session_state.credits, ignore_index=True)
    st.dataframe(all_credits)


# ---------- DOWNLOADS ----------
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


# ---------- RESET BUTTON ----------
if st.button("🔁 Reset Everything"):
    st.session_state.bills = []
    st.session_state.credits = []
    st.session_state.reset_uploader = 0
    st.session_state.show_upload_ui = True
    st.success("Session cleared.")
