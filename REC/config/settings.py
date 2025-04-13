import json
import os
import yaml
import time
from datetime import datetime, timedelta

# Predvolené nastavenia
DEFAULT_SETTINGS = {
    "pin_code": "1234",
    "system_active": False,
    "network": {
        "tcp_port": 8080,
        "udp_port": 8081,
        "discovery_port": 8082,
        "web_port": 8090
    },
    "alerts": {
        "sound_enabled": True,
        "notification_type": "Visual",
        "retention_days": 30
    },
    "images": {
        "storage_path": "captures",
        "retention_days": 14,
        "quality": "Medium"
    },
    "system": {
        "auto_start": True,
        "log_level": "INFO",
        "config_format": "JSON"
    },
    "sensors": [],
    "sensor_devices": {},
    "sensor_status": {}
}

# Cesta k súboru nastavení
SETTINGS_FILE_JSON = os.path.join(os.path.dirname(__file__), "settings.json")
SETTINGS_FILE_YAML = os.path.join(os.path.dirname(__file__), "settings.yaml")

# Globálna premenná nastavení
settings = {}

def load_settings():
    """Načíta nastavenia zo súboru alebo vytvorí predvolené nastavenia, ak súbor neexistuje"""
    global settings
    
    try:
        # Skontroluj formát nastavený v predchádzajúcom behu
        format_preference = "JSON"
        
        # Najprv skús načítať z JSON (predvolené)
        if os.path.exists(SETTINGS_FILE_JSON):
            with open(SETTINGS_FILE_JSON, 'r') as f:
                settings = json.load(f)
                format_preference = settings.get("system", {}).get("config_format", "JSON")
                print(f"DEBUG: Nastavenia načítané z {SETTINGS_FILE_JSON}")
        # Ak neexistuje JSON, skontroluj YAML
        elif os.path.exists(SETTINGS_FILE_YAML):
            with open(SETTINGS_FILE_YAML, 'r') as f:
                settings = yaml.safe_load(f)
                format_preference = settings.get("system", {}).get("config_format", "YAML")
                print(f"DEBUG: Nastavenia načítané z {SETTINGS_FILE_YAML}")
        # Ak neexistuje ani jeden, vytvor predvolené nastavenia
        else:
            settings = DEFAULT_SETTINGS.copy()
            save_settings()
            print(f"DEBUG: Vytvorený predvolený súbor nastavení")
        
        # Zabezpeč, že všetky sekcie nastavení existujú a majú aspoň predvolené hodnoty
        for section, default_values in DEFAULT_SETTINGS.items():
            if section not in settings:
                settings[section] = default_values
            elif isinstance(default_values, dict):
                for key, val in default_values.items():
                    if key not in settings[section]:
                        settings[section][key] = val
        
        return settings
    except Exception as e:
        print(f"ERROR: Zlyhalo načítanie nastavení: {e}")
        settings = DEFAULT_SETTINGS.copy()
        return settings

