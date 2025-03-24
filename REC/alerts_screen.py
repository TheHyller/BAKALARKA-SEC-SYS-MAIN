from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

class AlertsScreen(Screen):
    def __init__(self, **kwargs):
        super(AlertsScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Title
        layout.add_widget(Label(
            text="System Alerts",
            font_size=24,
            size_hint_y=0.1
        ))
        
        # Alerts list
        scroll_view = ScrollView(size_hint_y=0.7)
        self.alerts_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.alerts_list.bind(minimum_height=self.alerts_list.setter('height'))
        scroll_view.add_widget(self.alerts_list)
        layout.add_widget(scroll_view)
        
        # Add sample alerts (would be populated from actual alerts in a real app)
        self.add_alert("Motion detected - Front door", "2025-03-24 10:15:22")
        self.add_alert("Window sensor - Triggered", "2025-03-24 09:30:45")
        self.add_alert("System activated", "2025-03-24 08:00:00")
        
        # Back button
        back_button = Button(
            text="Back to Main",
            size_hint_y=0.1
        )
        back_button.bind(on_release=self.go_back)
        layout.add_widget(back_button)
        
        self.add_widget(layout)
        
    def add_alert(self, message, timestamp):
        """Add an alert to the alerts list"""
        alert_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        alert_layout.add_widget(Label(text=message, font_size=18, halign='left'))
        alert_layout.add_widget(Label(text=timestamp, font_size=14, halign='left'))
        
        self.alerts_list.add_widget(alert_layout)
        
    def go_back(self, instance):
        """Return to main screen"""
        self.manager.current = 'main'