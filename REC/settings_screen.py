from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
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
        network_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.4)
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
        
        # Pridanie ďalších nastavení podľa potreby
        
        layout.add_widget(form_layout)
        
        # Tlačidlá
        button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        
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
            
            # Uloženie všetkých nastavení
            save_settings()
            print("DEBUG: Nastavenia úspešne uložené")
        except Exception as e:
            print(f"ERROR: Zlyhalo uloženie nastavení: {e}")
        
    def go_back(self, instance):
        """Návrat na hlavnú obrazovku"""
        self.manager.current = 'main'