from ._anvil_designer import C_TrialLimitationsPopupTemplate
from anvil import *
import stripe.checkout
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import json
import anvil

from anvil_extras import routing
from ..nav import click_link, click_button, logout, save_var, load_var


class C_TrialLimitationsPopup(C_TrialLimitationsPopupTemplate):
    def __init__(
        self, total_count, today_count, max_trial_ratings=50, **properties
    ):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        global user
        user = anvil.users.get_user()

        # total_count = 51
        # today_count = 5

        # Use dynamic max_trial_ratings with fallback to 50
        warning_threshold = int(max_trial_ratings * 0.7)  # 70% warning

        # Determine which message to show
        if total_count == warning_threshold:
            # Warning at 70% of max recommendations
            html_content = self._get_warning_message(
                total_count, max_trial_ratings
            )

        elif total_count == max_trial_ratings:
            # Initial limit reached
            html_content = self._get_initial_limit_message(max_trial_ratings)

        elif total_count < max_trial_ratings:
            # Default message showing progress
            html_content = self._get_initial_progress_message(
                total_count, max_trial_ratings
            )

        elif total_count > max_trial_ratings and today_count == 0:
            # Default message showing progress
            html_content = self._get_welcome_back_message()

        elif total_count > max_trial_ratings and today_count < 5:
            # Default message showing progress
            html_content = self._get_daily_progress_message(today_count)

        elif total_count > max_trial_ratings and today_count >= 5:
            # Daily limit reached
            html_content = self._get_daily_limit_message()

        self.html = f"""
      <div class="trial-limit-popup">
        {html_content}
      </div>
      """

        # Expose close_alert method to JavaScript
        anvil.js.window.closeAlert = self._js_close_alert

    def _get_progress_bar(self, percentage, current, max_value):
        return f"""
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" style="width: {max(1, percentage)}%;"></div>
          </div>
          <div class="counter">
            <span>{current}/{max_value} recommendations used</span>
          </div>
        </div>
      """

    def _get_warning_message(self, current, max_val):
        percentage = int(current / max_val * 100)
        return f"""
        <h2>Trial Limit Approaching</h2>
        <p>You've used <strong>{current}</strong> of your initial {max_val} recommendations.</p>
        {self._get_progress_bar(percentage=percentage, current=current, max_value=max_val)}
        <p>Continue exploring<br>or upgrade for unlimited access!</p>
        <button class="pop-button-disabled" onclick="window.closeAlert()">Continue</button>
        <button class="pop-button-enabled" onclick="window.location.href='https://app.aidar.ai/#settings?section=Subscription'">Upgrade now</button>
      """

    def _get_initial_limit_message(self, max_val):
        return f"""
        <h2>Initial Trial Limit Reached</h2>
        <p>You've used all {max_val} of your initial recommendations.</p>
        {self._get_progress_bar(percentage=100, current=max_val, max_value=max_val)}      
        <p>Come back tomorrow for 5 new recommendations<br>or upgrade for unlimited access!</p>
        <button class="pop-button-enabled" onclick="window.location.href='https://app.aidar.ai/#settings?section=Subscription'">Upgrade now</button>
      """

    def _get_initial_progress_message(self, total_count, max_val):
        return f"""
      <h2>Your Trial Progress</h2>
      <p>You've used <strong>{total_count}</strong> of your initial {max_val} recommendations.</p>
      {self._get_progress_bar(percentage=int(total_count / max_val * 100), current=total_count, max_value=max_val)}
      <p>Continue exploring<br>or upgrade for unlimited access!</p>
        <button class="pop-button-disabled" onclick="window.closeAlert()">Continue</button>
        <button class="pop-button-enabled" onclick="window.location.href='https://app.aidar.ai/#settings?section=Subscription'">Upgrade now</button>
      """

    def _get_welcome_back_message(self):
        return """
        <h2>Welcome back!</h2>
        <p>You've got..</p>
        <p class="big-number">5</p>
        <p>daily recommendations left.</p>
        <button class="pop-button-disabled" onclick="window.closeAlert()">Continue</button>
        <button class="pop-button-enabled" onclick="window.location.href='https://app.aidar.ai/#settings?section=Subscription'">Upgrade now</button>
      """

    def _get_daily_progress_message(self, today_count):
        return f"""
        <h2>Your Trial Progress</h2>
        <p>You've used <strong>{today_count}</strong> of your daily 5 recommendations.</p>
        {self._get_progress_bar(percentage=int(today_count / 5 * 100), current=today_count, max_value=5)}
        <p>Continue exploring<br>or upgrade for unlimited access!</p>      
        <button class="pop-button-disabled" onclick="window.closeAlert()">Continue</button>
        <button class="pop-button-enabled" onclick="window.location.href='https://app.aidar.ai/#settings?section=Subscription'">Upgrade now</button>
      """

    def _get_daily_limit_message(self):
        return f"""
        <h2>Daily Trial Limit Reached</h2>
        <p>You've used all 5 of your daily recommendations.</p>
        {self._get_progress_bar(percentage=100, current=5, max_value=5)}
        <p>Come back tomorrow for 5 new recommendations<br>or upgrade for unlimited access!</p>
        <button class="pop-button-enabled" onclick="window.location.href='https://app.aidar.ai/#settings?section=Subscription'">Upgrade now</button>
      """

    def close_alert(self, **event_args):
        """Close the alert dialog from Python."""
        self.raise_event("x-close-alert")

    def _js_close_alert(self):
        """Close the alert dialog from JavaScript."""
        self.close_alert()
        return True
