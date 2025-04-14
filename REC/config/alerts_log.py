import json
import os
import time
from datetime import datetime, timedelta

class AlertsLogManager:
    """Správca pre manipuláciu so súborom denníka upozornení"""
    
    def __init__(self):
        """Inicializácia správcu denníka upozornení"""
        # Cesta k súboru denníka
        self.config_dir = os.path.dirname(__file__)
        self.log_file = os.path.join(self.config_dir, "alerts.log")
        
        # Inicializácia súboru denníka, ak neexistuje
        if not os.path.exists(self.log_file):
            self._write_log([])
    
    def get_alerts(self, count=None, unread_only=False):
        """Získanie uložených upozornení zo systému
        
        Args:
            count (int): Maximálny počet upozornení na vrátenie
            unread_only (bool): Či zahrnúť iba neprečítané upozornenia
        
        Returns:
            list: Zoznam upozornení
        """
        alerts = self._read_log()
        
        # Filtrovanie podľa stavu prečítania, ak je požadované
        if unread_only:
            alerts = [alert for alert in alerts if not alert.get("read", False)]
        
        # Zoradenie upozornení podľa časovej značky (najnovšie najprv)
        alerts = sorted(alerts, key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Obmedzenie výsledkov, ak je počet špecifikovaný
        if count is not None and isinstance(count, int) and count > 0:
            alerts = alerts[:count]
        
        return alerts
    
    def add_alert(self, alert_data, retention_days=30):
        """Pridanie nového upozornenia do systému
        
        Args:
            alert_data (dict): Dáta upozornenia (typ, správa, atď.)
            retention_days (int): Počet dní na uchovávanie upozornení
        
        Returns:
            bool: True, ak bolo upozornenie úspešne pridané
        """
        # Zabezpečenie, že základné polia sú prítomné
        alert = {
            "id": int(time.time() * 1000),  # Jedinečné ID založené na časovej značke v milisekundách
            "timestamp": time.time(),
            "read": False,
            "type": alert_data.get("type", "Info"),
            "message": alert_data.get("message", "Neznáme upozornenie")
        }
        
        # Pridanie akýchkoľvek dodatočných údajov
        alert.update(alert_data)
        
        # Získanie aktuálnych upozornení a pridanie nového
        alerts = self._read_log()
        alerts.append(alert)
        
        # Uchovanie iba nedávnych upozornení na základe doby uchovávania
        cutoff_time = time.time() - (retention_days * 24 * 3600)
        alerts = [a for a in alerts if a.get("timestamp", 0) > cutoff_time]
        
        # Uloženie aktualizovaných upozornení
        return self._write_log(alerts)
    
    def mark_alert_as_read(self, alert_index):
        """Označenie upozornenia ako prečítané
        
        Args:
            alert_index (int): Index upozornenia v zozname, ktoré sa má označiť ako prečítané
        
        Returns:
            bool: True, ak bolo upozornenie úspešne označené ako prečítané
        """
        alerts = self._read_log()
        
        # Uistenie sa, že upozornenia sú zoznam a index je platný
        if not isinstance(alerts, list) or not alerts:
            return False
        
        # Kontrola, či je index platný
        if 0 <= alert_index < len(alerts):
            alerts[alert_index]["read"] = True
            alerts[alert_index]["read_timestamp"] = time.time()
            return self._write_log(alerts)
        
        return False

    def mark_all_as_read(self):
        """Označenie všetkých upozornení ako prečítané
        
        Returns:
            bool: True, ak boli všetky upozornenia úspešne označené ako prečítané
        """
        alerts = self._read_log()
        
        if not alerts:
            return True
            
        current_time = time.time()
        for alert in alerts:
            if not alert.get("read", False):
                alert["read"] = True
                alert["read_timestamp"] = current_time
                
        return self._write_log(alerts)
    
    def _read_log(self):
        """Čítanie upozornení zo súboru denníka
        
        Returns:
            list: Zoznam upozornení
        """
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    alerts = json.load(f)
                    return alerts if isinstance(alerts, list) else []
            return []
        except Exception as e:
            print(f"CHYBA: Zlyhalo čítanie denníka upozornení: {e}")
            return []
    
    def _write_log(self, alerts):
        """Zápis upozornení do súboru denníka
        
        Args:
            alerts (list): Zoznam upozornení na zápis
        
        Returns:
            bool: True v prípade úspechu
        """
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.log_file, 'w') as f:
                json.dump(alerts, f, indent=4)
            return True
        except Exception as e:
            print(f"CHYBA: Zlyhalo zapisovanie denníka upozornení: {e}")
            return False

# Vytvorenie globálnej inštancie správcu denníka upozornení
alerts_log_manager = AlertsLogManager()

# Vytvorenie spätne kompatibilných funkcií pre jednoduchú migráciu
def get_alerts(count=None, unread_only=False):
    """Získanie uložených upozornení zo systému"""
    return alerts_log_manager.get_alerts(count, unread_only)

def add_alert(alert_data):
    """Pridanie nového upozornenia do systému"""
    from settings import get_setting
    retention_days = get_setting("alerts.retention_days", 30)
    return alerts_log_manager.add_alert(alert_data, retention_days)

def mark_alert_as_read(alert_index):
    """Označenie upozornenia ako prečítané"""
    return alerts_log_manager.mark_alert_as_read(alert_index)

def mark_all_alerts_as_read():
    """Označenie všetkých upozornení ako prečítané"""
    return alerts_log_manager.mark_all_as_read()