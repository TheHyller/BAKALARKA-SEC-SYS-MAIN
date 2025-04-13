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
            "retention_days": 30,
            "items": []
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
        self.base_dir = os.path.dirname(__file__)
        self.config_dir = os.path.join(self.base_dir, "config")
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
    previous_state = settings_manager.get("system_active", False)
    result = settings_manager.toggle_system_state(new_state)
    
    # Ak sa stav systému zmenil z aktívneho na neaktívny, zruš ochranné časovače
    if previous_state == True and (new_state is False or new_state is None):
        try:
            # Import notifikačnej služby až tu, aby sme predišli cyklickému importu
            from notification_service import notification_service
            # Zrušenie bežiacich ochranných časovačov
            notification_service.cancel_grace_period()
            print("DEBUG: Zrušené ochranné časovače pri deaktivácii systému")
        except Exception as e:
            print(f"ERROR: Zlyhalo zrušenie ochranných časovačov: {e}")
    
    return result

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

def get_alerts(include_read=False, max_count=None):
    """Získa uložené upozornenia zo systému
    
    Args:
        include_read (bool): Či zahrnúť prečítané upozornenia
        max_count (int): Maximálny počet upozornení pre vrátenie
    
    Returns:
        list: Zoznam upozornení
    """
    alerts = settings_manager.get("alerts.items", [])
    
    # Ak sú vyžiadané len neprečítané upozornenia
    if not include_read:
        alerts = [alert for alert in alerts if not alert.get("read", False)]
    
    # Zoradenie upozornení zostupne podľa času (najnovšie prvé)
    alerts = sorted(alerts, key=lambda x: x.get("timestamp", 0), reverse=True)
    
    # Ak je zadaný maximálny počet, obmedz výsledky
    if max_count is not None and isinstance(max_count, int):
        alerts = alerts[:max_count]
    
    return alerts

def add_alert(alert_data):
    """Pridá nové upozornenie do systému
    
    Args:
        alert_data (dict): Dáta upozornenia (typ, správa, atď.)
    
    Returns:
        bool: True ak bolo upozornenie úspešne pridané
    """
    # Zabezpeč, že základné polia sú prítomné
    alert = {
        "id": int(time.time() * 1000),  # Unikátne ID na základe časovej značky v milisekundách
        "timestamp": time.time(),
        "read": False,
        "type": alert_data.get("type", "Info"),
        "message": alert_data.get("message", "Neznáme upozornenie")
    }
    
    # Pridaj akékoľvek ďalšie dáta
    alert.update(alert_data)
    
    # Získaj aktuálne upozornenia a pridaj nové
    alerts = settings_manager.get("alerts.items", [])
    alerts.append(alert)
    
    # Ukladá upozornenia naspäť a zachováva najnovšie upozornenia
    retention_days = settings_manager.get("alerts.retention_days", 30)
    cutoff_time = time.time() - (retention_days * 24 * 3600)
    
    # Odstráň staré upozornenia
    alerts = [a for a in alerts if a.get("timestamp", 0) > cutoff_time]
    
    # Uloženie aktualizovaných upozornení
    return settings_manager.update("alerts.items", alerts)

def mark_alert_as_read(alert_id):
    """Označí upozornenie ako prečítané
    
    Args:
        alert_id (int): ID upozornenia na označenie
    
    Returns:
        bool: True ak bolo upozornenie úspešne označené
    """
    alerts = settings_manager.get("alerts.items", [])
    
    # Nájdi a označ upozornenie ako prečítané
    for alert in alerts:
        if alert.get("id") == alert_id:
            alert["read"] = True
            alert["read_timestamp"] = time.time()
            return settings_manager.update("alerts.items", alerts)
    
    return False

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