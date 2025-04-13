import os
import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
try:
    import pygame
except ImportError:
    pygame = None
from config.settings import get_setting

class NotificationService:
    """
    Konsolidovaná služba na odosielanie notifikácií pre bezpečnostné upozornenia - email aj zvukové.
    Táto trieda nahrádza a kombinuje funkcionalitu pôvodných NotificationService a SoundManager.
    """
    
    def __init__(self):
        """Inicializácia notifikačnej služby"""
        # Predvolené nastavenia notifikácií
        self.notification_thread = None
        self.last_notification = 0  # Časová pečiatka poslednej odoslanej notifikácie
        
        # Inicializácia zvukového systému
        self.sound_initialized = False
        if pygame:
            try:
                pygame.mixer.init()
                self.sound_initialized = True
                print("Zvukový systém úspešne inicializovaný")
            except Exception as e:
                print(f"Zlyhala inicializácia zvukového systému: {e}")
        
        # Nájdenie zvukových súborov
        self.assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        
        # Predvolené cesty zvukov
        self.sounds = {
            "alarm": os.path.join(self.assets_dir, "alarm.wav"),
            "notification": os.path.join(self.assets_dir, "notification.wav"),
            "error": os.path.join(self.assets_dir, "error.wav")
        }
        
        # Príznaky na ovládanie prehrávania zvuku
        self.playing_alarm = False
        self.alarm_thread = None
        
        # Časovač pre oneskorené upozornenia
        self.grace_period_timer = None
        self.grace_period_alert = None
        self.is_in_grace_period = False
    
    def send_email_alert(self, subject, message, image_path=None):
        """Odoslanie e-mailového upozornenia
        
        Args:
            subject (str): Predmet e-mailu
            message (str): Telo správy e-mailu
            image_path (str, optional): Cesta k obrázku na pripojenie
        
        Returns:
            bool: True, ak bol e-mail úspešne odoslaný, inak False
        """
        # Získanie nastavení e-mailu z konfigurácie
        email_settings = get_setting("notifications.email", {})
        
        # Kontrola, či sú e-mailové notifikácie povolené
        if not email_settings.get("enabled", False):
            print("E-mailové notifikácie sú zakázané")
            return False
            
        # Získanie konfiguračných hodnôt
        smtp_server = email_settings.get("smtp_server", "")
        smtp_port = email_settings.get("smtp_port", 587)
        sender_email = email_settings.get("sender_email", "")
        sender_password = email_settings.get("sender_password", "")
        recipient_emails = email_settings.get("recipient_emails", [])
        
        # Kontrola povinných nastavení
        if not all([smtp_server, sender_email, sender_password, recipient_emails]):
            print("Chýbajú povinné nastavenia e-mailu")
            return False
        
        try:
            # Vytvorenie správy
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = ", ".join(recipient_emails)
            msg['Subject'] = subject
            
            # Pridanie časovej pečiatky
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_message = f"{message}\n\nČas upozornenia: {timestamp}"
            
            # Pridanie tela správy
            msg.attach(MIMEText(full_message, 'plain'))
            
            # Pridanie obrázku, ak existuje
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as img_file:
                    img_data = img_file.read()
                    image = MIMEImage(img_data, name=os.path.basename(image_path))
                    msg.attach(image)
            
            # Odoslanie e-mailu
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            print(f"E-mailové upozornenie úspešne odoslané pre {len(recipient_emails)} príjemcov")
            return True
            
        except Exception as e:
            print(f"Zlyhalo odoslanie e-mailového upozornenia: {e}")
            return False
    
    def play_sound(self, sound_type="notification", loops=0):
        """Prehratie zvuku špecifikovaného typu
        
        Args:
            sound_type (str): Typ zvuku na prehratie ('alarm', 'notification', 'error')
            loops (int): Počet opakovaní zvuku (-1 pre nekonečno)
            
        Returns:
            bool: True, ak bol zvuk úspešne prehratý, inak False
        """
        # Kontrola, či sú zvuky povolené v nastaveniach
        if not get_setting("alerts.sound_enabled", True):
            print("Zvuk je zakázaný v nastaveniach")
            return False
        
        # Kontrola, či je zvukový systém inicializovaný
        if not self.sound_initialized:
            print("Nemožno prehrať zvuk: Zvukový systém nie je inicializovaný")
            return False
        
        # Kontrola, či existuje zvukový súbor
        if sound_type not in self.sounds or not os.path.exists(self.sounds[sound_type]):
            print(f"Nemožno prehrať zvuk: Zvukový súbor {sound_type} nebol nájdený")
            return False
        
        try:
            # Načítanie a prehratie zvuku
            sound = pygame.mixer.Sound(self.sounds[sound_type])
            sound.play(loops=loops)
            return True
        except Exception as e:
            print(f"Zlyhalo prehrávanie zvuku: {e}")
            return False
    
    def play_alarm(self, duration_seconds=30):
        """Prehratie zvuku alarmu v samostatnom vlákne s trvaním
        
        Args:
            duration_seconds (int): Trvanie prehrávania alarmu v sekundách
        """
        if self.playing_alarm:
            print("Alarm sa už prehráva")
            return
        
        def alarm_thread():
            self.playing_alarm = True
            # Prehratie zvuku alarmu
            if self.play_sound("alarm", -1):  # -1 znamená opakovať nekonečne
                # Čakanie na stanovené trvanie
                time.sleep(duration_seconds)
                # Zastavenie alarmu
                self.stop_alarm()
        
        # Vytvorenie a spustenie vlákna alarmu
        self.alarm_thread = threading.Thread(target=alarm_thread)
        self.alarm_thread.daemon = True
        self.alarm_thread.start()
    
    def stop_alarm(self):
        """Zastavenie aktuálne hrajúceho zvuku alarmu"""
        if not self.playing_alarm:
            return
        
        try:
            # Zastavenie všetkých kanálov
            if self.sound_initialized:
                pygame.mixer.stop()
            self.playing_alarm = False
            print("Alarm zastavený")
        except Exception as e:
            print(f"Zlyhalo zastavenie alarmu: {e}")
    
    def send_notification(self, title, message, notification_type="normal", image_path=None):
        """Zjednotené rozhranie pre odoslanie všetkých typov notifikácií
        
        Args:
            title (str): Názov notifikácie
            message (str): Správa notifikácie
            notification_type (str): Typ notifikácie ('normal', 'alert', 'error')
            image_path (str, optional): Cesta k priloženému obrázku
            
        Returns:
            bool: True, ak bola notifikácia úspešne odoslaná
        """
        result = True
        
        # Prehratie príslušného zvuku podľa typu notifikácie
        sound_map = {
            "normal": "notification",
            "alert": "alarm",
            "error": "error"
        }
        sound_type = sound_map.get(notification_type, "notification")
        
        # Prehrávanie zvuku
        if notification_type == "alert":
            self.play_alarm()
        else:
            self.play_sound(sound_type)
        
        # Odoslanie e-mailovej notifikácie pre upozornenia a chyby
        if notification_type in ["alert", "error"]:
            email_result = self.send_email_alert(title, message, image_path)
            result = result and email_result
            
        return result

    def start_grace_period(self, alert_data, grace_seconds=30):
        """Spustí ochranný časovač pre upozornenie
        
        Args:
            alert_data (dict): Dáta upozornenia (na odoslanie po vypršaní časovača)
            grace_seconds (int): Trvanie ochrannej doby v sekundách
        """
        # Ak už beží ochranný časovač, ukončíme ho
        self.cancel_grace_period()
        
        # Uloženie dát upozornenia
        self.grace_period_alert = alert_data
        self.is_in_grace_period = True
        
        print(f"DEBUG: Spustený ochranný časovač na {grace_seconds} sekúnd")
        
        # Funkcia pre časovač, ktorá sa spustí po vypršaní ochrannej doby
        def grace_period_expired():
            if not self.is_in_grace_period:
                return  # Časovač bol medzičasom zrušený
            
            print("DEBUG: Vypršala ochranná doba - aktivujem alarm a odosielajm email")
            
            # Prehranie alarmu
            self.play_alarm()
            
            # Odoslanie emailu
            title = f"BEZPEČNOSTNÉ UPOZORNENIE - {alert_data.get('sensor_type', 'Senzor')} {alert_data.get('status', '')}"
            message = f"Bezpečnostný systém detekoval udalosť:\n" + \
                     f"Zariadenie: {alert_data.get('device_name', 'Neznáme zariadenie')}\n" + \
                     f"Typ senzora: {alert_data.get('sensor_type', 'Neznámy')}\n" + \
                     f"Stav: {alert_data.get('status', 'Neznámy')}\n\n" + \
                     f"Systém nebol deaktivovaný v ochrannej dobe {grace_seconds} sekúnd."
            
            # Odoslanie emailového upozornenia
            self.send_email_alert(title, message)
            
            # Reset premenných ochrannej doby
            self.is_in_grace_period = False
            self.grace_period_alert = None
            self.grace_period_timer = None
        
        # Vytvorenie a spustenie časovača
        self.grace_period_timer = threading.Timer(grace_seconds, grace_period_expired)
        self.grace_period_timer.daemon = True
        self.grace_period_timer.start()
        
        # Prehranie upozorňovacieho zvuku (nie alarm) na oznámenie spustenia ochrannej doby
        self.play_sound("notification")
        
    def cancel_grace_period(self):
        """Zruší prebiehajúci ochranný časovač"""
        if self.grace_period_timer and self.is_in_grace_period:
            self.grace_period_timer.cancel()
            self.grace_period_timer = None
            self.is_in_grace_period = False
            self.grace_period_alert = None
            print("DEBUG: Ochranný časovač zrušený")
            return True
        return False
        
    def get_grace_period_status(self):
        """Vráti informácie o prebiehajúcom ochrannom časovači
        
        Returns:
            dict: Stav ochrannej doby alebo None ak nebeží
        """
        if not self.is_in_grace_period:
            return None
            
        return {
            "active": True,
            "alert_data": self.grace_period_alert
        }
    
    def get_grace_period_remaining_time(self):
        """Returns the number of seconds remaining in the grace period
        
        Returns:
            int: Seconds remaining, or 0 if no grace period is active
        """
        if not self.is_in_grace_period or not self.grace_period_timer:
            return 0
            
        # Get remaining time by checking the timer's remaining time
        # The timer's _target_time is when it will fire (private attribute)
        if hasattr(self.grace_period_timer, '_target_time'):
            current_time = time.time()
            target_time = self.grace_period_timer._target_time
            remaining = max(0, int(target_time - current_time))
            return remaining
            
        # Fallback if we can't access the timer's target time
        return 30  # Default to 30 seconds

# Vytvorenie globálnej inštancie pre jednoduchý prístup
notification_service = NotificationService()