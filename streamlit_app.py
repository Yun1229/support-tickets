import datetime
import random
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import hashlib
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
import json
from streamlit_gsheets import GSheetsConnection


# Show app title and description.
st.set_page_config(page_title="Fang's Marine Corporation", page_icon="🎫")
st.title("Fang's Marine Corporation")
st.write(
    """
    This app shows how you can build an internal tool in Streamlit. Here, we are
    implementing a support ticket workflow. The user can create a ticket, edit
    existing tickets, and view some statistics.
    """
)

# Security utilities


def make_hashes(password):
    return hashlib.sha256(password.encode()).hexdigest()


def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text


conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read()
# Print results.
for row in df.itertuples():
    st.write(f"{row.user} has a :{row.password}:")


# Save the dataframe in session state (a dictionary-like object that persists across
# page runs). This ensures our data is persisted when the app updates.
st.session_state.df = df

# User Dashboard


def user_dashboard(username):
    st.subheader(f"{username}'s Dashboard")
    st.write("View and add your items here.")

    # Display user's items
    user_items = [item for item in user_db["items"]
                  if item["owner"] == username]
    df = pd.DataFrame(user_items)
    if not df.empty:
        st.table(df)
    else:
        st.write("No items yet.")

        # Add new items
    item_name = st.text_input("Item Name")
    item_quantity = st.number_input("Quantity", min_value=1, value=1)
    if st.button("Add Item"):
        new_item = {"name": item_name, "quantity": item_quantity,
                    "status": "ordered", "owner": username}
        user_db["items"].append(new_item)
        st.success(f"Item {item_name} added successfully!")

# Admin Dashboard


def admin_dashboard():
    st.subheader("Admin Dashboard")
    st.write("View and modify the status of all items.")

    # Display all items
    if user_db["items"]:
        df = pd.DataFrame(user_db["items"])
        st.table(df)
    else:
        st.write("No items in the system.")

    # Modify item status
    item_index = st.number_input(
        "Item Index to modify", min_value=0, max_value=len(user_db["items"]) - 1)
    new_status = st.selectbox("New Status", ["ordered", "received", "paid"])
    if st.button("Update Status"):
        user_db["items"][item_index]["status"] = new_status
        st.success(f"Item status updated to {new_status}!")


# Mock user database
user_db = {
    "users": [
        {"username": "user1", "password": make_hashes(
            "user1_password"), "role": "user"},
        {"username": "user2", "password": make_hashes(
            "user2_password"), "role": "user"},
        {"username": "admin", "password": make_hashes(
            "admin_password"), "role": "admin"}
    ],
    "items": []  # Stores item details with statuses and owners
}


# Create a random Pandas dataframe with existing tickets.
if "df" not in st.session_state:

    # Set seed for reproducibility.
    np.random.seed(42)

    # Make up some fake issue descriptions.
    issue_descriptions = [
        "Network connectivity issues in the office",
        "Software application crashing on startup",
        "Printer not responding to print commands",
        "Email server downtime",
        "Data backup failure",
        "Login authentication problems",
        "Website performance degradation",
        "Security vulnerability identified",
        "Hardware malfunction in the server room",
        "Employee unable to access shared files",
        "Database connection failure",
        "Mobile application not syncing data",
        "VoIP phone system issues",
        "VPN connection problems for remote employees",
        "System updates causing compatibility issues",
        "File server running out of storage space",
        "Intrusion detection system alerts",
        "Inventory management system errors",
        "Customer data not loading in CRM",
        "Collaboration tool not sending notifications",
    ]

    # Generate the dataframe with 100 rows/tickets.
    data = {
        "ID": [f"TICKET-{i}" for i in range(1100, 1000, -1)],
        "Issue": np.random.choice(issue_descriptions, size=100),
        "Status": np.random.choice(["Open", "In Progress", "Closed"], size=100),
        "Priority": np.random.choice(["High", "Medium", "Low"], size=100),
        "Date Submitted": [
            datetime.date(2023, 6, 1) +
            datetime.timedelta(days=random.randint(0, 182))
            for _ in range(100)
        ],
    }
    df = pd.DataFrame(data)

    # Save the dataframe in session state (a dictionary-like object that persists across
    # page runs). This ensures our data is persisted when the app updates.
    st.session_state.df = df


# Show a section to add a new ticket.
st.header("User login")
st.write("DB username:", st.secrets["db_username"])
st.write("DB password:", st.secrets["db_password"])

# We're adding tickets via an `st.form` and some input widgets. If widgets are used
# in a form, the app will only rerun once the submit button is pressed.
with st.form("login_form"):
    # Login or Register
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        # run_seq(uri, username, password, database,10)
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        login = st.form_submit_button("Login")

    with tab2:
        # run_str(uri, username, password, database,50)
        username = st.text_input("New Username")
        password = st.text_input("New Password", type='password')
        register = st.form_submit_button("Register")


if login:

    user = next(
        (u for u in user_db["users"] if u["username"] == username), None)

    if user and check_hashes(password, user['password']):
        st.success("Logged in successfully!")
        st.success(f"Hello {user['username']}!")

        with st.form("add_ticket_form"):
            if user['role'] == 'user':
                user_dashboard(username)
            elif user['role'] == 'admin':
                admin_dashboard()
    else:
        st.error("Invalid username or password")

if register:
    if next((u for u in user_db["users"] if u["username"] == username), None):
        st.error("Username already exists. Please choose a different username.")
    else:
        hashed_password = make_hashes(password)
        user_db["users"].append(
            {"username": username, "password": hashed_password, "role": "user"})
        st.success("Registered successfully! You can now login.")

    # Show section to view and edit existing tickets in a table.
st.header("Ordered items")
st.write(f"Number of tickets: `{len(st.session_state.df)}`")

st.info(
    "You can edit the tickets by double clicking on a cell. Note how the plots below "
    "update automatically! You can also sort the table by clicking on the column headers.",
    icon="✍️",
)

# Show the tickets dataframe with `st.data_editor`. This lets the user edit the table
# cells. The edited data is returned as a new dataframe.
edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Ticket status",
            options=["Open", "In Progress", "Closed"],
            required=True,
        ),
        "Priority": st.column_config.SelectboxColumn(
            "Priority",
            help="Priority",
            options=["High", "Medium", "Low"],
            required=True,
        ),
    },
    # Disable editing the ID and Date Submitted columns.
    disabled=["ID", "Date Submitted"],
)

# Show some metrics and charts about the ticket.
st.header("Statistics")

# Show metrics side by side using `st.columns` and `st.metric`.
col1, col2, col3 = st.columns(3)
num_open_tickets = len(
    st.session_state.df[st.session_state.df.Status == "Open"])
col1.metric(label="Number of open tickets", value=num_open_tickets, delta=10)
col2.metric(label="First response time (hours)", value=5.2, delta=-1.5)
col3.metric(label="Average resolution time (hours)", value=16, delta=2)

# Show two Altair charts using `st.altair_chart`.
st.write("")
st.write("##### Ticket status per month")
status_plot = (
    alt.Chart(edited_df)
    .mark_bar()
    .encode(
        x="month(Date Submitted):O",
        y="count():Q",
        xOffset="Status:N",
        color="Status:N",
    )
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

st.write("##### Current ticket priorities")
priority_plot = (
    alt.Chart(edited_df)
    .mark_arc()
    .encode(theta="count():Q", color="Priority:N")
    .properties(height=300)
    .configure_legend(
        orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    )
)
st.altair_chart(priority_plot, use_container_width=True, theme="streamlit")
