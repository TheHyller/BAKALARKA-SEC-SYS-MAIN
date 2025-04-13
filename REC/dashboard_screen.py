from base_screen import BaseScreen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.carousel import Carousel
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from datetime import datetime, timedelta
import time
import os
from config.settings import get_sensor_devices, get_sensor_status, remove_sensor_device, get_setting

class SensorCard(BoxLayout):
    """Widget pre zobrazenie jedného zariadenia senzora"""
    
    def __init__(self, device_id, device_data, **kwargs):
        super(SensorCard, self).__init__(**kwargs)
        self.device_id = device_id
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 200
        self.padding = 10
        self.spacing = 5
        
        # Pridanie pozadia a okraja
        with self.canvas.before:
            Color(0.9, 0.9, 0.95, 1)  # Svetlosivé pozadie
            self.rect = Rectangle(pos=self.pos, size=self.size)
        
        # Keď sa zmení veľkosť widgetu, aktualizuj obdĺžnik
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Hlavička zariadenia
        header = BoxLayout(orientation='horizontal', size_hint_y=0.2)
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
        info = BoxLayout(orientation='horizontal', size_hint_y=0.15)
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
        sensor_status_layout = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        self.status_area = GridLayout(cols=3, spacing=5, size_hint_x=0.7)
        
        # Oblasť pre náhľad obrázka
        self.image_preview = BoxLayout(orientation='vertical', size_hint_x=0.3)
        self.preview_image = Image(
            source='',  # Zatiaľ žiadny obrázok
            size_hint=(1, 0.8),
            allow_stretch=True,
            keep_ratio=True
        )
        view_button = Button(
            text="View Images",
            size_hint=(1, 0.2),
            font_size=12
        )
        view_button.bind(on_release=lambda btn: self.view_device_images())
        
        self.image_preview.add_widget(self.preview_image)
        self.image_preview.add_widget(view_button)
        
        sensor_status_layout.add_widget(self.status_area)
        sensor_status_layout.add_widget(self.image_preview)
        
        # Tlačidlá pre zariadenie
        buttons = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=5)
        
        refresh_btn = Button(
            text="Refresh",
            size_hint_x=0.5
        )
        refresh_btn.bind(on_release=lambda btn: self.request_refresh())
        
        remove_btn = Button(
            text="Remove Device",
            size_hint_x=0.5
        )
        remove_btn.bind(on_release=lambda btn: self.confirm_remove_device())
        
        buttons.add_widget(refresh_btn)
        buttons.add_widget(remove_btn)
        
        # Pridanie widgetov do hlavného rozloženia
        self.add_widget(header)
        self.add_widget(info)
        self.add_widget(sensor_status_layout)
        self.add_widget(buttons)
        
        # Uchovanie callback pre obnovenie rodičovskej obrazovky
        self.refresh_callback = None
    
    def _update_rect(self, instance, value):
        """Aktualizácia obdĺžnika pri zmene veľkosti"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def update_status(self, sensor_status):
        """Aktualizácia zobrazenia stavu senzora"""
        self.status_area.clear_widgets()
        
        if not sensor_status:
            self.status_area.add_widget(Label(text="No sensor data available"))
            return
        
        # Načítanie najnovšieho obrázka
        self._update_preview_image()
            
        for sensor_type, data in sensor_status.items():
            # Štítok typu senzora
            self.status_area.add_widget(Label(
                text=sensor_type.capitalize(),
                font_size=14
            ))
            
            # Check if data is a dictionary or a string value
            status = "Unknown"
            if isinstance(data, dict):
                status = data.get('status', 'Unknown')
            else:
                # If data is a string, use it directly as the status
                status = str(data)
            
            # Štítok stavu s farbou podľa stavu
            status_label = Label(text=status, font_size=14)
            
            if status in ['OPEN', 'DETECTED', 'TRIGGERED', 'ALARM']:
                status_label.color = (1, 0, 0, 1)  # Červená pre stavové upozornenia
            elif status in ['CLOSED', 'CLEAR', 'NORMAL']:
                status_label.color = (0, 1, 0, 1)  # Zelená pre normálne stavy
            
            self.status_area.add_widget(status_label)
            
            # Časová pečiatka
            timestamp = 0
            if isinstance(data, dict):
                timestamp = data.get('timestamp', 0)
            
            if isinstance(timestamp, (int, float)):
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            else:
                time_str = str(timestamp)
                
            self.status_area.add_widget(Label(
                text=time_str,
                font_size=12
            ))
    
    def _update_preview_image(self):
        """Načítanie a zobrazenie najnovšieho obrázka zo zariadenia"""
        try:
            # Získanie cesty k obrázkam
            storage_path = get_setting("images.storage_path", "captures")
            
            # Ak nie je absolútna cesta, vytvor cestu relatívnu k projektu
            if not os.path.isabs(storage_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_path = os.path.join(base_dir, storage_path)
                
            # Kontrola, či adresár existuje
            if not os.path.exists(storage_path):
                return
                
            # Hľadanie najnovšieho obrázka pre toto zariadenie
            device_name = self.device_name.text.split(":")[0].strip() if ":" in self.device_name.text else self.device_name.text
            
            # Filter súborov podľa prefixu senzora
            matching_images = []
            
            for filename in os.listdir(storage_path):
                # Hľadáme súbory spájané s týmto zariadením podľa prefixu (motion_, door_, window_)
                if (filename.startswith(("motion_", "door_", "window_")) and 
                    filename.endswith(('.jpg', '.jpeg', '.png'))):
                    # Získanie úplnej cesty k súboru
                    filepath = os.path.join(storage_path, filename)
                    # Pridanie s časom vytvorenia súboru pre zoradenie
                    matching_images.append((filepath, os.path.getmtime(filepath)))
            
            # Zoradenie podľa času (najnovšie prvé)
            matching_images.sort(key=lambda x: x[1], reverse=True)
            
            # Zobrazenie najnovšieho obrázka, ak existuje
            if matching_images:
                self.preview_image.source = matching_images[0][0]
            
        except Exception as e:
            print(f"ERROR: Zlyhalo načítanie náhľadového obrázka: {e}")
            
    def view_device_images(self):
        """Zobrazenie všetkých obrázkov pre toto zariadenie"""
        try:
            # Získanie cesty k obrázkam
            storage_path = get_setting("images.storage_path", "captures")
            
            # Ak nie je absolútna cesta, vytvor cestu relatívnu k projektu
            if not os.path.isabs(storage_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_path = os.path.join(base_dir, storage_path)
                
            # Kontrola, či adresár existuje
            if not os.path.exists(storage_path):
                os.makedirs(storage_path, exist_ok=True)
                self._show_error_popup("No images found for this device")
                return
                
            # Hľadanie obrázkov pre toto zariadenie
            matching_images = []
            
            for filename in os.listdir(storage_path):
                # Hľadáme súbory spájané s týmto zariadením podľa typu senzora
                if (filename.startswith(("motion_", "door_", "window_")) and 
                    filename.endswith(('.jpg', '.jpeg', '.png'))):
                    # Získanie úplnej cesty k súboru
                    filepath = os.path.join(storage_path, filename)
                    # Pridanie s časom vytvorenia súboru pre zoradenie
                    matching_images.append((filepath, os.path.getmtime(filepath)))
            
            # Zoradenie podľa času (najnovšie prvé)
            matching_images.sort(key=lambda x: x[1], reverse=True)
            
            if not matching_images:
                self._show_error_popup("No images found for this device")
                return
                
            # Zobrazenie obrázkov v carousel popup
            self._show_images_carousel([img[0] for img in matching_images])
            
        except Exception as e:
            print(f"ERROR: Zlyhalo zobrazenie obrázkov: {e}")
            self._show_error_popup(f"Error loading images: {str(e)}")
            
    def _show_images_carousel(self, image_paths):
        """Zobrazenie obrázkov v karuseli (slideshow)"""
        # Vytvorenie obsahu popup
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Vytvorenie karuselu
        carousel = Carousel(direction='right', size_hint_y=0.9)
        
        for img_path in image_paths:
            img_container = BoxLayout(orientation='vertical')
            img = Image(
                source=img_path,
                allow_stretch=True,
                keep_ratio=True,
                size_hint_y=0.9
            )
            img_container.add_widget(img)
            
            # Pridanie menovky s názvom súboru a dátumom
            filename = os.path.basename(img_path)
            file_time = datetime.fromtimestamp(os.path.getmtime(img_path)).strftime("%Y-%m-%d %H:%M:%S")
            img_container.add_widget(Label(
                text=f"{filename} - {file_time}",
                size_hint_y=0.1
            ))
            
            carousel.add_widget(img_container)
        
        content.add_widget(carousel)
        
        # Tlačidlo na zatvorenie
        close_button = Button(
            text="Close",
            size_hint_y=0.1
        )
        content.add_widget(close_button)
        
        # Vytvorenie a zobrazenie popup
        popup = Popup(
            title=f"Images from {self.device_name.text}",
            content=content,
            size_hint=(0.9, 0.9)
        )
        
        close_button.bind(on_release=popup.dismiss)
        popup.open()
    
    def _show_error_popup(self, message):
        """Zobrazenie chybového hlásenia"""
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        
        button = Button(text="Close", size_hint_y=0.3)
        content.add_widget(button)
        
        popup = Popup(
            title="Error",
            content=content,
            size_hint=(0.7, 0.4)
        )
        
        button.bind(on_release=popup.dismiss)
        popup.open()
    
    def confirm_remove_device(self):
        """Potvrdenie pred odstránením zariadenia"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        content.add_widget(Label(
            text=f"Are you sure you want to remove device {self.device_name.text}?",
            halign='center'
        ))
        
        buttons = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.4)
        
        cancel_btn = Button(text="Cancel")
        remove_btn = Button(text="Remove")
        
        buttons.add_widget(cancel_btn)
        buttons.add_widget(remove_btn)
        content.add_widget(buttons)
        
        popup = Popup(
            title="Confirm Device Removal",
            content=content,
            size_hint=(0.7, 0.4),
            auto_dismiss=True
        )
        
        cancel_btn.bind(on_release=popup.dismiss)
        remove_btn.bind(on_release=lambda btn: self.remove_device(popup))
        
        popup.open()
    
    def remove_device(self, popup):
        """Odstránenie zariadenia zo systému"""
        popup.dismiss()
        
        # Odstránenie zariadenia z konfigurácie
        success = remove_sensor_device(self.device_id)
        
        if success and self.refresh_callback:
            self.refresh_callback()
    
    def request_refresh(self):
        """Volanie callback funkcie na obnovenie stavu"""
        if self.refresh_callback:
            self.refresh_callback()

