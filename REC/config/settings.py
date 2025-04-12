import json
import os

# Predvolené nastavenia
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

# Cesta k súboru nastavení
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

# Globálna premenná nastavení
settings = {}

def load_settings():
    """Načíta nastavenia zo súboru alebo vytvorí predvolené nastavenia, ak súbor neexistuje"""
    global settings
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            print(f"DEBUG: Nastavenia načítané z {SETTINGS_FILE}")
        else:
            settings = DEFAULT_SETTINGS.copy()
            save_settings()
            print(f"DEBUG: Vytvorený predvolený súbor nastavení v {SETTINGS_FILE}")
        return settings
    except Exception as e:
        print(f"ERROR: Zlyhalo načítanie nastavení: {e}")
        settings = DEFAULT_SETTINGS.copy()
        return settings

def save_settings():
    """Uloží aktuálne nastavenia do súboru"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        print(f"DEBUG: Nastavenia uložené do {SETTINGS_FILE}")
        return True
    except Exception as e:
        print(f"ERROR: Zlyhalo uloženie nastavení: {e}")
        return False

def get_setting(key, default=None):
    """Získa konkrétne nastavenie podľa kľúča"""
    return settings.get(key, default)

def update_setting(key, value):
    """Aktualizuje konkrétne nastavenie a uloží do súboru"""
    settings[key] = value
    return save_settings()

def validate_pin(pin_input):
    """Overí, či zadaný PIN zodpovedá uloženému PIN-u"""
    stored_pin = settings.get("pin_code", DEFAULT_SETTINGS["pin_code"])
    return pin_input == stored_pin

def update_pin(new_pin):
    """Aktualizuje PIN kód"""
    if len(new_pin) >= 4:
        return update_setting("pin_code", new_pin)
    return False

def toggle_system_state(new_state=None):
    """Prepne alebo nastaví stav systému (aktívny/neaktívny)"""
    if new_state is None:
        new_state = not settings.get("system_active", DEFAULT_SETTINGS["system_active"])
    return update_setting("system_active", new_state)

def get_sensor_devices():
    """Získa zoznam známych zariadení senzorov"""
    return settings.get("sensor_devices", {})

def add_sensor_device(device_id, device_data):
    """Pridá alebo aktualizuje zariadenie senzora"""
    if "sensor_devices" not in settings:
        settings["sensor_devices"] = {}
    
    # Aktualizuje alebo pridá zariadenie
    settings["sensor_devices"][device_id] = device_data
    return save_settings()

def remove_sensor_device(device_id):
    """Odstráni zariadenie senzora"""
    if "sensor_devices" in settings and device_id in settings["sensor_devices"]:
        del settings["sensor_devices"][device_id]
        return save_settings()
    return False

def get_sensor_status():
    """Získa aktuálny stav všetkých zariadení senzorov"""
    return settings.get("sensor_status", {})

def update_sensor_status(device_id, sensor_type, status, timestamp=None):
    """Aktualizuje stav senzora"""
    if "sensor_status" not in settings:
        settings["sensor_status"] = {}
    
    if device_id not in settings["sensor_status"]:
        settings["sensor_status"][device_id] = {}
    
    # Aktualizuje stav s časovou pečiatkou
    if timestamp is None:
        import time
        timestamp = time.time()
        
    settings["sensor_status"][device_id][sensor_type] = {
        "status": status,
        "timestamp": timestamp
    }
    
    return save_settings()