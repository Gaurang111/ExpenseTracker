# Expense Tracker

A private, passcode-protected personal finance app. It records income and spending in a Google Sheet and gives you live charts, all from a Streamlit interface.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-FF4B4B)
![Google Sheets](https://img.shields.io/badge/storage-Google%20Sheets-34A853?logo=googlesheets&logoColor=white)

---

## Overview

Spreadsheets are great for storing expenses and awkward for entering them on a phone. This app puts a simple entry form on top of a Google Sheet. You add a record in a few taps, and the app keeps your running balances correct and charts your spending.

## Features

- **Quick entry:** pick a date, a category, a payment method and an amount, and add an optional comment.
- **Running balances:** your available **Credit** and **credit-card debt** are updated with every record.
  - Income increases your balance.
  - Debit-card spending reduces your balance.
  - Credit-card spending increases card debt.
  - A card payment reduces both balance and debt.
- **Back-dated entries:** adding a record for a past date automatically adjusts the balances of every later day.
- **Interactive charts:** a grouped bar chart (Plotly) of spending by category, with Weekly, Monthly and Yearly views and a category filter.
- **Google Sheets as the database:** your data stays in a sheet you own and can open any time.
- **Automatic backup:** every save first copies the current sheet to an `Expense_backup` worksheet.
- **Passcode gate:** the app is locked until the correct passcode is entered.

## How it works

```
Streamlit UI  <-->  pandas DataFrame (session state)  <-->  Google Sheets (gspread)
                                                              |
                                                              +-- Expenses        (live data)
                                                              +-- Expense_backup  (previous version)
```

On start-up the sheet is loaded into a DataFrame. Edits happen in memory, and **Save changes** writes them back, after taking the backup.

## Getting started

### 1. Prepare the Google Sheet

1. Create a Google Sheet named **Expenses**.
2. Use these columns: `Date`, one column per expense category, `Income`, `Credit`, `CC Debt`, `CC Payment`, `Comments`.
3. In the Google Cloud console, create a **service account**, enable the Google Sheets and Drive APIs, and download its JSON key.
4. Share the sheet with the service account's email address (Editor access).

### 2. Install

```bash
git clone https://github.com/Gaurang111/ExpenseTracter.git
cd ExpenseTracter

python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure secrets

Create a `.env` file (it is git-ignored):

```env
PASSCODE=choose-a-passcode
GOOGLE_CRED=<base64-encoded service account JSON>
```

Encode the key file with:

```bash
# macOS / Linux
base64 -w0 cred.json

# Windows PowerShell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("cred.json"))
```

When deploying to Streamlit Cloud, set `DEV = False` in `main.py` and add `passcode` and `google_cred` to the app's secrets instead.

### 4. Run

```bash
streamlit run main.py
```

## Project structure

```
ExpenseTracter/
├── main.py            # Streamlit app: login, entry form, balances, charts
├── GoogleConnect.py   # Standalone script to test the Google Sheets connection
├── data/              # Local spreadsheet templates (not tracked)
└── requirements.txt
```

## Security notes

- Never commit `cred.json` or `.env`. Both are listed in `.gitignore`.
- The passcode is a light access gate for a personal tool, not a full authentication system.

## Tech stack

Python, Streamlit, pandas, Plotly, gspread, oauth2client.