class DashboardScreen(BaseScreen):
    """Hlavná obrazovka dashboardu zobrazujúca všetky zariadenia senzorov"""
    
    def __init__(self, **kwargs):
        super(DashboardScreen, self).__init__(**kwargs)
        
        # Nastavenie titulku
        self.set_title("Security System Dashboard")
        
        # Pridanie tlačidla späť do hlavičky
        back_button = Button(
            text="Back",
            size_hint_x=0.15
        )
        back_button.bind(on_release=self.go_back)
        self.header.add_widget(back_button)
        
        # Vytvorenie oblasti obsahu
        content_area = self.create_content_area()
        
        # Vytvorenie tlačidla na obnovenie v hornej časti obsahu
        refresh_button = Button(
            text="Refresh Dashboard",
            size_hint_y=0.05
        )
        refresh_button.bind(on_release=self.refresh_dashboard)
        content_area.add_widget(refresh_button)
        
        # Oblasť senzorov (s posúvaním)
        scroll_view = ScrollView(size_hint_y=0.95)
        self.sensors_layout = GridLayout(
            cols=1, 
            spacing=10, 
            size_hint_y=None,
            padding=10
        )
        self.sensors_layout.bind(minimum_height=self.sensors_layout.setter('height'))
        
        scroll_view.add_widget(self.sensors_layout)
        content_area.add_widget(scroll_view)
                
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
                card.refresh_callback = self.refresh_dashboard
                card.update_status(statuses.get(device_id, {}))
                self.sensor_cards[device_id] = card
                self.sensors_layout.add_widget(card)
    
    def update_dashboard(self, dt):
        """Aktualizácia dashboardu na časovači"""
        self.refresh_dashboard()
    
    def go_back(self, instance):
        """Návrat na hlavnú obrazovku"""
        self.manager.current = 'main'