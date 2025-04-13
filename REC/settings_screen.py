from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
# Zmena relatívneho importu na absolútny import
from config.settings import get_setting, update_setting, save_settings

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Nadpis
        layout.add_widget(Label(
            text="System Settings",
            font_size=24,
            size_hint_y=0.1
        ))
        
        # Formulár nastavení
        form_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.7)
        
        # Sieťové nastavenia
        network_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.25)
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
        
        # Alert Settings
        alert_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.25)
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
        image_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.25)
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
        system_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.25)
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
        
        layout.add_widget(form_layout)
        
        # Status message
        self.status_label = Label(
            text="",
            font_size=16,
            size_hint_y=0.1
        )
        layout.add_widget(self.status_label)
        
        # Tlačidlá
        button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.1)
        
        save_button = Button(text="Save Settings")
        save_button.bind(on_release=self.save_settings)
        button_layout.add_widget(save_button)
        
        back_button = Button(text="Back")
        back_button.bind(on_release=self.go_back)
        button_layout.add_widget(back_button)
        
        layout.add_widget(button_layout)
        
        self.add_widget(layout)
        
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
        """Návrat na hlavnú obrazovku"""
        self.manager.current = 'main'