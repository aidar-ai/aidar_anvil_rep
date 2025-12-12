from ._anvil_designer import HomeTemplate
from anvil import *
import stripe.checkout
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import json
from datetime import datetime
from anvil_labs.non_blocking import call_async
import time
import uuid

from anvil_extras import routing
from ..nav import (
    click_link,
    click_button,
    click_box,
    logout,
    login_check,
    load_var,
    save_var,
)

from ..C_Home_Agents import C_Home_Agents
from ..C_Home_NextUp import C_Home_NextUp
from ..C_Home_Hot import C_Home_Hot
from ..C_Short import C_Short
from ..C_TrialLimitationsPopup import C_TrialLimitationsPopup


@routing.route("", title="Home")
@routing.route("home", title="Home")
class Home(HomeTemplate):
    # Class variable to track the current active instance
    _active_instance = None
    _last_init_time = 0
    _min_time_between_inits = 0.5  # seconds

    def __init__(self, **properties):
        # Generate a unique instance ID
        self.instance_id = str(uuid.uuid4())[:8]

        # Print detailed diagnostics
        route_hash = anvil.js.window.location.hash
        current_time = time.time()

        # Always set this as the active instance so callbacks update the correct UI
        Home._active_instance = self

        # Check if this is a duplicate initialization within the threshold period
        time_since_last_init = current_time - Home._last_init_time

        global user
        user = anvil.users.get_user()

        if time_since_last_init < Home._min_time_between_inits:
            self.init_components(**properties)

            # Still need to handle possible UI setup for this instance
            self.colpan_wl_selection.visible = False
            self.no_watchlists.visible = False
            self.no_shorts.visible = False
            self.reload.visible = False

            user = anvil.users.get_user()
            name = (
                user["first_name"].upper()
                if user["first_name"] is not None
                else ""
            )
            self.welcome.content = f"""
      <span style="font-family: 'General Sans', sans-serif; font-weight: 600; font-size: 55px; color: white;">
        <span style="color: #FF4C2B;">.</span>WELCOME <span style="color: #FF4C2B;">{name}</span>
      </span>
      """

            return

        # Update the last initialization time
        Home._last_init_time = current_time

        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        if user is None or user == "None":
            self.visible = False

        elif (
            user["expiration_date"] is not None
            and (datetime.today().date() - user["expiration_date"]).days > 0
        ):
            routing.set_url_hash(
                "settings?section=Subscription", load_from_cache=False
            )
            get_open_form().SearchBar.visible = False

        else:
            model_id = load_var("model_id")
            self.model_id = model_id

            self.num_shorts = 0

            # -------------
            # 1. INITIALIZE ASYNCHRONOUS LOADING
            # 1.1 Hide "no data" messages during loading
            self.colpan_wl_selection.visible = False
            self.no_watchlists.visible = False
            self.no_shorts.visible = False
            self.reload.visible = False

            # 1.2 welcome name
            name = (
                user["first_name"].upper()
                if user["first_name"] is not None
                else ""
            )
            self.welcome.content = f"""
      <span style="font-family: 'General Sans', sans-serif; font-weight: 600; font-size: 55px; color: white;">
        <span style="color: rgb(253, 101, 45);">.</span>WELCOME <span style="color: rgb(253, 101, 45);">{name}</span>
      </span>
      """

            # 1.3 Initialize loading of agents asynchronously
            self.agents_start_time = time.time()
            # Initialize the Agents component with no data to show loading state immediately
            self.agents_component = C_Home_Agents(data=None)
            self.sec_agents.add_component(self.agents_component)
            self.load_agents_async()

            # # 1.4 Initialize loading of next asynchronously
            # self.next_start_time = time.time()
            # # Initialize the Next component with no data to show loading state immediately
            # self.next_component = C_Home_NextUp(data=None)
            # self.sec_next.add_component(self.next_component)
            # self.load_next_async()

            # 1.5 Initialize loading of hot asynchronously
            self.hot_start_time = time.time()
            # Initialize the Hot component with no data to show loading state immediately
            self.hot_component = C_Home_Hot(data=None)
            self.sec_hot.add_component(self.hot_component)
            self.load_hot_async()

            # 1.6 Initialize loading of shorts asynchronously
            self.shorts_start_time = time.time()
            self.load_shorts_async()

            # TRIAL NOTIFICATION
            if (
                user["plan"] in ["Trial", "Extended Trial"]
                and load_var("initial_login") == "true"
            ):
                usage_data = anvil.server.call(
                    "get_ratings_count", user["user_id"]
                )

                # Get latest max_trial_ratings from server
                max_trial_ratings = anvil.server.call(
                    "get_max_trial_ratings", user["user_id"]
                )

                print("total_count:", usage_data["total_count"])
                print("today_count:", usage_data["today_count"])
                print("max_trial_ratings:", max_trial_ratings)

                alert(
                    content=C_TrialLimitationsPopup(
                        usage_data["total_count"],
                        usage_data["today_count"],
                        max_trial_ratings,
                    ),
                    large=True,
                    buttons=[],
                )
            save_var("initial_login", False)

    # ------
    # 2. ASYNC METHODS
    # 2.1 AGENTS METHODS
    def load_agents_async(self):
        """Starts asynchronous loading of agents data"""
        async_call = call_async("get_home_agents", user["user_id"])
        async_call.on_result(self.agents_loaded)

    def agents_loaded(self, data):
        """Handles successful server response for agents."""
        # Calculate loading time
        load_time = time.time() - self.agents_start_time

        # Get the active instance - this is the one currently visible to the user
        active_instance = Home._active_instance

        # Check if we should update the current instance or the active instance
        if active_instance and active_instance.instance_id != self.instance_id:
            active_instance.process_agents_data(data)
        else:
            self.process_agents_data(data)

    def process_agents_data(self, data):
        """
        Process and display agents data

        Parameters:
            data (str): JSON string containing agents data
        """
        data = json.loads(data)

        # Check if we already have an agents component to update
        if hasattr(self, "agents_component") and self.agents_component:
            # Update the existing component with new data
            self.agents_component.update_data(data)
        else:
            # Fallback if component doesn't exist yet
            self.agents_component = C_Home_Agents(data=data)
            self.sec_agents.add_component(self.agents_component)

    # # ------
    # # 2.2 NEXT METHODS
    # def load_next_async(self):
    #   """Starts asynchronous loading of next data"""
    #   async_call = call_async("get_home_next", user["user_id"])
    #   async_call.on_result(self.next_loaded)

    # def next_loaded(self, data):
    #   """Handles successful server response for next."""
    #   # Calculate loading time
    #   load_time = time.time() - self.next_start_time

    #   # Get the active instance - this is the one currently visible to the user
    #   active_instance = Home._active_instance

    #   # Check if we should update the current instance or the active instance
    #   if active_instance and active_instance.instance_id != self.instance_id:
    #     active_instance.process_next_data(data)
    #   else:
    #     self.process_next_data(data)

    # def process_next_data(self, data):
    #   """
    #   Process and display next data

    #   Parameters:
    #       data (str): JSON string containing next data
    #   """
    #   data = json.loads(data)

    #   # Check if we already have a next component to update
    #   if hasattr(self, 'next_component') and self.next_component:
    #     # Update the existing component with new data
    #     self.next_component.update_data(data)
    #   else:
    #     # Fallback if component doesn't exist yet
    #     self.next_component = C_Home_NextUp(data=data)
    #     self.sec_next.add_component(self.next_component)

    # ------
    # 2.3 HOT METHODS
    def load_hot_async(self):
        """Starts asynchronous loading of hot data"""
        async_call = call_async("get_home_hot", user["user_id"])
        async_call.on_result(self.hot_loaded)

    def hot_loaded(self, data):
        """Handles successful server response for hot."""
        # Get the active instance - this is the one currently visible to the user
        active_instance = Home._active_instance

        # Check if we should update the current instance or the active instance
        if active_instance and active_instance.instance_id != self.instance_id:
            active_instance.process_hot_data(data)
        else:
            self.process_hot_data(data)

    def process_hot_data(self, data):
        """
        Process and display hot data

        Parameters:
            data (str): JSON string containing hot data
        """
        data = json.loads(data)

        # Check if we already have a hot component to update
        if hasattr(self, "hot_component") and self.hot_component:
            # Update the existing component with new data
            self.hot_component.update_data(data)
        else:
            # Fallback if component doesn't exist yet
            self.hot_component = C_Home_Hot(data=data)
            self.sec_hot.add_component(self.hot_component)

    # ------
    # 2.4 SHORTS METHODS
    def load_shorts_async(self, selected_wl_ids=None):
        """
        Starts asynchronous loading of shorts data
        """
        # Call asynchronously
        async_call = call_async(
            "get_home_shorts", user["user_id"], selected_wl_ids
        )
        async_call.on_result(self.shorts_loaded)

    def shorts_loaded(self, result):
        """Handles successful server response for shorts."""
        # Get the active instance - this is the one currently visible to the user
        active_instance = Home._active_instance

        # Check if we should update the current instance or the active instance
        if active_instance and active_instance.instance_id != self.instance_id:
            active_wl_ids = active_instance.setup_watchlists(
                result["watchlists"]
            )
            active_instance.process_shorts(result["shorts"])
        else:
            active_wl_ids = self.setup_watchlists(result["watchlists"])
            self.process_shorts(result["shorts"])

    def setup_watchlists(self, watchlists):
        """Set up watchlist UI components"""
        # Save current selection state before clearing the panel
        current_states = {}
        for component in self.flow_panel_watchlists.get_components():
            if isinstance(component, Link):
                # Save the active/inactive state of each watchlist
                current_states[str(component.tag)] = component.role

        # Clear existing components
        self.flow_panel_watchlists.clear()

        if watchlists is not None and len(watchlists) > 0:
            self.no_watchlists.visible = False
            self.reload.visible = False

            active_wl_ids = []

            for i in range(0, len(watchlists)):
                wl_id = watchlists[i]["watchlist_id"]
                wl_id_str = str(wl_id)

                # Determine role based on previous state
                role = current_states.get(wl_id_str, "genre-box")

                # Create the link with the appropriate role
                wl_link = Link(
                    text=watchlists[i]["watchlist_name"], tag=wl_id, role=role
                )

                wl_link.set_event_handler(
                    "click", self.create_activate_watchlist_handler(wl_id)
                )
                self.flow_panel_watchlists.add_component(wl_link)

                # Add to active list if it's active
                if role == "genre-box":
                    active_wl_ids.append(wl_id)

        else:
            # No watchlists found - show message
            self.no_watchlists.visible = True
            self.no_shorts.visible = False
            self.reload.visible = False

        return active_wl_ids

    def process_shorts(self, shorts):
        """Process and display shorts data"""
        self.flow_panel_shorts.clear()
        self.num_shorts = 0

        # Show no shorts message if there are no shorts or no active watchlists
        if shorts is None or len(shorts) == 0:
            self.no_shorts.visible = True
            self.reload.visible = False
            return

        self.no_shorts.visible = False

        # Parse and add shorts components
        shorts = json.loads(shorts)
        for i in range(0, len(shorts)):
            self.flow_panel_shorts.add_component(C_Short(data=shorts[i]))

        self.num_shorts = len(shorts)

        # Show reload button if we have enough shorts
        self.reload.visible = len(shorts) >= 9

    # ------
    # 3. USER INTERACTION METHODS
    # 3.1 NAVIGATION
    def link_discover_click(self, **event_args):
        temp_artist_id = anvil.server.call(
            "get_next_artist_id", load_var("model_id")
        )
        click_link(
            self.artist_link,
            f"agent_artists?artist_id={temp_artist_id}",
            event_args,
        )

    def button_discover_click(self, **event_args):
        temp_artist_id = anvil.server.call(
            "get_next_artist_id", load_var("model_id")
        )
        click_button(f"agent_artists?artist_id={temp_artist_id}", event_args)

    def link_funnel_click(self, **event_args):
        click_link(self.link_funnel, "funnel", event_args)

    # 3.2 SHORTS MANAGEMENT
    def add_shorts(self, **event_args):
        # get active watchlist ids
        wl_ids = []
        for component in self.flow_panel_watchlists.get_components():
            if (
                isinstance(component, Link) and component.role == "genre-box"
            ):  # Only active models
                wl_ids.append(component.tag)

        # add new shorts
        if wl_ids:
            # Call asynchronously
            async_call = call_async(
                "get_additional_shorts",
                user["user_id"],
                wl_ids,
                self.num_shorts,
                9,
            )
            async_call.on_result(self.additional_shorts_loaded)

    def additional_shorts_loaded(self, shorts):
        """Handles successful server response for additional shorts."""
        # Record the time when additional shorts are loaded
        # Get the active instance - this is the one currently visible to the user
        active_instance = Home._active_instance

        # Check if we should update the current instance or the active instance
        if active_instance and active_instance.instance_id != self.instance_id:
            active_instance.append_additional_shorts(shorts)
        else:
            self.append_additional_shorts(shorts)

    def append_additional_shorts(self, shorts):
        """Append additional shorts to the existing list"""
        # present shorts
        if shorts is not None and len(shorts) > 0:
            self.reload.visible = True
            shorts = json.loads(shorts)

            for i in range(0, len(shorts)):
                self.flow_panel_shorts.add_component(C_Short(data=shorts[i]))

            self.num_shorts = self.num_shorts + len(shorts)

            if len(shorts) < 9:
                self.reload.visible = False
        else:
            self.reload.visible = False

    # 3.3 WATCHLIST BUTTONS
    def create_activate_watchlist_handler(self, watchlist_id):
        def handler(**event_args):
            self.activate_watchlist(watchlist_id)

        return handler

    # change active status of WATCHLIST BUTTONS
    def activate_watchlist(self, watchlist_id):
        # Toggle the clicked watchlist's activation state
        for component in self.flow_panel_watchlists.get_components():
            if isinstance(component, Link):
                if int(component.tag) == watchlist_id:
                    # Toggle the role - if active make inactive, and vice versa
                    if component.role == "genre-box":
                        component.role = "genre-box-deselect"
                    else:
                        component.role = "genre-box"

        # Collect all currently active watchlist IDs (role = "genre-box")
        active_wl_ids = []
        for component in self.flow_panel_watchlists.get_components():
            if isinstance(component, Link) and component.role == "genre-box":
                active_wl_ids.append(component.tag)

        # Reset start time for reloading shorts
        self.shorts_start_time = time.time()
        print(
            f"HOME ASYNC [{self.instance_id}] - Shorts reloading with active watchlist IDs: {active_wl_ids}",
            flush=True,
        )

        # Clear existing shorts
        self.flow_panel_shorts.clear()
        self.no_shorts.visible = False

        # Load shorts with only the active watchlist IDs
        self.load_shorts_async(selected_wl_ids=active_wl_ids)

    def button_news_selection_click(self, **event_args):
        # if self.colpan_wl_selection.visible is True:
        #   self.colpan_wl_selection.visible = False
        # else:
        #   self.colpan_wl_selection.visible = True
        pass
