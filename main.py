import os
import base64
import pandas as pd
from datetime import datetime
import gspread
import random
import json
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

DEV = False

if DEV:
    PASSCODE = os.getenv("PASSCODE")
    GOOGLE_CRED = os.getenv('GOOGLE_CRED')
else:
    PASSCODE = st.secrets['passcode']
    GOOGLE_CRED = st.secrets['google_cred']

decoded_bytes = base64.b64decode(GOOGLE_CRED)
decoded_str = decoded_bytes.decode('utf-8')
cred = json.loads(decoded_str)

FUNNY_GIFS = [
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExendsbXc5OGh3djdxaDU4Mjd3bDV0cXB3YmtldjRvcmx1dGZxcWNyaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/bKj0qEKTVBdF2o5Dgn/giphy.gif",
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExZGQwZXBlOGptazA3YnhscjNpeHVxbnVlczlsbWNmMmg0NGd1aHg3dyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/5SAPlGAS1YnLN9jHua/giphy.gif",
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExMnc2OWFra3Vocm5rYXM4enNmeHIxemR6cHM0NHgxN2NoenhidnRlOSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/98maV70oAqIZtEYqB4/giphy.gif",
    "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExOGxvZzlwdHo3OXNxeW16cXMxYnZhbW0zeW40aWEzZmNoaWZpODQ4MiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oz8xLd9DJq2l2VFtu/giphy.gif",
]

# Session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Hello, Gaurang!")

    passcode = st.text_input("Enter secret code...", type="password")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        launch_input = st.button("Lanuch 🚀")
    if launch_input:
        if passcode == PASSCODE:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Incorrect passcode! Try again.")
            st.image(random.choice(FUNNY_GIFS), use_container_width=True)

    st.stop()

# Constants
SHEET_NAME = "Expenses"  # Google Sheet Name
BACKUP_SHEET_NAME = "Expense_backup"
PAYMENT_METHOD_OPTIONS = ['Credit Card', 'Debit Card']
NOT_EXPENSE_OPTIONS = ['Date', 'Income', 'Credit', 'CC Debt', 'CC Payment', 'Comments']
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# Google Sheets Auth and Client Setup
def authenticate_google_sheets():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred, scope)
    return gspread.authorize(creds)


# Load data from Google Sheets
def load_data_from_sheets():
    gc = authenticate_google_sheets()
    sheet = gc.open(SHEET_NAME).sheet1  # Assuming data is in the first sheet

    # Fetch all records and headers
    data = sheet.get_all_records()
    headers = sheet.row_values(1)
    # If there's no data, initialize with headers
    if not data:  # No data found
        data = pd.DataFrame(columns=headers)  # Create an empty DataFrame with headers
    else:
        data = pd.DataFrame(data)
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')

        for col in data.columns:
            if col not in ['Date', 'Comments']:
                data[col] = pd.to_numeric(data[col], errors='coerce', downcast='float')

    return data, headers





