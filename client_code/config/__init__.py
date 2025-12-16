"""
# --- 1. CLIENT CONFIGURATION MODULE ---
# Contains configuration values for client-side components.
# This module can be imported anywhere in the client-side Anvil application.
"""

import anvil.server

# --- 2. CONFIGURATION CACHE ---
# Cache for server-side configuration to avoid multiple calls
_config_cache = {}

# --- 3. WEBSOCKET CONFIGURATION ---
# Simple flag to determine which WebSocket server to use
USE_LOCAL_WEBSOCKET = False

# WebSocket server URLs
LOCAL_WEBSOCKET_URL = "ws://localhost:8000"
PROD_WEBSOCKET_URL = "wss://api.aidar.ai"

# --- 4. WEBSOCKET FUNCTIONS ---
def set_websocket_environment():
    """
    # --- 4.1 SET WEBSOCKET ENVIRONMENT ---
    Sets the appropriate WebSocket base URL in JavaScript based on current configuration.
    This should be called once at app startup.
    """
    import anvil.js
    base_url = LOCAL_WEBSOCKET_URL if USE_LOCAL_WEBSOCKET else PROD_WEBSOCKET_URL
    anvil.js.call_js('eval', f'window.WEBSOCKET_BASE_URL = "{base_url}";')
    
# Auto-initialize the WebSocket environment when this module is imported
set_websocket_environment()

# --- 5. PRICING CONFIGURATION ---
def _fetch_server_config():
    """
    # --- 3.1 FETCH SERVER CONFIG ---
    Internal function to fetch configuration from server
    and update the cache with all configuration elements.
    
    Returns:
    --------
    bool
        True if fetch was successful, False otherwise
    """
    try:
        # Fetch pricing config from server
        server_config = anvil.server.call('get_pricing_config')
        if server_config:
            # Store each config element in cache
            if 'price_values' in server_config:
                _config_cache['price_values'] = server_config['price_values']
            if 'price_ids' in server_config:
                _config_cache['price_ids'] = server_config['price_ids']
            return True
        else:
            print("[CONFIG_ERROR] Invalid configuration returned from server")
            return False
    except Exception as e:
        print(f"[CONFIG_ERROR] Error fetching configuration: {e}")
        return False

def get_price_values():
    """
    # --- 3.2 GET PRICING VALUES ---
    Fetches pricing configuration from the server.
    Uses cached values if available.
    
    Returns:
    --------
    dict
        Dictionary containing price values for all plans and frequencies
    """
    if 'price_values' not in _config_cache:
        if not _fetch_server_config():
            return {}
    
    return _config_cache['price_values']

def get_price_id(plan, frequency):
    """
    # --- 3.3 GET PRICE ID ---
    Gets the Stripe price ID for a given plan and frequency.
    
    Parameters:
    -----------
    plan : str
        The plan type ('explore' or 'professional')
    frequency : str
        The billing frequency ('monthly' or 'yearly')
    Returns:
    --------
    str
        Stripe price ID for the given plan and frequency
    """
    plan = plan.lower() if plan else ""
    frequency = frequency.lower() if frequency else ""
    
    # Ensure we have price ID data
    if 'price_ids' not in _config_cache:
        if not _fetch_server_config():
            return None
    
    price_ids = _config_cache.get('price_ids', {})
    
    # Return the price ID if available
    if plan in price_ids and frequency in price_ids.get(plan, {}):
        return price_ids[plan][frequency]
    
    return None

# --- 6. CONVENIENCE FUNCTIONS ---
def calculate_price(plan, frequency, user_count=1):
    """
    # --- 4.1 CALCULATE PRICE ---
    Calculate the price for a given plan, frequency, and user count.

    Parameters:
    -----------
    plan : str
        The plan type ('explore' or 'professional')
    frequency : str
        The billing frequency ('monthly' or 'yearly')
    user_count : int, optional
        Number of users (only relevant for professional plan)

    Returns:
    --------
    tuple
        (price_string, raw_price)
    """
    plan = plan.lower() if plan else ""
    frequency = frequency.lower() if frequency else ""
    price_values = get_price_values()

    if not price_values or plan not in price_values:
        return ("", 0)

    # Default to discounted prices for display
    if frequency == 'monthly':
        monthly_price = price_values[plan]['monthly']['discounted']
        if plan == 'professional':
            amount = monthly_price * user_count
            return (f'€{amount:.2f}/mo', amount)
        else:
            return (f'€{monthly_price:.2f}/mo', monthly_price)
    elif frequency == 'yearly':
        yearly_price = price_values[plan]['yearly']['discounted']
        if plan == 'professional':
            yearly_amount = yearly_price * 12 * user_count
            return (f'€{yearly_amount:.2f}/yr ({yearly_price:.2f}/mo/user)', yearly_amount)
        else:
            yearly_amount = yearly_price * 12
            return (f'€{yearly_amount:.2f}/yr ({yearly_price:.2f}/mo)', yearly_amount)

    return ("", 0)