def save_settings():
    """Uloží aktuálne nastavenia do súboru vo formáte podľa preferencie"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE_JSON), exist_ok=True)
        
        # Kontrola preferovaného formátu (predvolene JSON)
        format_preference = settings.get("system", {}).get("config_format", "JSON")
        
        if format_preference == "YAML":
            with open(SETTINGS_FILE_YAML, 'w') as f:
                yaml.dump(settings, f, default_flow_style=False)
            # Odstráň JSON súbor, ak existuje, aby sme predišli zmätku
            if os.path.exists(SETTINGS_FILE_JSON):
                os.remove(SETTINGS_FILE_JSON)
            print(f"DEBUG: Nastavenia uložené do {SETTINGS_FILE_YAML}")
        else:  # Defaultne JSON
            with open(SETTINGS_FILE_JSON, 'w') as f:
                json.dump(settings, f, indent=4)
            # Odstráň YAML súbor, ak existuje
            if os.path.exists(SETTINGS_FILE_YAML):
                os.remove(SETTINGS_FILE_YAML)
            print(f"DEBUG: Nastavenia uložené do {SETTINGS_FILE_JSON}")
        
        return True
    except Exception as e:
        print(f"ERROR: Zlyhalo uloženie nastavení: {e}")
        return False

def get_setting(key, default=None):
    """Získa konkrétne nastavenie podľa kľúča s podporou vnorených kľúčov (napr. 'network.tcp_port')"""
    keys = key.split('.')
    
    # Prejdi cez všetky kľúče
    current = settings
    try:
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current
    except (KeyError, TypeError):
        return default

def update_setting(key, value):
    """Aktualizuje konkrétne nastavenie a uloží do súboru s podporou vnorených kľúčov"""
    keys = key.split('.')
    
    # Príprava odkazu na správnu pozíciu nastavenia
    if len(keys) == 1:
        settings[keys[0]] = value
    else:
        current = settings
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    
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
        timestamp = time.time()
        
    settings["sensor_status"][device_id][sensor_type] = {
        "status": status,
        "timestamp": timestamp
    }
    
    # Pridanie upozornenia do histórie, ak je stav aktivovaný
    if settings.get("system_active", False) and status in ["OPEN", "DETECTED", "TRIGGERED"]:
        add_alert(device_id, sensor_type, status, timestamp)
    
    return save_settings()

def add_alert(device_id, sensor_type, status, timestamp=None):
    """Pridá upozornenie do histórie upozornení"""
    # Inicializuj zoznam upozornení, ak neexistuje
    if "alerts" not in settings:
        settings["alerts"] = {}
    
    if "history" not in settings["alerts"]:
        settings["alerts"]["history"] = []
    
    # Získaj názov zariadenia
    device_name = "Unknown Device"
    if device_id in settings.get("sensor_devices", {}):
        device_name = settings["sensor_devices"][device_id].get("name", "Unknown Device")
    
    # Vytvor upozornenie
    alert = {
        "device_id": device_id,
        "device_name": device_name,
        "sensor_type": sensor_type,
        "status": status,
        "timestamp": timestamp or time.time(),
        "read": False
    }
    
    # Pridaj na začiatok zoznamu (najnovšie prvé)
    settings["alerts"]["history"].insert(0, alert)
    
    # Obmedzenie dĺžky histórie
    retention_days = settings.get("alerts", {}).get("retention_days", 30)
    threshold_time = time.time() - (retention_days * 24 * 60 * 60)
    
    # Odstráňenie starých upozornení
    settings["alerts"]["history"] = [a for a in settings["alerts"]["history"] 
                                   if a["timestamp"] > threshold_time]
    
    # Trigger notification sound if enabled
    if settings.get("alerts", {}).get("sound_enabled", True):
        try:
            # Import here to avoid circular import issues
            from sound_manager import sound_manager
            
            # Play different sound based on notification type
            notification_type = settings.get("alerts", {}).get("notification_type", "Visual")
            if status in ["OPEN", "DETECTED", "TRIGGERED", "ALARM"]:
                if notification_type == "Full Screen":
                    # Play alarm sound for critical alerts with full screen notification
                    sound_manager.play_alarm(duration_seconds=10)
                else:
                    # Play normal notification sound
                    sound_manager.play_sound("alarm" if "motion" in sensor_type.lower() else "notification")
        except ImportError:
            print("WARNING: Sound manager not available, notification sound not played")
    
    # Send email/SMS notifications if enabled
    try:
        # Get relevant image for this alert
        image_path = None
        if status in ["OPEN", "DETECTED", "TRIGGERED", "ALARM"]:
            # Find the most recent image related to this alert
            storage_path = settings.get("images", {}).get("storage_path", "captures")
            # If not an absolute path, create path relative to project
            if not os.path.isabs(storage_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_path = os.path.join(base_dir, storage_path)
                
            # Find image with closest timestamp
            if os.path.exists(storage_path):
                for filename in os.listdir(storage_path):
                    if filename.startswith(f"{sensor_type.lower()}_") and filename.endswith(('.jpg', '.jpeg', '.png')):
                        image_path = os.path.join(storage_path, filename)
                        # Just use the first matching image (which should be the most recent if sorted by time)
                        break
            
            # Import notification service and send alert
            from notification_service import notification_service
            notification_service.send_notification(
                alert_type=sensor_type,
                device_name=device_name,
                status=status,
                sensor_type=sensor_type,
                image_path=image_path
            )
    except ImportError:
        print("WARNING: Notification service not available")
    except Exception as e:
        print(f"ERROR: Failed to send notification: {e}")
    
    return save_settings()

def get_alerts(count=None, unread_only=False):
    """Získa zoznam upozornení s voliteľným filtrovaním"""
    alerts = settings.get("alerts", {}).get("history", [])
    
    if unread_only:
        alerts = [a for a in alerts if not a.get("read", False)]
    
    if count is not None:
        alerts = alerts[:count]
    
    return alerts

def mark_alert_as_read(alert_index):
    """Označí upozornenie ako prečítané podľa indexu"""
    if ("alerts" in settings and "history" in settings["alerts"] and 
            0 <= alert_index < len(settings["alerts"]["history"])):
        settings["alerts"]["history"][alert_index]["read"] = True
        return save_settings()
    return False

def cleanup_old_images():
    """Odstráni staré obrázky podľa nastavenia retencie"""
    import os
    from datetime import datetime, timedelta
    
    storage_path = settings.get("images", {}).get("storage_path", "captures")
    retention_days = settings.get("images", {}).get("retention_days", 14)
    
    # Absolútna cesta k adresáru na základe relatívnej cesty
    if not os.path.isabs(storage_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        storage_path = os.path.join(base_dir, storage_path)
    
    try:
        if os.path.exists(storage_path):
            threshold_date = datetime.now() - timedelta(days=retention_days)
            
            for filename in os.listdir(storage_path):
                file_path = os.path.join(storage_path, filename)
                
                # Preskočenie adresárov
                if os.path.isdir(file_path):
                    continue
                
                # Kontrola dátumu vytvorenia/modifikácie súboru
                file_time = os.path.getmtime(file_path)
                file_date = datetime.fromtimestamp(file_time)
                
                if file_date < threshold_date:
                    os.remove(file_path)
                    print(f"DEBUG: Odstránený starý obrázok: {filename}")
        
    except Exception as e:
        print(f"ERROR: Zlyhalo čistenie starých obrázkov: {e}")