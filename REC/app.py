from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from config.settings import load_settings
from main_screen import MainScreen
from login_screen import LoginScreen
from settings_screen import SettingsScreen
from alerts_screen import AlertsScreen
from dashboard_screen import DashboardScreen  # New import
from listeners import DiscoveryListener, UDPListener, TCPListener

class MainApp(App):
    def build(self):
        # Load application settings
        settings = load_settings()
        print("DEBUG: Application starting with loaded settings")
        
        # Start listeners
        self.discovery_listener = DiscoveryListener()
        self.discovery_listener.start()
        
        self.udp_listener = UDPListener()
        self.udp_listener.start()
        
        self.tcp_listener = TCPListener()
        self.tcp_listener.start()
        
        print("DEBUG: Network listeners started for sensor communication")
        
        # Create screen manager
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(AlertsScreen(name='alerts'))
        sm.add_widget(DashboardScreen(name='dashboard'))  # Add new dashboard screen
        
        # Set the initial screen
        sm.current = 'login'
        
        return sm
    
    def on_stop(self):
        # Stop listeners when app closes
        if hasattr(self, 'discovery_listener'):
            self.discovery_listener.stop()
        if hasattr(self, 'udp_listener'):
            self.udp_listener.stop()
        if hasattr(self, 'tcp_listener'):
            self.tcp_listener.stop()
        
if __name__ == '__main__':
    MainApp().run()