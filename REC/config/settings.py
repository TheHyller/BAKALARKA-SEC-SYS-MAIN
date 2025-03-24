import json
import os

# Default settings
DEFAULT_SETTINGS = {
    "pin_code": "1234",
    "system_active": False,
    "network": {
        "tcp_port": 8080,
        "udp_port": 8081,
        "discovery_port": 8082
    },
    "sensors": []
}

# Path to the settings file
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

# Global settings variable
settings = {}

def load_settings():
    """Load settings from file or create with defaults if file doesn't exist"""
    global settings
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            print(f"DEBUG: Settings loaded from {SETTINGS_FILE}")
        else:
            settings = DEFAULT_SETTINGS.copy()
            save_settings()
            print(f"DEBUG: Created default settings file at {SETTINGS_FILE}")
        return settings
    except Exception as e:
        print(f"ERROR: Failed to load settings: {e}")
        settings = DEFAULT_SETTINGS.copy()
        return settings

def save_settings():
    """Save current settings to file"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        print(f"DEBUG: Settings saved to {SETTINGS_FILE}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to save settings: {e}")
        return False

def get_setting(key, default=None):
    """Get a specific setting by key"""
    return settings.get(key, default)

def update_setting(key, value):
    """Update a specific setting and save to file"""
    settings[key] = value
    return save_settings()

def validate_pin(pin_input):
    """Validate if provided PIN matches stored PIN"""
    stored_pin = settings.get("pin_code", DEFAULT_SETTINGS["pin_code"])
    return pin_input == stored_pin

def update_pin(new_pin):
    """Update the PIN code"""
    if len(new_pin) >= 4:
        return update_setting("pin_code", new_pin)
    return False

def toggle_system_state(new_state=None):
    """Toggle or set the system state (active/inactive)"""
    if new_state is None:
        new_state = not settings.get("system_active", DEFAULT_SETTINGS["system_active"])
    return update_setting("system_active", new_state)

def get_sensor_devices():
    """Get list of known sensor devices"""
    return settings.get("sensor_devices", {})

def add_sensor_device(device_id, device_data):
    """Add or update a sensor device"""
    if "sensor_devices" not in settings:
        settings["sensor_devices"] = {}
    
    # Update or add the device
    settings["sensor_devices"][device_id] = device_data
    return save_settings()

def remove_sensor_device(device_id):
    """Remove a sensor device"""
    if "sensor_devices" in settings and device_id in settings["sensor_devices"]:
        del settings["sensor_devices"][device_id]
        return save_settings()
    return False

def get_sensor_status():
    """Get current status of all sensor devices"""
    return settings.get("sensor_status", {})

def update_sensor_status(device_id, sensor_type, status, timestamp=None):
    """Update the status of a sensor"""
    if "sensor_status" not in settings:
        settings["sensor_status"] = {}
    
    if device_id not in settings["sensor_status"]:
        settings["sensor_status"][device_id] = {}
    
    # Update status with timestamp
    if timestamp is None:
        import time
        timestamp = time.time()
        
    settings["sensor_status"][device_id][sensor_type] = {
        "status": status,
        "timestamp": timestamp
    }
    
    return save_settings()