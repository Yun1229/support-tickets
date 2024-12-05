import os
from streamlit_gsheets import GSheetsConnection
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import hashlib
import streamlit as st
import pandas as pd
import altair as alt
import datetime
from gspread.exceptions import APIError


st.set_page_config(page_title="Fang's Marine Corporation", page_icon="🎫")
# Connect to Google Sheets
# conn = st.connection("gsheets", type=GSheetsConnection)
user_list = pd.read_csv(
    "fang_list - user_list.csv")
item_list = pd.read_csv(
    "fang_list - item_list.csv")
# st.dataframe(user_list)
st.dataframe(item_list)


@st.cache_data
def connect_api(worksheet_name):
    try:
        # worksheet = conn.read(spreadsheet="fang_list",worksheet=f"{worksheet_name}")
        worksheet = worksheet_name
        return worksheet
    except APIError as e:
        st.warning(
            'The system is too busy now. Please try again later.', icon="⚠️")
        st.warning(
            e)
        st.stop()


def update_data(new_user, new_password, contact):
    df = connect_api(user_list)

    # Add new user data to the DataFrame
    new_row = pd.DataFrame({"User": [new_user], "Password": [
                           new_password], "Contact": [contact]})
    updated_df = pd.concat([df, new_row], ignore_index=True)
    # Update the worksheet with the new DataFrame

    # conn.update(data=updated_df)
    return updated_df


def safe_int_conversion(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return " "


def itemDisplay(username, item_list):

    # item_df = pd.DataFrame(item_list)
    user_items = item_list[item_list["User"] == username]

    if not user_items.empty:
        user_items = pd.DataFrame(user_items)
        user_items = user_items.fillna(" ")
        user_items["Weight"] = user_items["Weight"].apply(
            safe_int_conversion)
        user_items["Price"] = user_items["Price"].apply(
            safe_int_conversion)
        st.dataframe(user_items.iloc[:, 1:],
                     hide_index=True, use_container_width=True)

    else:
        st.write("No items yet.")


def add_item(username):
    st.header("Add a New Item")
    st.session_state.username = username
    with st.form("add_item_form"):
        item_name = st.text_input("Item Name", key="item_name")
        page_link = st.text_input("Page Link", key="page_link")
        submitted = st.form_submit_button("Submit")
    if submitted:
        st.session_state["Submit"] = True
        st.write(username)


# Show app title and description.
st.title("Fang's Marine Corporation")


st.write("""This app shows how you can build an internal tool in Streamlit. Here, we areimplementing a support ticket workflow. The user can create a ticket, editexisting tickets, and view some statistics.""")


# Show a section to add a new ticket.


if "Login" not in st.session_state:
    st.session_state["Login"] = False
if "Submit" not in st.session_state:
    st.session_state["Submit"] = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'item_name' not in st.session_state:
    st.session_state.item_name = None
if 'page_link' not in st.session_state:
    st.session_state.page_link = None


if not st.session_state["Login"]:
    st.header("User login")
    # Display tabs only if the user is not logged in
    # Login or Register
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        st.cache_data.clear()
        user_df = connect_api(user_list)
        username = st.text_input("Username", key='username')
        password = st.text_input("Password", type='password')
        login = st.button("Login")
        if login:
            # Reload user data to get the latest changes

            user = next(
                (u for u in user_df.to_dict("records")
                 if u["User"] == username),
                None,
            )
            # user = next((u for u in user_df.to_dict("records")if u["User"] == username), None)
            if user:
                if password == user['Password']:
                    st.session_state["Login"] = True

                    st.rerun()

                else:
                    st.error("Invalid password. Please try again.")
            else:
                st.error(
                    "Username not found. Please check your username or register.")
    with tab2:
        user_df = connect_api(user_list)
        username = st.text_input("New Username")
        password = st.text_input("New Password", type='password')
        contact = st.text_input(
            "Contact information", placeholder="Can be your email, phone number or Facebook name.")
        register = st.button("Register")
        if register:
            if next((u for u in user_df.to_dict("records") if u["User"] == username), None):
                st.error(
                    "Username already exists. Please choose a different username.")
            elif username and password:
                # update_data(str(username), str(password), str(contact))
                user_list_up = update_data(
                    str(username), str(password), str(contact))
                st.success("Registered successfully! You can now login.")
                st.dataframe(user_list_up, key='user_list_up')

            else:
                st.error("Please fill in both the username and password.")
else:
    # if st.session_state["Login"]:
    st.success("Logged in successfully!")
    st.success(f"Hello {st.session_state.username}!")
    st.header("Your Items")

    item_list = connect_api(item_list)
    # item_list = conn.read(worksheet="item_list")
    itemDisplay(st.session_state.username, item_list)
    add_item(st.session_state.username)


if st.session_state["Submit"] and st.session_state.item_name:

    st.success("Item submitted!")

    item_df = connect_api(item_list)

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    new_row = pd.DataFrame(
        [
            {
                "User": st.session_state.username,
                "Item": st.session_state.item_name,
                "Link": st.session_state.page_link,
                "Date Submitted": today,
                "Status": "Ordered",
                "Weight": None,
                "Price": None,
                "Paid": None
            }
        ]
    )

    new_row = pd.DataFrame(new_row)
    new_row = new_row.fillna(" ")
    new_row["Weight"] = new_row["Weight"].apply(
        lambda x: int(x) if x != " " else " ")
    new_row["Price"] = new_row["Price"].apply(
        lambda x: int(x)if x != " "else " ")
    # st.dataframe(new_row.iloc[:, 1:],hide_index=True, use_container_width=True)

    updated_df = pd.concat([item_df, new_row], ignore_index=True)
    # st.dataframe(updated_df)
    # conn.update(worksheet="item_list", data=updated_df)

    st.success("The updated order list:")
    # st.cache_data.clear()
    # item_df = connect_api(item_list)
    # itemDisplay(st.session_state.username, item_df)

    item_df = connect_api(item_list)
    # item_list = conn.read(worksheet="item_list")
    itemDisplay(st.session_state.username, updated_df)

elif st.session_state["Submit"] and not st.session_state.item_name:
    st.error("Please enter an item name.")


_ = """

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
"""
