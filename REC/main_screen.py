# Inicializácia balíka
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from config.settings import get_setting, validate_pin, update_pin, toggle_system_state
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
        
        # Stavový štítok
        self.status_label = Label(
            text="System Status: Inactive", 
            font_size=24,
            size_hint_y=0.2
        )
        
        # Rozloženie tlačidiel
        button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        
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
        
        button_layout.add_widget(self.toggle_button)
        button_layout.add_widget(self.change_pin_button)
        
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
        
        # Oblasť stavu senzorov (zjednodušená - teraz máme samostatný dashboard)
        sensor_layout = BoxLayout(orientation='vertical', size_hint_y=0.4)
        sensor_layout.add_widget(Label(text="Recent Activity:", font_size=18, size_hint_y=0.2))
        self.sensor_list = GridLayout(cols=1, spacing=5)
        sensor_layout.add_widget(self.sensor_list)
        
        # Pridanie widgetov do hlavného rozloženia
        layout.add_widget(self.status_label)
        layout.add_widget(button_layout)
        layout.add_widget(nav_layout)  # Pridanie navigačných tlačidiel
        layout.add_widget(sensor_layout)
        
        self.add_widget(layout)
        
        # Spustenie sieťových poslucháčov
        self.start_listeners()
        
        # Aktualizácia UI s aktuálnym stavom
        self.update_ui()
        
    def start_listeners(self):
        """Spustenie sieťových poslucháčov pre senzory"""
        self.tcp_listener = TCPListener()
        self.tcp_listener.add_callback(self.handle_sensor_data)
        self.tcp_listener.start()
        
        self.udp_listener = UDPListener()
        self.udp_listener.add_callback(self.handle_sensor_data)
        self.udp_listener.start()
        
        self.discovery_listener = DiscoveryListener()
        self.discovery_listener.add_callback(self.handle_discovery)
        self.discovery_listener.start()
        
    def handle_sensor_data(self, data, address):
        """Spracovanie dát prijatých zo senzorov"""
        print(f"DEBUG: Prijaté dáta zo senzora: {data} z {address}")
        # Parsovanie dát zo senzora a aktualizácia UI
        # Napríklad: "SENSOR:front_door:OPEN"
        Clock.schedule_once(lambda dt: self.update_sensor_ui(data, address), 0)
        
    def handle_discovery(self, data, address):
        """Spracovanie správ objavovania"""
        print(f"DEBUG: Prijatá správa objavovania: {data} z {address}")
        
    def update_sensor_ui(self, data, address):
        """Aktualizácia UI senzora s novými dátami"""
        # Príklad implementácie - bola by rozšírená v reálnej aplikácii
        try:
            sensor_label = Label(
                text=f"Sensor data: {data} from {address[0]}",
                font_size=16,
                halign='left'
            )
            self.sensor_list.add_widget(sensor_label)
        except Exception as e:
            print(f"ERROR: Zlyhala aktualizácia UI senzora: {e}")
        
    def update_ui(self):
        """Aktualizácia UI na základe aktuálneho stavu systému"""
        system_active = get_setting("system_active", False)
        
        if system_active:
            self.status_label.text = "System Status: ACTIVE"
            self.toggle_button.text = "Deactivate System"
        else:
            self.status_label.text = "System Status: INACTIVE"
            self.toggle_button.text = "Activate System"
            
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
    
    # Pridanie nových navigačných metód
    def open_dashboard(self, instance):
        """Otvorenie obrazovky dashboard senzorov"""
        self.manager.current = 'dashboard'
    
    def open_alerts(self, instance):
        """Otvorenie obrazovky histórie upozornení"""
        self.manager.current = 'alerts'
    
    def open_settings(self, instance):
        """Otvorenie obrazovky nastavení"""
        self.manager.current = 'settings'