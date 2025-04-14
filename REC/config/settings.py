import json
import os
import yaml
import time
from datetime import datetime, timedelta

class SettingsManager:
    """Centralizovaný správca nastavení aplikácie s podporou rôznych formátov"""
    
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
        "notifications": {
            "email": {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "to_email": ""
            },
            "cooldown_seconds": 60
        },
        "sensors": [],
        "sensor_devices": {},
        "sensor_status": {}
    }
    
    def __init__(self):
        """Inicializácia správcu nastavení"""
        # Cesta k súboru nastavení
        self.config_dir = os.path.dirname(__file__)
        self.settings_file_json = os.path.join(self.config_dir, "settings.json")
        self.settings_file_yaml = os.path.join(self.config_dir, "settings.yaml")
        
        # Nastavenia aplikácie
        self.settings = {}
        self.load()
    
    def load(self):
        """Načíta nastavenia zo súboru alebo vytvorí predvolené nastavenia, ak súbor neexistuje"""
        try:
            # Skontroluj formát nastavený v predchádzajúcom behu
            format_preference = "JSON"
            
            # Najprv skús načítať z JSON (predvolené)
            if os.path.exists(self.settings_file_json):
                with open(self.settings_file_json, 'r') as f:
                    self.settings = json.load(f)
                    format_preference = self.settings.get("system", {}).get("config_format", "JSON")
                    print(f"DEBUG: Nastavenia načítané z {self.settings_file_json}")
            # Ak neexistuje JSON, skontroluj YAML
            elif os.path.exists(self.settings_file_yaml):
                with open(self.settings_file_yaml, 'r') as f:
                    self.settings = yaml.safe_load(f)
                    format_preference = self.settings.get("system", {}).get("config_format", "YAML")
                    print(f"DEBUG: Nastavenia načítané z {self.settings_file_yaml}")
            # Ak neexistuje ani jeden, vytvor predvolené nastavenia
            else:
                self.settings = self.DEFAULT_SETTINGS.copy()
                self.save()
                print(f"DEBUG: Vytvorený predvolený súbor nastavení")
            
            # Zabezpeč, že všetky sekcie nastavení existujú a majú aspoň predvolené hodnoty
            for section, default_values in self.DEFAULT_SETTINGS.items():
                if section not in self.settings:
                    self.settings[section] = default_values
                elif isinstance(default_values, dict):
                    for key, val in default_values.items():
                        if key not in self.settings[section]:
                            self.settings[section][key] = val
            
            return self.settings
        except Exception as e:
            print(f"ERROR: Zlyhalo načítanie nastavení: {e}")
            self.settings = self.DEFAULT_SETTINGS.copy()
            return self.settings
    
    def save(self):
        """Uloží aktuálne nastavenia do súboru vo formáte podľa preferencie"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Kontrola preferovaného formátu (predvolene JSON)
            format_preference = self.settings.get("system", {}).get("config_format", "JSON")
            
            if format_preference == "YAML":
                with open(self.settings_file_yaml, 'w') as f:
                    yaml.dump(self.settings, f, default_flow_style=False)
                # Odstráň JSON súbor, ak existuje, aby sme predišli zmätku
                if os.path.exists(self.settings_file_json):
                    os.remove(self.settings_file_json)
                print(f"DEBUG: Nastavenia uložené do {self.settings_file_yaml}")
            else:  # Defaultne JSON
                with open(self.settings_file_json, 'w') as f:
                    json.dump(self.settings, f, indent=4)
                # Odstráň YAML súbor, ak existuje
                if os.path.exists(self.settings_file_yaml):
                    os.remove(self.settings_file_yaml)
                print(f"DEBUG: Nastavenia uložené do {self.settings_file_json}")
            
            return True
        except Exception as e:
            print(f"ERROR: Zlyhalo uloženie nastavení: {e}")
            return False
    
    def get(self, key, default=None):
        """Získa konkrétne nastavenie podľa kľúča s podporou vnorených kľúčov (napr. 'network.tcp_port')"""
        keys = key.split('.')
        
        # Prejdi cez všetky kľúče
        current = self.settings
        try:
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return default
            return current
        except (KeyError, TypeError):
            return default
    
    def update(self, key, value):
        """Aktualizuje konkrétne nastavenie a uloží do súboru s podporou vnorených kľúčov"""
        keys = key.split('.')
        
        # Príprava odkazu na správnu pozíciu nastavenia
        if len(keys) == 1:
            self.settings[keys[0]] = value
        else:
            current = self.settings
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        
        return self.save()
    
    def validate_pin(self, pin_input):
        """Overí, či zadaný PIN zodpovedá uloženému PIN-u"""
        stored_pin = self.settings.get("pin_code", self.DEFAULT_SETTINGS["pin_code"])
        return pin_input == stored_pin
    
    def update_pin(self, new_pin):
        """Aktualizuje PIN kód"""
        if len(new_pin) >= 4:
            return self.update("pin_code", new_pin)
        return False
    
    def toggle_system_state(self, new_state=None):
        """Prepne alebo nastaví stav systému (aktívny/neaktívny)"""
        if new_state is None:
            new_state = not self.settings.get("system_active", self.DEFAULT_SETTINGS["system_active"])
        return self.update("system_active", new_state)
    
    def get_sensor_devices(self):
        """Získa zoznam známych zariadení senzorov"""
        return self.settings.get("sensor_devices", {})
    
    def add_sensor_device(self, device_id, device_data):
        """Pridá alebo aktualizuje zariadenie senzora"""
        if "sensor_devices" not in self.settings:
            self.settings["sensor_devices"] = {}
        
        # Aktualizuje alebo pridá zariadenie
        self.settings["sensor_devices"][device_id] = device_data
        return self.save()
    
    def remove_sensor_device(self, device_id):
        """Odstráni zariadenie senzora"""
        if "sensor_devices" in self.settings and device_id in self.settings["sensor_devices"]:
            del self.settings["sensor_devices"][device_id]
            # Tiež odstráň zo stavu senzorov, ak existuje
            if "sensor_status" in self.settings and device_id in self.settings["sensor_status"]:
                del self.settings["sensor_status"][device_id]
            return self.save()
        return False
    
    def get_sensor_status(self):
        """Získa aktuálny stav všetkých senzorov"""
        return self.settings.get("sensor_status", {})
    
    def update_sensor_status(self, device_id, status_data):
        """Aktualizuje stav senzora"""
        if "sensor_status" not in self.settings:
            self.settings["sensor_status"] = {}
        
        # Aktualizuje alebo pridá stav
        current_status = self.settings["sensor_status"].get(device_id, {})
        current_status.update(status_data)
        current_status["last_updated"] = time.time()
        
        self.settings["sensor_status"][device_id] = current_status
        return self.save()

# Vytvor globálnu inštanciu manažéra nastavení
settings_manager = SettingsManager()

# Vytvor spiatočne kompatibilné funkcie pre jednoduchú migráciu z predošlej verzie
def load_settings():
    """Kompatibilná funkcia - načíta nastavenia"""
    return settings_manager.load()

def save_settings():
    """Kompatibilná funkcia - uloží nastavenia"""
    return settings_manager.save()

def get_setting(key, default=None):
    """Kompatibilná funkcia - získa nastavenie"""
    return settings_manager.get(key, default)

def update_setting(key, value):
    """Kompatibilná funkcia - aktualizuje nastavenie"""
    return settings_manager.update(key, value)

def validate_pin(pin_input):
    """Kompatibilná funkcia - overí PIN"""
    return settings_manager.validate_pin(pin_input)

def update_pin(new_pin):
    """Kompatibilná funkcia - aktualizuje PIN"""
    return settings_manager.update_pin(new_pin)

def toggle_system_state(new_state=None):
    """Kompatibilná funkcia - prepne stav systému"""
    return settings_manager.toggle_system_state(new_state)

def get_sensor_devices():
    """Kompatibilná funkcia - získa zariadenia senzorov"""
    return settings_manager.get_sensor_devices()

def add_sensor_device(device_id, device_data):
    """Kompatibilná funkcia - pridá zariadenie senzora"""
    return settings_manager.add_sensor_device(device_id, device_data)

def remove_sensor_device(device_id):
    """Kompatibilná funkcia - odstráni zariadenie senzora"""
    return settings_manager.remove_sensor_device(device_id)

def get_sensor_status():
    """Kompatibilná funkcia - získa stav senzorov"""
    return settings_manager.get_sensor_status()

def update_sensor_status(device_id, status_data):
    """Kompatibilná funkcia - aktualizuje stav senzora"""
    return settings_manager.update_sensor_status(device_id, status_data)

# Funkcia pre správu upozornení

def get_alerts(count=None, unread_only=False):
    """Získanie uložených upozornení zo systému - ZASTARANÉ
    
    Použite alerts_log.get_alerts() namiesto toho.
    Táto funkcia je zachovaná pre spätnú kompatibilitu.
    
    Args:
        count (int): Maximálny počet upozornení na vrátenie
        unread_only (bool): Či zahrnúť iba neprečítané upozornenia
    
    Returns:
        list: Zoznam upozornení
    """
    # Import tu na predídenie cirkulárnym importom
    from config.alerts_log import get_alerts as get_alerts_from_log
    return get_alerts_from_log(count, unread_only)

def add_alert(alert_data):
    """Pridanie nového upozornenia do systému - ZASTARANÉ
    
    Použite alerts_log.add_alert() namiesto toho.
    Táto funkcia je zachovaná pre spätnú kompatibilitu.
    
    Args:
        alert_data (dict): Dáta upozornenia (typ, správa, atď.)
    
    Returns:
        bool: True, ak bolo upozornenie úspešne pridané
    """
    # Import tu na predídenie cirkulárnym importom
    from config.alerts_log import add_alert as add_alert_to_log
    return add_alert_to_log(alert_data)

def mark_alert_as_read(alert_index):
    """Označenie upozornenia ako prečítané - ZASTARANÉ
    
    Použite alerts_log.mark_alert_as_read() namiesto toho.
    Táto funkcia je zachovaná pre spätnú kompatibilitu.
    
    Args:
        alert_index (int): Index upozornenia v zozname, ktoré sa má označiť ako prečítané
    
    Returns:
        bool: True, ak bolo upozornenie úspešne označené ako prečítané
    """
    # Import tu na predídenie cirkulárnym importom
    from config.alerts_log import mark_alert_as_read as mark_alert_read_in_log
    return mark_alert_read_in_log(alert_index)

def mark_all_alerts_as_read():
    """Označenie všetkých upozornení ako prečítané - ZASTARANÉ
    
    Použite alerts_log.mark_all_alerts_as_read() namiesto toho.
    Táto funkcia je zachovaná pre spätnú kompatibilitu.
    
    Returns:
        bool: True, ak boli všetky upozornenia úspešne označené ako prečítané
    """
    # Import tu na predídenie cirkulárnym importom
    from config.alerts_log import mark_all_alerts_as_read as mark_all_read_in_log
    return mark_all_read_in_log()

def cleanup_old_images():
    """Vymaže staré obrázky podľa nastavenia retencie
    
    Returns:
        tuple: (počet odstránených súborov, celková uvoľnená veľkosť v bajtoch)
    """
    storage_path = settings_manager.get("images.storage_path", "captures")
    retention_days = settings_manager.get("images.retention_days", 14)
    
    # Ak je cesta relatívna, vyrieš ju vzhľadom na adresár skriptu
    if not os.path.isabs(storage_path):
        storage_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), storage_path)
    
    # Ak adresár neexistuje, nič sa neodstráni
    if not os.path.exists(storage_path) or not os.path.isdir(storage_path):
        print(f"Adresár pre obrázky neexistuje: {storage_path}")
        return 0, 0
    
    # Vypočítanie hraničného času pre vymazanie
    cutoff_time = datetime.now() - timedelta(days=retention_days)
    cutoff_timestamp = cutoff_time.timestamp()
    
    files_removed = 0
    bytes_freed = 0
    
    try:
        for filename in os.listdir(storage_path):
            file_path = os.path.join(storage_path, filename)
            
            # Preskočenie adresárov
            if os.path.isdir(file_path):
                continue
            
            # Kontrola času vytvorenia/modifikácie súboru
            file_timestamp = os.path.getmtime(file_path)
            
            # Ak je súbor starší ako hraničný čas, odstráň ho
            if file_timestamp < cutoff_timestamp:
                file_size = os.path.getsize(file_path)
                try:
                    os.remove(file_path)
                    files_removed += 1
                    bytes_freed += file_size
                    print(f"Odstránený starý súbor: {filename}")
                except Exception as e:
                    print(f"Zlyhalo odstránenie súboru {filename}: {e}")
        
        return files_removed, bytes_freed
    except Exception as e:
        print(f"Zlyhalo čistenie starých obrázkov: {e}")
        return 0, 0