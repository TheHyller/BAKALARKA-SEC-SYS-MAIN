from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.clock import Clock
from datetime import datetime
import time
from config.settings import get_sensor_devices, get_sensor_status, remove_sensor_device

class SensorCard(BoxLayout):
    """Widget pre zobrazenie jedného zariadenia senzora"""
    
    def __init__(self, device_id, device_data, **kwargs):
        super(SensorCard, self).__init__(**kwargs)
        self.device_id = device_id
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 150
        self.padding = 10
        self.spacing = 5
        
        # Pridanie okraja
        self.canvas.before.rgba = (0.8, 0.8, 0.8, 1)
        
        # Hlavička zariadenia
        header = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        self.device_name = Label(
            text=device_data.get('name', 'Unknown Device'),
            font_size=18,
            bold=True,
            size_hint_x=0.7
        )
        
        # Čas posledného videnia
        last_seen = device_data.get('last_seen', '')
        if last_seen:
            try:
                # Parsovanie ISO formátu dátumu a času
                dt = datetime.fromisoformat(last_seen)
                last_seen_text = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                last_seen_text = last_seen
        else:
            last_seen_text = "Unknown"
            
        self.last_seen_label = Label(
            text=f"Last seen: {last_seen_text}",
            font_size=12,
            size_hint_x=0.3
        )
        
        header.add_widget(self.device_name)
        header.add_widget(self.last_seen_label)
        
        # Informácie o zariadení
        info = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        ip_label = Label(
            text=f"IP: {device_data.get('ip', 'Unknown')}",
            font_size=14,
            size_hint_x=0.5
        )
        id_label = Label(
            text=f"ID: {device_id[:8]}...",
            font_size=14,
            size_hint_x=0.5
        )
        info.add_widget(ip_label)
        info.add_widget(id_label)
        
        # Oblasť stavu senzora
        self.status_area = GridLayout(cols=3, size_hint_y=0.4)
        
        # Pridanie widgetov do hlavného rozloženia
        self.add_widget(header)
        self.add_widget(info)
        self.add_widget(self.status_area)
    
    def update_status(self, sensor_status):
        """Aktualizácia zobrazenia stavu senzora"""
        self.status_area.clear_widgets()
        
        if not sensor_status:
            self.status_area.add_widget(Label(text="No sensor data available"))
            return
            
        for sensor_type, data in sensor_status.items():
            # Štítok typu senzora
            self.status_area.add_widget(Label(
                text=sensor_type.capitalize(),
                font_size=14
            ))
            
            # Štítok stavu s farbou podľa stavu
            status = data.get('status', 'Unknown')
            status_label = Label(text=status, font_size=14)
            
            if status in ['OPEN', 'DETECTED', 'TRIGGERED', 'ALARM']:
                status_label.color = (1, 0, 0, 1)  # Červená pre stavové upozornenia
            elif status in ['CLOSED', 'CLEAR', 'NORMAL']:
                status_label.color = (0, 1, 0, 1)  # Zelená pre normálne stavy
            
            self.status_area.add_widget(status_label)
            
            # Časová pečiatka
            timestamp = data.get('timestamp', 0)
            if isinstance(timestamp, (int, float)):
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            else:
                time_str = str(timestamp)
                
            self.status_area.add_widget(Label(
                text=time_str,
                font_size=12
            ))

class DashboardScreen(Screen):
    """Hlavná obrazovka dashboardu zobrazujúca všetky zariadenia senzorov"""
    
    def __init__(self, **kwargs):
        super(DashboardScreen, self).__init__(**kwargs)
        
        # Vytvorenie hlavného rozloženia
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Hlavička
        header = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        header.add_widget(Label(
            text="Security System Dashboard",
            font_size=24,
            bold=True,
            size_hint_x=0.7
        ))
        
        refresh_button = Button(
            text="Refresh",
            size_hint_x=0.15
        )
        refresh_button.bind(on_release=self.refresh_dashboard)
        
        back_button = Button(
            text="Back",
            size_hint_x=0.15
        )
        back_button.bind(on_release=self.go_back)
        
        header.add_widget(refresh_button)
        header.add_widget(back_button)
        
        # Oblasť senzorov (s posúvaním)
        scroll_view = ScrollView(size_hint_y=0.9)
        self.sensors_layout = GridLayout(
            cols=1, 
            spacing=10, 
            size_hint_y=None,
            padding=10
        )
        self.sensors_layout.bind(minimum_height=self.sensors_layout.setter('height'))
        
        scroll_view.add_widget(self.sensors_layout)
        
        # Pridanie widgetov do hlavného rozloženia
        layout.add_widget(header)
        layout.add_widget(scroll_view)
        
        self.add_widget(layout)
        
        # Uloženie kariet senzorov podľa ID zariadenia
        self.sensor_cards = {}
        
        # Naplánovanie pravidelných aktualizácií
        Clock.schedule_interval(self.update_dashboard, 5)  # Aktualizácia každých 5 sekúnd
    
    def on_enter(self):
        """Volá sa pri vstupe na obrazovku"""
        self.refresh_dashboard()
    
    def refresh_dashboard(self, *args):
        """Obnovenie dashboardu s aktuálnymi údajmi senzorov"""
        print("DEBUG: Obnovovanie dashboardu")
        
        # Získanie aktuálnych zariadení a stavov
        devices = get_sensor_devices()
        statuses = get_sensor_status()
        
        # Vyčistenie existujúcich widgetov, ak nie sú zariadenia
        if not devices:
            self.sensors_layout.clear_widgets()
            self.sensor_cards = {}
            no_sensors_label = Label(
                text="No sensor devices detected\nPlease make sure your sensors are powered on and connected to the network",
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=200
            )
            self.sensors_layout.add_widget(no_sensors_label)
            return
            
        # Odstránenie kariet pre zariadenia, ktoré už neexistujú
        to_remove = []
        for device_id in self.sensor_cards:
            if device_id not in devices:
                to_remove.append(device_id)
                
        for device_id in to_remove:
            if self.sensor_cards[device_id] in self.sensors_layout.children:
                self.sensors_layout.remove_widget(self.sensor_cards[device_id])
            del self.sensor_cards[device_id]
        
        # Aktualizácia alebo pridanie kariet pre každé zariadenie
        for device_id, device_data in devices.items():
            # Kontrola, či bolo zariadenie videné v poslednej hodine
            if 'last_seen' in device_data:
                try:
                    last_seen = datetime.fromisoformat(device_data['last_seen'])
                    now = datetime.now()
                    # Preskočenie zariadení, ktoré neboli videné v poslednej hodine
                    if (now - last_seen).total_seconds() > 3600:
                        if device_id in self.sensor_cards:
                            self.sensors_layout.remove_widget(self.sensor_cards[device_id])
                            del self.sensor_cards[device_id]
                        continue
                except (ValueError, TypeError):
                    pass
            
            if device_id in self.sensor_cards:
                # Aktualizácia existujúcej karty
                self.sensor_cards[device_id].update_status(statuses.get(device_id, {}))
            else:
                # Vytvorenie novej karty
                card = SensorCard(device_id, device_data)
                card.update_status(statuses.get(device_id, {}))
                self.sensor_cards[device_id] = card
                self.sensors_layout.add_widget(card)
    
    def update_dashboard(self, dt):
        """Aktualizácia dashboardu na časovači"""
        self.refresh_dashboard()
    
    def go_back(self, instance):
        """Návrat na hlavnú obrazovku"""
        self.manager.current = 'main'