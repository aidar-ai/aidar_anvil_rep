from ._anvil_designer import C_Home_HotTemplate
from anvil import *
import stripe.checkout
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import json
import anvil.js
from anvil import get_open_form
from ..nav import click_button, save_var
import time
from anvil.js.window import location


class C_Home_Hot(C_Home_HotTemplate):
    def __init__(self, data, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        global user
        user = anvil.users.get_user()

        self.data = data
        self.max_visible_rows = 6
        self.max_expanded_rows = 12  # Maximum number of rows when expanded
        self.expanded_watchlist = False
        self.expanded_notifications = False
        self.is_loading = data is None  # Track loading state

        # Filter data by source or use empty lists if data is still loading
        self.watchlist_data = []
        self.notification_data = []
        if not self.is_loading and data:
            self.watchlist_data = [
                item
                for item in self.data
                if item.get("source", "") == "watchlist"
            ]
            self.notification_data = [
                item
                for item in self.data
                if item.get("source", "") == "notification"
            ]

        # Filter data by source
        # self.watchlist_data = [item for item in self.data if item.get('source', '') == 'watchlist']
        # self.notification_data = [item for item in self.data if item.get('source', '') == 'notification']

        # 1. Register JavaScript callbacks for direct call (not promises)
        anvil.js.call_js(
            "eval",
            """
      window.pyArtistNameClicked = function(artistId) {
        console.log('[DEBUG] Artist name clicked with ID:', artistId);
        location.hash = 'agent_artists?artist_id=' + artistId;
        return true;
      }
      
      window.pyWatchlistToggleClicked = function() {
        console.log('[DEBUG] Watchlist toggle rows visibility clicked');
        window._anvilJSCallableObjects.pyWatchlistToggleClicked.call();
        return true;
      }
      
      window.pyNotificationsToggleClicked = function() {
        console.log('[DEBUG] Notifications toggle rows visibility clicked');
        window._anvilJSCallableObjects.pyNotificationsToggleClicked.call();
        return true;
      }
      
      // Function to toggle the visibility of rows in Watchlist table
      window.toggleWatchlistRowsVisibility = function(expanded) {
        console.log('[DEBUG] Toggling Watchlist rows visibility, expanded:', expanded);
        
        // Specifically target rows within the watchlist-container
        var container = document.querySelector('.watchlist-container');
        if (container) {
          var rows = container.querySelectorAll('.hot-row');
          var toggleLink = container.querySelector('.hot-toggle-link');
          
          // Show rows 7-18 when expanded, hide when collapsed
          for (var i = 7; i < rows.length; i++) {
            // If expanded, show rows up to max_expanded_rows (18)
            // If collapsed, hide all rows beyond max_visible_rows (7)
            var shouldHide = !expanded || (i >= 18);
            rows[i].classList.toggle('hidden', shouldHide);
          }
          
          if (toggleLink) {
            toggleLink.textContent = expanded ? 'show less' : 'show more';
          }
        }
      }
      
      // Function to toggle the visibility of rows in Notifications table
      window.toggleNotificationsRowsVisibility = function(expanded) {
        console.log('[DEBUG] Toggling Notifications rows visibility, expanded:', expanded);
        
        // Specifically target rows within the notifications-container
        var container = document.querySelector('.notifications-container');
        if (container) {
          var rows = container.querySelectorAll('.hot-row');
          var toggleLink = container.querySelector('.hot-toggle-link');
          
          // Show rows 7-18 when expanded, hide when collapsed
          for (var i = 7; i < rows.length; i++) {
            // If expanded, show rows up to max_expanded_rows (18)
            // If collapsed, hide all rows beyond max_visible_rows (7)
            var shouldHide = !expanded || (i >= 18);
            rows[i].classList.toggle('hidden', shouldHide);
          }
          
          if (toggleLink) {
            toggleLink.textContent = expanded ? 'show less' : 'show more';
          }
        }
      }
      """,
        )

        # Register the Python functions
        anvil.js.window.pyWatchlistToggleClicked = (
            self.handle_watchlist_toggle_click
        )
        anvil.js.window.pyNotificationsToggleClicked = (
            self.handle_notifications_toggle_click
        )

        # 2. Create tables
        self.create_hot_tables()

    def form_show(self, **event_args):
        """This method is called when the HTML panel is shown on the screen"""
        pass

    def handle_watchlist_toggle_click(self):
        """
        JavaScript callback for when the watchlist show more/show less link is clicked.
        Toggles the visibility of rows beyond the maximum visible rows, up to max_expanded_rows.

        Returns:
            bool: True indicating successful completion
        """
        print(
            f"[DEBUG] Watchlist toggle rows visibility clicked, current state: {self.expanded_watchlist}"
        )

        # Toggle expanded state
        self.expanded_watchlist = not self.expanded_watchlist

        # Call JavaScript function to toggle row visibility
        anvil.js.call_js(
            "window.toggleWatchlistRowsVisibility", self.expanded_watchlist
        )

        return True

    def handle_notifications_toggle_click(self):
        """
        JavaScript callback for when the notifications show more/show less link is clicked.
        Toggles the visibility of rows beyond the maximum visible rows, up to max_expanded_rows.

        Returns:
            bool: True indicating successful completion
        """
        print(
            f"[DEBUG] Notifications toggle rows visibility clicked, current state: {self.expanded_notifications}"
        )

        # Toggle expanded state
        self.expanded_notifications = not self.expanded_notifications

        # Call JavaScript function to toggle row visibility
        anvil.js.call_js(
            "window.toggleNotificationsRowsVisibility",
            self.expanded_notifications,
        )

        return True

    def create_hot_tables(self):
        """
        Creates both hot tables: watchlist and notifications
        """
        watchlist_html = self.generate_table_html(
            self.watchlist_data,
            "watchlist-container",
            "My Watchlists",
            self.expanded_watchlist,
            "pyWatchlistToggleClicked",
            "toggleWatchlistRowsVisibility",
        )

        # notifications_html = self.generate_table_html(
        #   self.notification_data,
        #   'notifications-container',
        #   'My Observations',
        #   self.expanded_notifications,
        #   'pyNotificationsToggleClicked',
        #   'toggleNotificationsRowsVisibility'
        # )

        # Combined HTML for both tables with spacing between
        html_content = f"""
    {watchlist_html}
    """
        # {notifications_html}

        # Initialize JavaScript for handling clicks and visibility
        js_code = (
            """
    console.log('[DEBUG] Hot tables JavaScript loaded');
    
    // Initialize row visibility for both tables
    if (window.toggleWatchlistRowsVisibility) {
      window.toggleWatchlistRowsVisibility("""
            + str(self.expanded_watchlist).lower()
            + """);
    }
    
    if (window.toggleNotificationsRowsVisibility) {
      window.toggleNotificationsRowsVisibility("""
            + str(self.expanded_notifications).lower()
            + """);
    }
    """
        )

        # Set the HTML content and evaluate the JavaScript
        self.html = html_content
        anvil.js.call_js("eval", js_code)

    def update_data(self, new_data):
        """
        Updates the component with new data and refreshes the display

        Parameters:
            new_data (list): The new data to display
        """
        self.data = new_data
        self.is_loading = False

        # Filter data by source
        self.watchlist_data = [
            item for item in self.data if item.get("source", "") == "watchlist"
        ]
        self.notification_data = [
            item
            for item in self.data
            if item.get("source", "") == "notification"
        ]

        # Recreate the tables with the new data
        self.create_hot_tables()

        return True

    def generate_table_html(
        self,
        data,
        container_class,
        header_text,
        expanded,
        toggle_function,
        visibility_function,
    ):
        """
        Generates HTML for a table with the given parameters

        Parameters:
            data (list): List of artist data to display
            container_class (str): CSS class for the container
            header_text (str): Text to display in the header
            expanded (bool): Whether the table is expanded
            toggle_function (str): JavaScript function name for toggle clicks
            visibility_function (str): JavaScript function name for visibility toggle

        Returns:
            str: HTML content for the table
        """
        # 1. Create the main container HTML with the header
        html_content = f"""
    <div class="hot-container {container_class}">
      <!-- <div class="hot-header">
        <h3>{header_text}</h3>
      </div> -->
      <table class="hot-table">
        <tbody>
    """

        # 2. Check if data is loading or empty and display appropriate message
        if self.is_loading:
            # Loading state message
            html_content += f"""
        <tr class="hot-row hot-status-row">
          <td colspan="4" class="hot-status-cell">
            <div class="hot-status-message hot-loading-message">Loading artists...</div>
          </td>
        </tr>
      """
        elif not data:
            # No data message
            html_content += f"""
        <tr class="hot-row hot-status-row">
          <td colspan="4" class="hot-status-cell">
            <div class="hot-status-message hot-empty-message">No artists available</div>
          </td>
        </tr>
      """
        else:
            # 3. Generate table rows for each artist
            for i, item in enumerate(data):
                artist_id = item.get("artist_id", "")
                artist_name = item.get("name", "Unknown")
                artist_pic_url = item.get("artist_picture_url", "")
                list_name = item.get("list_name", "Unknown")
                metric_value = item.get("metric_value", "")  # New metric value
                metric_name = item.get("metric_name", "")  # New metric name

                # Create unique row ID
                row_id = f"hot-row-{container_class}-{i}"

                # Add 'hidden' class for rows beyond the max_visible_rows
                # If i is greater than max_visible_rows (7) and either
                # 1. We are not expanded OR
                # 2. It's beyond max_expanded_rows (18)
                hidden_class = (
                    " hidden"
                    if (
                        i >= self.max_visible_rows
                        and (not expanded or i >= self.max_expanded_rows)
                    )
                    else ""
                )

                # Add the row for this artist
                html_content += f"""
          <tr id="{row_id}" class="hot-row{hidden_class}">
            <td class="hot-pic-cell">
              <img src="{artist_pic_url}" class="hot-artist-pic" alt="{artist_name}">
            </td>
            <td class="hot-name-cell"><a href="javascript:void(0)" onclick="window.pyArtistNameClicked('{artist_id}')">{artist_name}</a></td>
            <!-- <td class="hot-watchlist-cell">on {list_name}</td> -->
            <td class="hot-release-cell">
              <div class="hot-release-box">
                <span class="hot-release-value">{metric_value}</span>
                <span class="hot-metric-name">{metric_name}</span>
              </div>
            </td>
          </tr>
        """

        # 4. Complete the HTML for the table
        html_content += """
        </tbody>
      </table>
    """

        # 5. Add the toggle link if there are more than max_visible_rows entries and not loading/empty
        if not self.is_loading and data and len(data) > self.max_visible_rows:
            toggle_text = "show less" if expanded else "show more"
            html_content += f"""
      <div class="hot-toggle-container">
        <a href="javascript:void(0)" class="hot-toggle-link" onclick="window.{toggle_function}()">{toggle_text}</a>
      </div>
      """

        # 6. Complete the container HTML
        html_content += """
    </div>
    """

        return html_content
