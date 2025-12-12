import anvil.stripe
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import numpy as np
from datetime import datetime, timedelta, timezone
import json


# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.


@anvil.server.callable
def sign_up_with_extra_data(
    customer_id, customer_name, email, password, first_name, last_name
):
    try:
        # Sign up the user
        user = anvil.users.signup_with_email(email, password)

        # Add user base data
        user["first_name"] = first_name
        user["last_name"] = last_name
        user["customer_name"] = customer_name
        user["welcome_email_sent"] = False

        if customer_id is not None:
            # get data
            base_data = json.loads(
                anvil.server.call("get_customer", customer_id)
            )[0]

            # customer_id
            user["customer_id"] = customer_id

            # customer_name
            name = base_data["name"] if "name" in base_data else None
            user["customer_name"] = name

            # plan
            plan = base_data["plan"] if "plan" in base_data else None
            user["plan"] = plan

            # expiration_date
            expiration_date = (
                base_data["expiration_date"]
                if "expiration_date" in base_data
                else None
            )
            if (
                expiration_date
                and expiration_date is not None
                and expiration_date != "None"
            ):
                user["expiration_date"] = datetime.strptime(
                    expiration_date, "%Y-%m-%d"
                ).date()
            else:
                user["expiration_date"] = None

            # status
            user["active"] = True
            user["admin"] = False

            print(
                f"sign_up_with_extra_data: customer_id={user['customer_id']}, customer_name={user['customer_name']}, plan={user['plan']}, expiration_date={user['expiration_date']}"
            )

        else:
            # add Trial data
            user["expiration_date"] = (
                datetime.now(timezone.utc) + timedelta(days=14)
            ).date()
            user["plan"] = "Trial"
            user["max_trial_ratings"] = 50
            user["active"] = True
            user["admin"] = True

        return "success"

    except anvil.users.UserExists:
        return "user exists"

    except Exception as e:
        print(e)
        return "other"


@anvil.server.callable
def check_user_exists(email):
    # Check if a user exists in the Users table by email
    user = app_tables.users.get(email=email)

    # Return True if user exists, otherwise return False
    return user is not None


@anvil.server.callable
def server_transfer_user_id(timezone=None):
    user = anvil.users.get_user()
    if user["user_id"] is None:
        # Pass raw IANA timezone to backend for conversion (timezone must be provided by client)
        new_user_id = anvil.server.call(
            "check_user_presence",
            user["customer_id"],
            user["email"],
            user["first_name"],
            user["last_name"],
            timezone,
        )
        if new_user_id is not None:
            user_row = app_tables.users.get(email=user["email"])
            user_row["user_id"] = new_user_id
            anvil.server.call(
                "sent_mail_first_login",
                f'{user["email"]} / {user["first_name"]} {user["last_name"]} logged in the first time for Customer ID {user["customer_id"]}',
            )


@anvil.server.callable
def update_slider_start(value):
    print(f"Slider start value: {value}")
    # You can update the graph, filter data, etc., based on this value


@anvil.server.callable
def update_slider_end(value):
    print(f"Slider end value: {value}")
    # Update your logic based on this value


@anvil.server.callable
def update_anvil_user(user_id, first_name, last_name):
    """
    Updates a user's first_name and last_name in the Anvil Users table.

    Args:
        user_id: The user ID to update
        first_name: The new first name
        last_name: The new last name

    Returns:
        'success' if the update was successful, 'error' otherwise
    """
    try:
        # Get the user row from the Users table
        user_row = app_tables.users.get(user_id=user_id)

        if user_row:
            # Update the user's information
            user_row["first_name"] = first_name
            user_row["last_name"] = last_name
            return "success"
        else:
            return "error"
    except Exception as e:
        print(f"Error updating Anvil user: {e}")
        return "error"


@anvil.server.callable
def get_agent_messages(agent_id):
    """Fetch message history for an agent"""
    messages = anvil.server.call("get_messages", agent_id)
    return messages


@anvil.server.callable
def get_anvil_users(customer_id):
    """
    1. Get all users for a given customer_id
    2. Transform the data to a format ready for client-side display

    Args:
        customer_id (str): The customer ID to filter users by

    Returns:
        list: List of dictionaries with user data formatted for display
    """
    users = list(app_tables.users.search(customer_id=customer_id))
    formatted_users = []

    for u in users:
        # Create a user dictionary with proper naming
        user_dict = {
            "user_id": u["user_id"],
            "first_name": u["first_name"],
            "last_name": u["last_name"],
            "name": f"{u['first_name']} {u['last_name']}".strip(),
            "email": u["email"],
            "customer_id": u["customer_id"],
            "customer_name": u["customer_name"],
            "plan": u["plan"],
            "expiration_date": u["expiration_date"],
            "active": u["active"],
            "admin": u["admin"],
        }
        formatted_users.append(user_dict)

    return formatted_users


@anvil.server.callable
def update_user_role(change_list):
    for change in change_list:
        user_row = app_tables.users.get(user_id=change["user_id"])
        active = True if change["active"] == "active" else False
        admin = True if change["admin"] == "yes" else False
        user_row["active"] = active
        user_row["admin"] = admin


@anvil.server.callable
def remove_user_from_customer(user_id):
    user = app_tables.users.get(user_id=user_id)
    user["customer_id"] = None
    user["customer_name"] = None
    user["plan"] = None
    user["expiration_date"] = (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).date()
    user["admin"] = True
    user["active"] = True
