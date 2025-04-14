# Inicializácia balíka
from base_screen import BaseScreen
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
from network import network_manager

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
        btn_clear = Button(text="Vymazať", font_size=20)
        btn_clear.bind(on_release=self.on_clear)
        self.add_widget(btn_clear)
        
        btn_0 = Button(text="0", font_size=24)
        btn_0.bind(on_release=self.on_button_press)
        self.add_widget(btn_0)
        
        btn_enter = Button(text="Potvrdiť", font_size=20)
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
        
class MainScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        
        # Nastavenie titulku
        self.set_title("Bezpečnostný systém domácnosti")
        
        # Upravenie hlavičky - pridanie stavového štítku
        self.status_label = Label(
            text="Stav systému: Neaktívny", 
            font_size=18,
            size_hint_y=0.4
        )
        self.header.add_widget(self.status_label)
        
        # Vytvorenie oblasti obsahu
        content_area = self.create_content_area()
        
        # Súhrn zariadení
        devices_summary = BoxLayout(orientation='vertical', size_hint_y=0.3)
        devices_summary.add_widget(Label(
            text="Pripojené zariadenia",
            font_size=18,
            bold=True,
            size_hint_y=0.3
        ))
        
        self.devices_grid = GridLayout(cols=3, spacing=5, size_hint_y=0.7)
        self.update_devices_summary()
        devices_summary.add_widget(self.devices_grid)
        content_area.add_widget(devices_summary)
        
        # Posledné upozornenia
        alerts_summary = BoxLayout(orientation='vertical', size_hint_y=0.5)
        alerts_summary.add_widget(Label(
            text="Nedávne upozornenia",
            font_size=18,
            bold=True,
            size_hint_y=0.2
        ))
        
        self.alerts_list = GridLayout(cols=1, spacing=5, size_hint_y=0.8)
        self.update_alerts_summary()
        alerts_summary.add_widget(self.alerts_list)
        content_area.add_widget(alerts_summary)
        
        # Vytvorenie päty (footer)
        footer = self.create_footer()
        
        # Rozloženie do dvoch riadkov, použitím GridLayout
        footer_grid = GridLayout(cols=1, rows=2, spacing=10)
        footer.add_widget(footer_grid)
        
        # Rozloženie tlačidiel - prvý riadok
        buttons_layout = GridLayout(cols=2, spacing=10)
        
        self.toggle_button = Button(
            text="Aktivovať systém",
            font_size=20
        )
        self.toggle_button.bind(on_release=self.toggle_system)
        
        self.change_pin_button = Button(
            text="Zmeniť PIN",
            font_size=20
        )
        self.change_pin_button.bind(on_release=self.show_change_pin)
        
        buttons_layout.add_widget(self.toggle_button)
        buttons_layout.add_widget(self.change_pin_button)
        footer_grid.add_widget(buttons_layout)
        
        # Pridanie navigačných tlačidiel - druhý riadok
        nav_layout = GridLayout(cols=3, spacing=10)
        
        dashboard_button = Button(
            text="Dashboard senzorov",
            font_size=20
        )
        dashboard_button.bind(on_release=self.open_dashboard)
        
        alerts_button = Button(
            text="História upozornení",
            font_size=20
        )
        alerts_button.bind(on_release=self.open_alerts)
        
        settings_button = Button(
            text="Nastavenia",
            font_size=20
        )
        settings_button.bind(on_release=self.open_settings)
        
        nav_layout.add_widget(dashboard_button)
        nav_layout.add_widget(alerts_button)
        nav_layout.add_widget(settings_button)
        
        footer_grid.add_widget(nav_layout)
        
        # Track grace period popup
        self.grace_period_popup = None
        
        # Naplánuj pravidelné aktualizácie
        Clock.schedule_interval(self.update_ui, 5)  # Každých 5 sekúnd
        
        # More frequent checks for grace period status
        Clock.schedule_interval(self.check_grace_period, 1)  # Check every second
        
    def on_enter(self):
        """Volaná pri vstupe na obrazovku"""
        self.update_ui()
        
    def update_devices_summary(self):
        """Aktualizácia súhrnu pripojených zariadení"""
        self.devices_grid.clear_widgets()
        
        devices = get_sensor_devices()
        
        if not devices:
            self.devices_grid.add_widget(Label(
                text="Žiadne pripojené zariadenia",
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
            text=f"Celkovo: {total_devices}",
            font_size=16
        ))
        
        # Druhý stĺpec - Aktívne
        self.devices_grid.add_widget(Label(
            text=f"Aktívne: {active_devices}",
            font_size=16,
            color=(0, 1, 0, 1) if active_devices > 0 else (1, 0, 0, 1)
        ))
        
        # Tretí stĺpec - Indikátor stavu
        status_text = "Všetky online" if active_devices == total_devices else "Niektoré offline"
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
                text="Žiadne nedávne upozornenia",
                font_size=16
            ))
            return
            
        # Zobrazenie upozornení
        for alert in alerts:
            device_name = alert.get('device_name', 'Neznáme zariadenie')
            sensor_type = alert.get('sensor_type', 'neznámy').capitalize()
            status = alert.get('status', 'NEZNÁMY')
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
            self.status_label.text = "Stav systému: AKTÍVNY"
            self.status_label.color = (0, 1, 0, 1)  # Zelená pre aktívny stav
            self.toggle_button.text = "Deaktivovať systém"
            self.toggle_button.background_color = (1, 0.5, 0.5, 1)  # Červená pre deaktiváciu
        else:
            self.status_label.text = "Stav systému: NEAKTÍVNY"
            self.status_label.color = (1, 0, 0, 1)  # Červená pre neaktívny stav
            self.toggle_button.text = "Aktivovať systém"
            self.toggle_button.background_color = (0.5, 1, 0.5, 1)  # Zelená pre aktiváciu
            
        # Aktualizácia súhrnu zariadení a upozornení
        self.update_devices_summary()
        self.update_alerts_summary()
        
        print(f"DEBUG: UI aktualizované, systém aktívny: {system_active}")
        
    def toggle_system(self, instance):
        """Zobrazenie PIN dialógu na prepnutie stavu systému"""
        self.pin_popup = Popup(
            title='Zadajte PIN',
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
                title='Chyba',
                content=Label(text='Neplatný PIN'),
                size_hint=(0.5, 0.3)
            )
            error_popup.open()
            
    def show_change_pin(self, instance):
        """Zobrazenie dialógu na zmenu PIN-u"""
        self.pin_popup = Popup(
            title='Zadajte aktuálny PIN',
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
                title='Zadajte nový PIN',
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
                title='Chyba',
                content=Label(text='Neplatný PIN'),
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
            message = 'PIN úspešne aktualizovaný' if success else 'Zlyhala aktualizácia PIN'
            confirm_popup = Popup(
                title='Zmena PIN',
                content=Label(text=message),
                size_hint=(0.5, 0.3)
            )
            confirm_popup.open()
        else:
            print("DEBUG: Nový PIN je príliš krátky")
            self.new_pin_popup.dismiss()
            
            # Zobrazenie chybového okna
            error_popup = Popup(
                title='Chyba',
                content=Label(text='PIN musí mať aspoň 4 číslice'),
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
    
    def check_grace_period(self, dt):
        """Kontrola, či existuje aktívna ochranná doba a zobrazenie upozornenia v prípade potreby"""
        # Import notification service tu, aby sa predišlo cyklickým importom
        from notification_service import notification_service
        
        # Získanie aktuálneho stavu ochrannej doby
        grace_status = notification_service.get_grace_period_status()
        
        # Ak existuje aktívna ochranná doba a momentálne nie je zobrazené žiadne vyskakovacie okno
        if grace_status and grace_status.get('active') and not self.grace_period_popup:
            # Získanie dát upozornenia z ochrannej doby
            alert_data = grace_status.get('alert_data')
            if alert_data:
                # Import triedy GracePeriodAlert z alerts_screen
                from alerts_screen import GracePeriodAlert
                
                # Vytvorenie a zobrazenie vyskakovacieho okna ochrannej doby
                self.grace_period_popup = GracePeriodAlert(alert_data, grace_seconds=30)
                self.grace_period_popup.bind(on_dismiss=self.on_grace_period_popup_closed)
                self.grace_period_popup.open()
                print("DEBUG: Zobrazujem vyskakovacie okno ochrannej doby")
        # Ak vyskakovacie okno existuje, ale systém bol deaktivovaný, zatvorí ho
        elif self.grace_period_popup and not get_setting("system_active", False):
            self.grace_period_popup.dismiss()
            self.grace_period_popup = None
            print("DEBUG: Vyskakovacie okno ochrannej doby zatvorené, pretože systém bol deaktivovaný")
    
    def on_grace_period_popup_closed(self, instance):
        """Volaná pri zatvorení vyskakovacieho okna ochrannej doby"""
        self.grace_period_popup = None
        print("DEBUG: Vyskakovacie okno ochrannej doby zatvorené")