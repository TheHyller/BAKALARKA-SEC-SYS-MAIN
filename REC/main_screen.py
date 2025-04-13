# Inicializácia balíka
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.clock import Clock
from datetime import datetime
import os
from config.settings import get_setting, validate_pin, update_pin, toggle_system_state, get_alerts, get_sensor_devices, get_sensor_status
from listeners import TCPListener, UDPListener, DiscoveryListener

class NumericKeypad(GridLayout):
    def __init__(self, callback, **kwargs):
        super(NumericKeypad, self).__init__(**kwargs)
        self.cols = 3
        self.spacing = [10, 10]
        self.padding = [20, 20, 20, 20]
        self.callback = callback
        self.pin_input = ""
        
        # Vytvorenie textového displeja
        self.display = TextInput(multiline=False, readonly=True, halign="center", font_size=24, password=True)
        self.add_widget(BoxLayout(height=50))  # Medzerník
        self.add_widget(self.display)
        self.add_widget(BoxLayout(height=50))  # Medzerník
        
        # Vytvorenie tlačidiel s číslami
        for i in range(1, 10):
            btn = Button(text=str(i), font_size=24)
            btn.bind(on_release=self.on_button_press)
            self.add_widget(btn)
            
        # Pridanie tlačidiel vymazať, 0 a potvrdiť
        btn_clear = Button(text="Clear", font_size=20)
        btn_clear.bind(on_release=self.on_clear)
        self.add_widget(btn_clear)
        
        btn_0 = Button(text="0", font_size=24)
        btn_0.bind(on_release=self.on_button_press)
        self.add_widget(btn_0)
        
        btn_enter = Button(text="Enter", font_size=20)
        btn_enter.bind(on_release=self.on_enter)
        self.add_widget(btn_enter)
        
    def on_button_press(self, instance):
        self.pin_input += instance.text
        self.display.text = "*" * len(self.pin_input)
        
    def on_clear(self, instance):
        self.pin_input = ""
        self.display.text = ""
        
    def on_enter(self, instance):
        self.callback(self.pin_input)
        
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        
        # Vytvorenie hlavného rozloženia
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Logo a názov aplikácie
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15)
        
        # Logo - use our created logo
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               "assets", "security_logo.png")
        logo = Image(
            source=logo_path,
            size_hint_x=0.3
        )
        
        # Názov a stavový štítok
        title_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        title_layout.add_widget(Label(
            text="Home Security System", 
            font_size=28,
            bold=True,
            size_hint_y=0.6
        ))
        
        self.status_label = Label(
            text="System Status: Inactive", 
            font_size=18,
            size_hint_y=0.4
        )
        title_layout.add_widget(self.status_label)
        
        header_layout.add_widget(logo)
        header_layout.add_widget(title_layout)
        layout.add_widget(header_layout)
        
        # Súhrn zariadení
        devices_summary = BoxLayout(orientation='vertical', size_hint_y=0.2)
        devices_summary.add_widget(Label(
            text="Connected Devices",
            font_size=18,
            bold=True,
            size_hint_y=0.3
        ))
        
        self.devices_grid = GridLayout(cols=3, spacing=5, size_hint_y=0.7)
        self.update_devices_summary()
        devices_summary.add_widget(self.devices_grid)
        layout.add_widget(devices_summary)
        
        # Posledné upozornenia
        alerts_summary = BoxLayout(orientation='vertical', size_hint_y=0.3)
        alerts_summary.add_widget(Label(
            text="Recent Alerts",
            font_size=18,
            bold=True,
            size_hint_y=0.2
        ))
        
        self.alerts_list = GridLayout(cols=1, spacing=5, size_hint_y=0.8)
        self.update_alerts_summary()
        alerts_summary.add_widget(self.alerts_list)
        layout.add_widget(alerts_summary)
        
        # Rozloženie tlačidiel
        buttons_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.15)
        
        self.toggle_button = Button(
            text="Activate System",
            font_size=20
        )
        self.toggle_button.bind(on_release=self.toggle_system)
        
        self.change_pin_button = Button(
            text="Change PIN",
            font_size=20
        )
        self.change_pin_button.bind(on_release=self.show_change_pin)
        
        buttons_layout.add_widget(self.toggle_button)
        buttons_layout.add_widget(self.change_pin_button)
        layout.add_widget(buttons_layout)
        
        # Pridanie navigačných tlačidiel
        nav_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        
        dashboard_button = Button(
            text="Sensor Dashboard",
            font_size=20
        )
        dashboard_button.bind(on_release=self.open_dashboard)
        
        alerts_button = Button(
            text="Alerts History",
            font_size=20
        )
        alerts_button.bind(on_release=self.open_alerts)
        
        settings_button = Button(
            text="Settings",
            font_size=20
        )
        settings_button.bind(on_release=self.open_settings)
        
        nav_layout.add_widget(dashboard_button)
        nav_layout.add_widget(alerts_button)
        nav_layout.add_widget(settings_button)
        layout.add_widget(nav_layout)
        
        self.add_widget(layout)
        
        # Naplánuj pravidelné aktualizácie
        Clock.schedule_interval(self.update_ui, 5)  # Každých 5 sekúnd
        
    def on_enter(self):
        """Volaná pri vstupe na obrazovku"""
        self.update_ui()
        
    def update_devices_summary(self):
        """Aktualizácia súhrnu pripojených zariadení"""
        self.devices_grid.clear_widgets()
        
        devices = get_sensor_devices()
        
        if not devices:
            self.devices_grid.add_widget(Label(
                text="No devices connected",
                font_size=16,
                size_hint_x=1,
                halign='center'
            ))
            return
        
        # Zobrazenie súhrnu zariadení
        total_devices = len(devices)
        active_devices = 0
        
        # Zistenie počtu aktívnych zariadení
        now = datetime.now()
        for device_id, device_data in devices.items():
            if 'last_seen' in device_data:
                try:
                    last_seen = datetime.fromisoformat(device_data['last_seen'])
                    if (now - last_seen).total_seconds() < 3600:  # Aktívne v poslednej hodine
                        active_devices += 1
                except (ValueError, TypeError):
                    pass
                    
        # Prvý stĺpec - Celkový počet
        self.devices_grid.add_widget(Label(
            text=f"Total: {total_devices}",
            font_size=16
        ))
        
        # Druhý stĺpec - Aktívne
        self.devices_grid.add_widget(Label(
            text=f"Active: {active_devices}",
            font_size=16,
            color=(0, 1, 0, 1) if active_devices > 0 else (1, 0, 0, 1)
        ))
        
        # Tretí stĺpec - Indikátor stavu
        status_text = "All Online" if active_devices == total_devices else "Some Offline"
        status_color = (0, 1, 0, 1) if active_devices == total_devices else (1, 0.7, 0, 1)
        
        self.devices_grid.add_widget(Label(
            text=status_text,
            font_size=16,
            color=status_color
        ))
        
    def update_alerts_summary(self):
        """Aktualizácia súhrnu posledných upozornení"""
        self.alerts_list.clear_widgets()
        
        # Načítanie posledných 3 upozornení
        alerts = get_alerts(3)
        
        if not alerts:
            self.alerts_list.add_widget(Label(
                text="No recent alerts",
                font_size=16
            ))
            return
            
        # Zobrazenie upozornení
        for alert in alerts:
            device_name = alert.get('device_name', 'Unknown Device')
            sensor_type = alert.get('sensor_type', 'unknown').capitalize()
            status = alert.get('status', 'UNKNOWN')
            timestamp = alert.get('timestamp', 0)
            
            # Formátovanie časovej pečiatky
            if isinstance(timestamp, (int, float)):
                time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = str(timestamp)
                
            # Vytvorenie štítku upozornenia
            alert_text = f"{time_str} - {device_name}: {sensor_type} {status}"
            alert_label = Label(
                text=alert_text,
                font_size=14,
                halign='left'
            )
            alert_label.bind(size=lambda s, w: setattr(s, 'text_size', w))
            
            self.alerts_list.add_widget(alert_label)
        
    def update_ui(self, *args):
        """Aktualizácia UI na základe aktuálneho stavu systému"""
        system_active = get_setting("system_active", False)
        
        if system_active:
            self.status_label.text = "System Status: ACTIVE"
            self.status_label.color = (0, 1, 0, 1)  # Zelená pre aktívny stav
            self.toggle_button.text = "Deactivate System"
            self.toggle_button.background_color = (1, 0.5, 0.5, 1)  # Červená pre deaktiváciu
        else:
            self.status_label.text = "System Status: INACTIVE"
            self.status_label.color = (1, 0, 0, 1)  # Červená pre neaktívny stav
            self.toggle_button.text = "Activate System"
            self.toggle_button.background_color = (0.5, 1, 0.5, 1)  # Zelená pre aktiváciu
            
        # Aktualizácia súhrnu zariadení a upozornení
        self.update_devices_summary()
        self.update_alerts_summary()
        
        print(f"DEBUG: UI aktualizované, systém aktívny: {system_active}")
        
    def toggle_system(self, instance):
        """Zobrazenie PIN dialógu na prepnutie stavu systému"""
        self.pin_popup = Popup(
            title='Enter PIN',
            size_hint=(0.8, 0.8),
            auto_dismiss=True
        )
        
        keypad = NumericKeypad(self.validate_toggle_pin)
        self.pin_popup.content = keypad
        self.pin_popup.open()
        
    def validate_toggle_pin(self, pin_input):
        """Overenie PIN-u a prepnutie systému, ak je správny"""
        if validate_pin(pin_input):
            print("DEBUG: PIN úspešne overený")
            self.pin_popup.dismiss()
            
            # Prepnutie stavu systému
            toggled = toggle_system_state()
            print(f"DEBUG: Stav systému prepnutý: {toggled}")
            
            # Aktualizácia UI
            self.update_ui()
        else:
            print(f"DEBUG: Zadaný neplatný PIN: {pin_input}")
            self.pin_popup.dismiss()
            
            # Zobrazenie chybového okna
            error_popup = Popup(
                title='Error',
                content=Label(text='Invalid PIN'),
                size_hint=(0.5, 0.3)
            )
            error_popup.open()
            
    def show_change_pin(self, instance):
        """Zobrazenie dialógu na zmenu PIN-u"""
        self.pin_popup = Popup(
            title='Enter Current PIN',
            size_hint=(0.8, 0.8),
            auto_dismiss=True
        )
        
        keypad = NumericKeypad(self.validate_current_pin)
        self.pin_popup.content = keypad
        self.pin_popup.open()
        
    def validate_current_pin(self, pin_input):
        """Overenie aktuálneho PIN-u pred povolením zmeny"""
        if validate_pin(pin_input):
            print("DEBUG: Aktuálny PIN overený, zobrazujem dialóg nového PIN-u")
            self.pin_popup.dismiss()
            
            # Zobrazenie dialógu nového PIN-u
            self.new_pin_popup = Popup(
                title='Enter New PIN',
                size_hint=(0.8, 0.8),
                auto_dismiss=True
            )
            
            keypad = NumericKeypad(self.set_new_pin)
            self.new_pin_popup.content = keypad
            self.new_pin_popup.open()
        else:
            print(f"DEBUG: Zadaný neplatný aktuálny PIN: {pin_input}")
            self.pin_popup.dismiss()
            
            # Zobrazenie chybového okna
            error_popup = Popup(
                title='Error',
                content=Label(text='Invalid PIN'),
                size_hint=(0.5, 0.3)
            )
            error_popup.open()
            
    def set_new_pin(self, new_pin):
        """Nastavenie nového PIN-u"""
        if len(new_pin) >= 4:
            print(f"DEBUG: Nastavenie nového PIN-u: {len(new_pin) * '*'}")
            success = update_pin(new_pin)
            
            self.new_pin_popup.dismiss()
            
            # Zobrazenie potvrdzovacieho okna
            message = 'PIN updated successfully' if success else 'Failed to update PIN'
            confirm_popup = Popup(
                title='PIN Change',
                content=Label(text=message),
                size_hint=(0.5, 0.3)
            )
            confirm_popup.open()
        else:
            print("DEBUG: Nový PIN je príliš krátky")
            self.new_pin_popup.dismiss()
            
            # Zobrazenie chybového okna
            error_popup = Popup(
                title='Error',
                content=Label(text='PIN must be at least 4 digits'),
                size_hint=(0.5, 0.3)
            )
            error_popup.open()
    
    # Navigačné metódy
    def open_dashboard(self, instance):
        """Otvorenie obrazovky dashboard senzorov"""
        self.manager.current = 'dashboard'
    
    def open_alerts(self, instance):
        """Otvorenie obrazovky histórie upozornení"""
        self.manager.current = 'alerts'
    
    def open_settings(self, instance):
        """Otvorenie obrazovky nastavení"""
        self.manager.current = 'settings'