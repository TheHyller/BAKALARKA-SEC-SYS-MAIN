from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.clock import Clock
from datetime import datetime
import os
from config.settings import get_alerts, mark_alert_as_read, get_setting

class AlertsScreen(Screen):
    def __init__(self, **kwargs):
        super(AlertsScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Nadpis
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        header_layout.add_widget(Label(
            text="System Alerts",
            font_size=24,
            size_hint_x=0.7
        ))
        
        # Tlačidlo na obnovenie
        refresh_button = Button(
            text="Refresh",
            size_hint_x=0.3
        )
        refresh_button.bind(on_release=self.refresh_alerts)
        header_layout.add_widget(refresh_button)
        
        layout.add_widget(header_layout)
        
        # Zoznam upozornení
        scroll_view = ScrollView(size_hint_y=0.7)
        self.alerts_list = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.alerts_list.bind(minimum_height=self.alerts_list.setter('height'))
        scroll_view.add_widget(self.alerts_list)
        layout.add_widget(scroll_view)
        
        # Štatistiky upozornení
        self.stats_label = Label(
            text="Total alerts: 0 | Unread: 0",
            font_size=16,
            size_hint_y=0.1
        )
        layout.add_widget(self.stats_label)
        
        # Tlačidlá
        buttons_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.1)
        
        back_button = Button(
            text="Back to Main"
        )
        back_button.bind(on_release=self.go_back)
        
        clear_button = Button(
            text="Mark All Read"
        )
        clear_button.bind(on_release=self.mark_all_read)
        
        buttons_layout.add_widget(back_button)
        buttons_layout.add_widget(clear_button)
        layout.add_widget(buttons_layout)
        
        self.add_widget(layout)
        
        # Naplánuj automatické obnovovanie
        Clock.schedule_interval(self.refresh_alerts, 30)  # Obnovenie každých 30 sekúnd
        
    def on_enter(self):
        """Volaná pri vstupe na obrazovku"""
        self.refresh_alerts()
        
    def refresh_alerts(self, *args):
        """Načítanie a zobrazenie upozornení zo systému"""
        self.alerts_list.clear_widgets()
        
        # Načítanie upozornení z databázy
        alerts = get_alerts()
        
        if not alerts:
            self.alerts_list.add_widget(Label(
                text="No alerts to display",
                font_size=18,
                size_hint_y=None,
                height=80
            ))
            self.stats_label.text = "Total alerts: 0 | Unread: 0"
            return
        
        # Počítanie neprečítaných upozornení
        unread_count = sum(1 for a in alerts if not a.get('read', False))
        
        # Aktualizácia štatistiky
        self.stats_label.text = f"Total alerts: {len(alerts)} | Unread: {unread_count}"
        
        # Pridanie upozornení do zoznamu
        for i, alert in enumerate(alerts):
            self.add_alert_to_ui(i, alert)
            
    def add_alert_to_ui(self, index, alert):
        """Pridanie upozornenia do používateľského rozhrania"""
        # Extrahovanie dát
        device_name = alert.get('device_name', 'Unknown Device')
        sensor_type = alert.get('sensor_type', 'unknown').capitalize()
        status = alert.get('status', 'UNKNOWN')
        timestamp = alert.get('timestamp', 0)
        is_read = alert.get('read', False)
        
        # Formátovanie časovej pečiatky
        if isinstance(timestamp, (int, float)):
            time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_str = str(timestamp)
        
        # Vytvorenie boxu pre upozornenie
        alert_box = BoxLayout(
            orientation='vertical', 
            size_hint_y=None, 
            height=120,
            padding=10,
            spacing=5
        )
        
        # Pridanie orámčekovania a farby pozadia pre neprečítané upozornenia
        if not is_read:
            from kivy.graphics import Color, Rectangle
            with alert_box.canvas.before:
                Color(0.9, 0.9, 1, 1)  # Svetlomodrá pre neprečítané
                Rectangle(pos=alert_box.pos, size=alert_box.size)
                
        # Horný riadok: Názov zariadenia a časová pečiatka
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        device_label = Label(
            text=f"Device: {device_name}",
            font_size=16,
            bold=True,
            halign='left',
            size_hint_x=0.6
        )
        device_label.bind(size=lambda s, w: setattr(s, 'text_size', w))
        
        time_label = Label(
            text=time_str,
            font_size=14,
            halign='right',
            size_hint_x=0.4
        )
        time_label.bind(size=lambda s, w: setattr(s, 'text_size', w))
        
        header_layout.add_widget(device_label)
        header_layout.add_widget(time_label)
        alert_box.add_widget(header_layout)
        
        # Hlavná správa
        message = f"{sensor_type} sensor {status}"
        message_label = Label(
            text=message,
            font_size=18,
            halign='left',
            size_hint_y=0.4
        )
        message_label.bind(size=lambda s, w: setattr(s, 'text_size', w))
        alert_box.add_widget(message_label)
        
        # Tlačidlá
        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=5)
        
        view_images_btn = Button(
            text="View Images",
            size_hint_x=0.5
        )
        view_images_btn.index = index  # Uloženie indexu pre callback
        view_images_btn.bind(on_release=self.view_alert_images)
        
        mark_read_btn = Button(
            text="Mark as Read" if not is_read else "Already Read",
            size_hint_x=0.5,
            disabled=is_read
        )
        mark_read_btn.index = index  # Uloženie indexu pre callback
        mark_read_btn.bind(on_release=self.mark_alert_read)
        
        buttons_layout.add_widget(view_images_btn)
        buttons_layout.add_widget(mark_read_btn)
        alert_box.add_widget(buttons_layout)
        
        # Pridanie do zoznamu
        self.alerts_list.add_widget(alert_box)
        
    def mark_alert_read(self, instance):
        """Označí upozornenie ako prečítané"""
        if hasattr(instance, 'index'):
            success = mark_alert_as_read(instance.index)
            if success:
                self.refresh_alerts()
                
    def mark_all_read(self, instance):
        """Označí všetky upozornenia ako prečítané"""
        alerts = get_alerts()
        for i in range(len(alerts)):
            mark_alert_as_read(i)
        self.refresh_alerts()
        
    def view_alert_images(self, instance):
        """Zobrazenie obrázkov spojených s upozornením"""
        if not hasattr(instance, 'index'):
            return
            
        alert = get_alerts()[instance.index]
        
        # Získanie detailov upozornenia
        device_id = alert.get('device_id')
        sensor_type = alert.get('sensor_type')
        timestamp = alert.get('timestamp')
        
        if not all([device_id, sensor_type, timestamp]):
            self.show_error_popup("Cannot display images: Missing alert details")
            return
            
        # Konvertovanie časovej pečiatky na formát, ktorý by sa mohol zhodovať s názvami súborov
        if isinstance(timestamp, (int, float)):
            timestamp_date = datetime.fromtimestamp(timestamp).strftime("%Y%m%d")
        else:
            self.show_error_popup("Cannot display images: Invalid timestamp")
            return
            
        # Cesta k adresáru s obrázkami
        storage_path = get_setting("images.storage_path", "captures")
        
        # Ak nie je absolútna cesta, vytvor cestu relatívnu k projektu
        if not os.path.isabs(storage_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            storage_path = os.path.join(base_dir, storage_path)
            
        # Kontrola, či adresár existuje
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, exist_ok=True)
            self.show_error_popup("No images found: Image directory doesn't exist")
            return
            
        # Hľadanie obrázkov zodpovedajúcich tomuto upozorneniu
        matching_images = []
        
        for filename in os.listdir(storage_path):
            # Hľadanie súborov, ktoré by mohli zodpovedať tomuto upozorneniu
            # Príklad formátu: motion_20250412_102030.jpg
            if (filename.startswith(f"{sensor_type}_") and 
                timestamp_date in filename and 
                filename.endswith(('.jpg', '.jpeg', '.png'))):
                matching_images.append(os.path.join(storage_path, filename))
        
        if not matching_images:
            self.show_error_popup("No images found for this alert")
            return
            
        # Zobrazenie obrázkov v popup okne
        self.show_images_popup(matching_images, alert)
            
    def show_images_popup(self, image_paths, alert):
        """Zobrazenie obrázkov v popup okne"""
        # Formátovanie informácií o upozornení
        device_name = alert.get('device_name', 'Unknown Device')
        sensor_type = alert.get('sensor_type', 'unknown').capitalize()
        status = alert.get('status', 'UNKNOWN')
        timestamp = alert.get('timestamp', 0)
        
        if isinstance(timestamp, (int, float)):
            time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_str = str(timestamp)
            
        # Vytvorenie titulku
        title = f"{sensor_type} alert from {device_name} at {time_str}"
        
        # Vytvorenie obsahu popup
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Informácie o upozornení
        content.add_widget(Label(
            text=f"{sensor_type} sensor {status}",
            font_size=18,
            size_hint_y=0.1
        ))
        
        # Zobrazenie obrázkov
        image_scroll = ScrollView(size_hint_y=0.8)
        image_grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        image_grid.bind(minimum_height=image_grid.setter('height'))
        
        for img_path in image_paths:
            img_box = BoxLayout(orientation='vertical', size_hint_y=None, height=320)
            img_box.add_widget(Label(
                text=os.path.basename(img_path),
                font_size=14,
                size_hint_y=0.1
            ))
            
            try:
                img = Image(
                    source=img_path,
                    size_hint_y=0.9,
                    allow_stretch=True,
                    keep_ratio=True
                )
                img_box.add_widget(img)
                image_grid.add_widget(img_box)
            except Exception as e:
                print(f"ERROR: Nemožno načítať obrázok {img_path}: {e}")
                
        image_scroll.add_widget(image_grid)
        content.add_widget(image_scroll)
        
        # Tlačidlo na zatvorenie
        close_button = Button(
            text="Close",
            size_hint_y=0.1
        )
        content.add_widget(close_button)
        
        # Vytvorenie a zobrazenie popup
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.9, 0.9)
        )
        
        close_button.bind(on_release=popup.dismiss)
        popup.open()
        
    def show_error_popup(self, message):
        """Zobrazí chybové hlásenie"""
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
        
    def go_back(self, instance):
        """Návrat na hlavnú obrazovku"""
        self.manager.current = 'main'