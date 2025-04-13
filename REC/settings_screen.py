from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
# Zmena relatívneho importu na absolútny import
from config.settings import get_setting, update_setting, save_settings
from base_screen import BaseScreen

class SettingsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        
        # Set title using BaseScreen method
        self.set_title("System Settings")
        self.add_back_button(target_screen='main')
        
        # Create content area for settings
        content_area = self.create_content_area()
        
        # Pridanie ScrollView pre obsah nastavení
        scroll_view = ScrollView(size_hint_y=1)
        
        # Formulár nastavení vo vnútri ScrollView
        form_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter('height'))
        
        # Sieťové nastavenia
        network_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=150)
        network_layout.add_widget(Label(text="Network Settings", font_size=18))
        
        # TCP Port
        tcp_layout = BoxLayout(orientation='horizontal', spacing=5)
        tcp_layout.add_widget(Label(text="TCP Port:", size_hint_x=0.3))
        self.tcp_port = TextInput(
            text=str(get_setting("network", {}).get("tcp_port", 8080)), 
            multiline=False,
            size_hint_x=0.7
        )
        tcp_layout.add_widget(self.tcp_port)
        network_layout.add_widget(tcp_layout)
        
        # UDP Port
        udp_layout = BoxLayout(orientation='horizontal', spacing=5)
        udp_layout.add_widget(Label(text="UDP Port:", size_hint_x=0.3))
        self.udp_port = TextInput(
            text=str(get_setting("network", {}).get("udp_port", 8081)), 
            multiline=False,
            size_hint_x=0.7
        )
        udp_layout.add_widget(self.udp_port)
        network_layout.add_widget(udp_layout)
        
        # Discovery Port
        discovery_layout = BoxLayout(orientation='horizontal', spacing=5)
        discovery_layout.add_widget(Label(text="Discovery Port:", size_hint_x=0.3))
        self.discovery_port = TextInput(
            text=str(get_setting("network", {}).get("discovery_port", 8082)), 
            multiline=False,
            size_hint_x=0.7
        )
        discovery_layout.add_widget(self.discovery_port)
        network_layout.add_widget(discovery_layout)
        
        form_layout.add_widget(network_layout)
        
        # Email Notifications Settings
        email_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=270)
        email_layout.add_widget(Label(text="Email Notifications", font_size=18))
        
        # Enable Email Notifications
        email_enable_layout = BoxLayout(orientation='horizontal', spacing=5)
        email_enable_layout.add_widget(Label(text="Enable Email:", size_hint_x=0.3))
        self.email_enabled = Switch(active=get_setting("notifications.email", {}).get("enabled", False))
        email_enable_wrapper = BoxLayout(orientation='horizontal', size_hint_x=0.7)
        email_enable_wrapper.add_widget(Label(text="Off", size_hint_x=0.15))
        email_enable_wrapper.add_widget(self.email_enabled)
        email_enable_wrapper.add_widget(Label(text="On", size_hint_x=0.15))
        email_enable_layout.add_widget(email_enable_wrapper)
        email_layout.add_widget(email_enable_layout)
        
        # SMTP Server
        smtp_server_layout = BoxLayout(orientation='horizontal', spacing=5)
        smtp_server_layout.add_widget(Label(text="SMTP Server:", size_hint_x=0.3))
        self.smtp_server = TextInput(
            text=get_setting("notifications.email", {}).get("smtp_server", "smtp.gmail.com"),
            multiline=False,
            size_hint_x=0.7
        )
        smtp_server_layout.add_widget(self.smtp_server)
        email_layout.add_widget(smtp_server_layout)
        
        # SMTP Port
        smtp_port_layout = BoxLayout(orientation='horizontal', spacing=5)
        smtp_port_layout.add_widget(Label(text="SMTP Port:", size_hint_x=0.3))
        self.smtp_port = TextInput(
            text=str(get_setting("notifications.email", {}).get("smtp_port", 587)),
            multiline=False,
            input_filter="int",
            size_hint_x=0.7
        )
        smtp_port_layout.add_widget(self.smtp_port)
        email_layout.add_widget(smtp_port_layout)
        
        # Username
        username_layout = BoxLayout(orientation='horizontal', spacing=5)
        username_layout.add_widget(Label(text="Username:", size_hint_x=0.3))
        self.email_username = TextInput(
            text=get_setting("notifications.email", {}).get("username", ""),
            multiline=False,
            size_hint_x=0.7
        )
        username_layout.add_widget(self.email_username)
        email_layout.add_widget(username_layout)
        
        # Password
        password_layout = BoxLayout(orientation='horizontal', spacing=5)
        password_layout.add_widget(Label(text="Password:", size_hint_x=0.3))
        self.email_password = TextInput(
            text=get_setting("notifications.email", {}).get("password", ""),
            multiline=False,
            password=True,
            size_hint_x=0.7
        )
        password_layout.add_widget(self.email_password)
        email_layout.add_widget(password_layout)
        
        # From Email
        from_email_layout = BoxLayout(orientation='horizontal', spacing=5)
        from_email_layout.add_widget(Label(text="From Email:", size_hint_x=0.3))
        self.from_email = TextInput(
            text=get_setting("notifications.email", {}).get("from_email", ""),
            multiline=False,
            size_hint_x=0.7
        )
        from_email_layout.add_widget(self.from_email)
        email_layout.add_widget(from_email_layout)
        
        # To Email
        to_email_layout = BoxLayout(orientation='horizontal', spacing=5)
        to_email_layout.add_widget(Label(text="To Email:", size_hint_x=0.3))
        self.to_email = TextInput(
            text=get_setting("notifications.email", {}).get("to_email", ""),
            multiline=False,
            size_hint_x=0.7
        )
        to_email_layout.add_widget(self.to_email)
        email_layout.add_widget(to_email_layout)
        
        # Test Email Button
        test_email_layout = BoxLayout(orientation='horizontal', spacing=5)
        test_email_button = Button(
            text="Test Email Settings",
            size_hint_x=1.0
        )
        test_email_button.bind(on_release=self.test_email_settings)
        test_email_layout.add_widget(test_email_button)
        email_layout.add_widget(test_email_layout)
        
        form_layout.add_widget(email_layout)
        
        # Alert Settings
        alert_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=150)
        alert_layout.add_widget(Label(text="Alert Settings", font_size=18))
        
        # Alert sound
        sound_layout = BoxLayout(orientation='horizontal', spacing=5)
        sound_layout.add_widget(Label(text="Alert Sound:", size_hint_x=0.3))
        self.alert_sound = Switch(active=get_setting("alerts", {}).get("sound_enabled", True))
        sound_wrapper = BoxLayout(orientation='horizontal', size_hint_x=0.7)
        sound_wrapper.add_widget(Label(text="Off", size_hint_x=0.15))
        sound_wrapper.add_widget(self.alert_sound)
        sound_wrapper.add_widget(Label(text="On", size_hint_x=0.15))
        sound_layout.add_widget(sound_wrapper)
        alert_layout.add_widget(sound_layout)
        
        # Alert notification type
        notification_layout = BoxLayout(orientation='horizontal', spacing=5)
        notification_layout.add_widget(Label(text="Notification Type:", size_hint_x=0.3))
        self.notification_type = Spinner(
            text=get_setting("alerts", {}).get("notification_type", "Visual"),
            values=("Visual", "Visual + Sound", "Full Screen"),
            size_hint_x=0.7
        )
        notification_layout.add_widget(self.notification_type)
        alert_layout.add_widget(notification_layout)
        
        # Alert history retention
        retention_layout = BoxLayout(orientation='horizontal', spacing=5)
        retention_layout.add_widget(Label(text="History (days):", size_hint_x=0.3))
        self.retention_days = TextInput(
            text=str(get_setting("alerts", {}).get("retention_days", 30)),
            multiline=False,
            input_filter="int",
            size_hint_x=0.7
        )
        retention_layout.add_widget(self.retention_days)
        alert_layout.add_widget(retention_layout)
        
        form_layout.add_widget(alert_layout)
        
        # Camera and Image Settings
        image_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=150)
        image_layout.add_widget(Label(text="Image Settings", font_size=18))
        
        # Image storage path
        path_layout = BoxLayout(orientation='horizontal', spacing=5)
        path_layout.add_widget(Label(text="Storage Path:", size_hint_x=0.3))
        self.storage_path = TextInput(
            text=get_setting("images", {}).get("storage_path", "captures"),
            multiline=False,
            size_hint_x=0.7
        )
        path_layout.add_widget(self.storage_path)
        image_layout.add_widget(path_layout)
        
        # Image retention
        img_retention_layout = BoxLayout(orientation='horizontal', spacing=5)
        img_retention_layout.add_widget(Label(text="Keep Images (days):", size_hint_x=0.3))
        self.img_retention_days = TextInput(
            text=str(get_setting("images", {}).get("retention_days", 14)),
            multiline=False,
            input_filter="int",
            size_hint_x=0.7
        )
        img_retention_layout.add_widget(self.img_retention_days)
        image_layout.add_widget(img_retention_layout)
        
        # Image quality
        quality_layout = BoxLayout(orientation='horizontal', spacing=5)
        quality_layout.add_widget(Label(text="Image Quality:", size_hint_x=0.3))
        self.image_quality = Spinner(
            text=get_setting("images", {}).get("quality", "Medium"),
            values=("Low", "Medium", "High"),
            size_hint_x=0.7
        )
        quality_layout.add_widget(self.image_quality)
        image_layout.add_widget(quality_layout)
        
        form_layout.add_widget(image_layout)
        
        # System Settings
        system_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=150)
        system_layout.add_widget(Label(text="System Settings", font_size=18))
        
        # Auto start on boot
        autostart_layout = BoxLayout(orientation='horizontal', spacing=5)
        autostart_layout.add_widget(Label(text="Auto Start:", size_hint_x=0.3))
        self.auto_start = Switch(active=get_setting("system", {}).get("auto_start", True))
        autostart_wrapper = BoxLayout(orientation='horizontal', size_hint_x=0.7)
        autostart_wrapper.add_widget(Label(text="Off", size_hint_x=0.15))
        autostart_wrapper.add_widget(self.auto_start)
        autostart_wrapper.add_widget(Label(text="On", size_hint_x=0.15))
        autostart_layout.add_widget(autostart_wrapper)
        system_layout.add_widget(autostart_layout)
        
        # Log level
        log_layout = BoxLayout(orientation='horizontal', spacing=5)
        log_layout.add_widget(Label(text="Log Level:", size_hint_x=0.3))
        self.log_level = Spinner(
            text=get_setting("system", {}).get("log_level", "INFO"),
            values=("DEBUG", "INFO", "WARNING", "ERROR"),
            size_hint_x=0.7
        )
        log_layout.add_widget(self.log_level)
        system_layout.add_widget(log_layout)
        
        # Configuration format
        config_layout = BoxLayout(orientation='horizontal', spacing=5)
        config_layout.add_widget(Label(text="Config Format:", size_hint_x=0.3))
        self.config_format = Spinner(
            text=get_setting("system", {}).get("config_format", "JSON"),
            values=("JSON", "YAML"),
            size_hint_x=0.7
        )
        config_layout.add_widget(self.config_format)
        system_layout.add_widget(config_layout)
        
        form_layout.add_widget(system_layout)
        
        # Pridanie form_layout do scroll_view
        scroll_view.add_widget(form_layout)
        content_area.add_widget(scroll_view)
        
        # Status message
        self.status_label = Label(
            text="",
            font_size=16,
            size_hint_y=0.05
        )
        content_area.add_widget(self.status_label)
        
        # Create footer for buttons
        footer = self.create_footer()
        
        save_button = Button(text="Save Settings")
        save_button.bind(on_release=self.save_settings)
        footer.add_widget(save_button)
        
    def test_email_settings(self, instance):
        """Test email settings by sending a test email"""
        try:
            # Načítanie aktuálnych nastavení
            notifications = get_setting("notifications", {})
            email_settings = notifications.get("email", {})
            
            # Aktualizácia nastavení pre test (bez ich uloženia)
            email_settings = {
                "enabled": True,
                "smtp_server": self.smtp_server.text,
                "smtp_port": int(self.smtp_port.text),
                "username": self.email_username.text,
                "password": self.email_password.text,
                "from_email": self.from_email.text or self.email_username.text,
                "to_email": self.to_email.text
            }
            
            # Kontrola, či sú všetky potrebné polia vyplnené
            if not all([
                email_settings["smtp_server"],
                email_settings["username"],
                email_settings["password"],
                email_settings["to_email"]
            ]):
                self.status_label.text = "Vyplňte všetky potrebné polia pre email"
                return
            
            # Import a použitie notifikačnej služby
            from notification_service import notification_service
            
            # Vytvorenie obsahu testového emailu
            subject = "Test bezpečnostného systému"
            message = "Toto je testovací email z bezpečnostného systému. Ak ste ho dostali, vaše nastavenia emailu fungujú správne."
            
            # Dočasné nastavenie
            temp_notifications = {"email": email_settings}
            
            # Zobrazenie informácie používateľovi
            self.status_label.text = "Odosielam testovací email..."
            
            # Volať funkcie notifikačnej služby priamo
            import threading
            def test_thread():
                try:
                    # Použitie upravených nastavení
                    original_get_setting = notification_service.get_setting
                    
                    def mock_get_setting(key, default=None):
                        if key == "notifications.email":
                            return email_settings
                        elif key == "notifications.email.enabled":
                            return True
                        else:
                            return original_get_setting(key, default)
                    
                    # Nahradenie get_setting funkcie
                    notification_service.get_setting = mock_get_setting
                    
                    # Odoslanie testovacieho emailu
                    success = notification_service.send_email_alert(subject, message)
                    
                    # Obnovenie pôvodnej funkcie
                    notification_service.get_setting = original_get_setting
                    
                    # Aktualizovanie stavu
                    if success:
                        self.status_label.text = "Testovací email úspešne odoslaný!"
                    else:
                        self.status_label.text = "Odoslanie testovacieho emailu zlyhalo"
                except Exception as e:
                    self.status_label.text = f"Chyba pri odosielaní emailu: {str(e)}"
            
            # Spustenie v samostatnom vlákne
            test_thread = threading.Thread(target=test_thread)
            test_thread.daemon = True
            test_thread.start()
            
        except Exception as e:
            self.status_label.text = f"Chyba pri testovaní emailu: {str(e)}"

    def save_settings(self, instance):
        """Uloženie nastavení do súboru"""
        try:
            # Aktualizácia sieťových nastavení
            network = get_setting("network", {})
            network["tcp_port"] = int(self.tcp_port.text)
            network["udp_port"] = int(self.udp_port.text)
            network["discovery_port"] = int(self.discovery_port.text)
            update_setting("network", network)
            
            # Aktualizácia nastavení upozornení
            alerts = get_setting("alerts", {})
            alerts["sound_enabled"] = self.alert_sound.active
            alerts["notification_type"] = self.notification_type.text
            alerts["retention_days"] = int(self.retention_days.text)
            update_setting("alerts", alerts)
            
            # Aktualizácia emailových nastavení
            notifications = get_setting("notifications", {})
            email_settings = notifications.get("email", {})
            email_settings["enabled"] = self.email_enabled.active
            email_settings["smtp_server"] = self.smtp_server.text
            email_settings["smtp_port"] = int(self.smtp_port.text)
            email_settings["username"] = self.email_username.text
            email_settings["password"] = self.email_password.text
            email_settings["from_email"] = self.from_email.text
            email_settings["to_email"] = self.to_email.text
            
            if "notifications" not in get_setting("", {}):
                update_setting("notifications", {})
            
            update_setting("notifications.email", email_settings)
            
            # Aktualizácia nastavení obrázkov
            images = get_setting("images", {})
            images["storage_path"] = self.storage_path.text
            images["retention_days"] = int(self.img_retention_days.text)
            images["quality"] = self.image_quality.text
            update_setting("images", images)
            
            # Aktualizácia systémových nastavení
            system = get_setting("system", {})
            system["auto_start"] = self.auto_start.active
            system["log_level"] = self.log_level.text
            system["config_format"] = self.config_format.text
            update_setting("system", system)
            
            # Uloženie všetkých nastavení
            save_settings()
            self.status_label.text = "Settings saved successfully!"
            print("DEBUG: Nastavenia úspešne uložené")
        except Exception as e:
            self.status_label.text = f"Error saving settings: {str(e)}"
            print(f"ERROR: Zlyhalo uloženie nastavení: {e}")
        
    def go_back(self, instance):
        """Navigate back to main screen"""
        self.go_to_screen('main')