def backup_google_sheet(spreadsheet, original_sheet):
    data = original_sheet.get_all_values()
    try:
        backup_sheet = spreadsheet.worksheet(BACKUP_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        # If the backup sheet doesn't exist, create it
        backup_sheet = spreadsheet.add_worksheet(title=BACKUP_SHEET_NAME, rows=original_sheet.row_count,
                                                 cols=original_sheet.col_count)

    # Clear the backup sheet and update with current data
    backup_sheet.clear()
    backup_sheet.update(data, "A1")



def save_data_to_sheets(data):
    gc = authenticate_google_sheets()
    spreadsheet = gc.open(SHEET_NAME)
    sheet = spreadsheet.sheet1

    backup_google_sheet(spreadsheet, sheet)
    sheet.clear()
    data = data.copy()
    data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
    sheet.update([data.columns.values.tolist()] + data.values.tolist())

def adjust_later_data(selected_date, category, selected_option, payment_option, amount):
    data_to_adjust = st.session_state.data[st.session_state.data['Date'] > selected_date]

    if category == "Money Management":
        if selected_option == 'Income':
            data_to_adjust['Credit'] += amount
        elif selected_option == 'CC Payment':
            data_to_adjust['Credit'] -= amount
            data_to_adjust['CC Debt'] -= amount
    elif category == "Expense":
        if payment_option == 'Credit Card':
            data_to_adjust['CC Debt'] += amount
        elif payment_option == 'Debit Card':
            data_to_adjust['Credit'] -= amount

    st.session_state.data.update(data_to_adjust)

# Initialize or update row in DataFrame
def initialize_new_row(date):
    if not st.session_state.data.empty:
        latest_data = st.session_state.data.iloc[-1]
    else:
        latest_data = None

    expense_options = [cat for cat in st.session_state.headers if cat not in NOT_EXPENSE_OPTIONS]
    new_row = {col: float(0) for col in expense_options}

    if latest_data is not None:
        new_row.update({'Date': date, 'Income': float(0), 'CC Payment': float(0),
                        'Credit': latest_data['Credit'], 'CC Debt': latest_data['CC Debt'], 'Comments': ''})
    else:
        new_row.update({'Date': date, 'Income': float(0), 'CC Payment': float(0),
                        'Credit': float(0), 'CC Debt': float(0), 'Comments': ''})

    new_row_df = pd.DataFrame([new_row])

    st.session_state.data = pd.concat([st.session_state.data, new_row_df], ignore_index=True)


# Streamlit UI
if 'data' not in st.session_state:
    st.session_state.data,  st.session_state.headers = load_data_from_sheets()

if st.session_state.data.empty:
    st.warning("Google Sheets is empty.")

if 'changes_made' not in st.session_state:
    st.session_state.changes_made = False

# Main app content starts here
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.title("Welcome, Gaurang!")

if st.session_state.data.empty:
    st.markdown("### No data available yet.")
else:
    # Display Credit and CC Debt
    latest_data = st.session_state.data.iloc[-1]
    st.markdown(f"### Credit: ${latest_data['Credit']:.2f}")
    st.markdown(f"### CC debt: ${latest_data['CC Debt']:.2f}")

# Select date
selected_date = st.date_input("Select date", datetime.now())
selected_date = pd.to_datetime(selected_date)

# Choose category
category = st.selectbox("Select category", ["Money Management", "Expenses"])
expense_options = [cat for cat in st.session_state.headers if cat not in NOT_EXPENSE_OPTIONS]

# Input fields for category selection
if category == "Money Management":
    selected_option = st.selectbox("Select section", ['Income', 'CC Payment'])
    payment_option = None
elif category == "Expenses":
    selected_option = st.selectbox("Select section", expense_options)
    payment_option = st.selectbox("Select payment option", PAYMENT_METHOD_OPTIONS)

amount = st.number_input("Enter amount",min_value=0.0, format="%.2f")
comment = st.text_input("Enter a comment", "")

if st.button("Add Record"):
    if selected_date not in st.session_state.data['Date'].values:
        initialize_new_row(selected_date)

    if category == "Money Management":
        if selected_option == 'Income':
            st.session_state.data.loc[st.session_state.data['Date'] == selected_date, 'Credit'] += amount
        elif selected_option == 'CC Payment':
            st.session_state.data.loc[st.session_state.data['Date'] == selected_date, 'Credit'] -= amount
            st.session_state.data.loc[st.session_state.data['Date'] == selected_date, 'CC Debt'] -= amount

    if category == "Expenses":
        if payment_option == 'Credit Card':
            st.session_state.data.loc[st.session_state.data['Date'] == selected_date, 'CC Debt'] += amount
        elif payment_option == 'Debit Card':
            st.session_state.data.loc[st.session_state.data['Date'] == selected_date, 'Credit'] -= amount

    st.session_state.data.loc[st.session_state.data['Date'] == selected_date, selected_option] += amount

    if comment:
        existing_comment = st.session_state.data.loc[st.session_state.data['Date'] == selected_date, 'Comments'].values
        new_comment = f"{existing_comment[0]}, {comment}" if existing_comment[0] != "" else comment
        st.session_state.data.loc[st.session_state.data['Date'] == selected_date, 'Comments'] = new_comment

    if selected_date < pd.to_datetime(datetime.now().date()):
        adjust_later_data(selected_date, category, selected_option, payment_option, amount)

    st.session_state.changes_made = True

# Save data to Google Sheets
if st.session_state.changes_made and st.button("Save changes"):
    save_data_to_sheets(st.session_state.data)
    st.session_state.changes_made = False
    st.success("Changes saved successfully!")

