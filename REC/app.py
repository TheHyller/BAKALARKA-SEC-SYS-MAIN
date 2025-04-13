from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from config.settings import load_settings
from main_screen import MainScreen
from login_screen import LoginScreen
from settings_screen import SettingsScreen
from alerts_screen import AlertsScreen
from dashboard_screen import DashboardScreen
from listeners import DiscoveryListener, UDPListener, TCPListener
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.config import Config
from theme_helper import COLORS, style_screen
from web_app import web_app
import kivy

# Set Kivy configuration before app starts
kivy.require('2.0.0')  # Replace with your version if different
Config.set('kivy', 'default_font', ['Roboto', 'data/fonts/Roboto-Regular.ttf', 'data/fonts/Roboto-Italic.ttf', 'data/fonts/Roboto-Bold.ttf', 'data/fonts/Roboto-BoldItalic.ttf'])
Config.set('graphics', 'window_state', 'maximized')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')  # Better mouse behavior
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.write()

class MainApp(App):
    title = 'Security System'
    
    def build(self):
        # Ensure the window has white background
        Window.clearcolor = COLORS['background']
        
        # Load application settings
        settings = load_settings()
        print("DEBUG: Aplikácia sa spúšťa s načítanými nastaveniami")
        
        # Start network listeners
        self.discovery_listener = DiscoveryListener()
        self.discovery_listener.start()
        
        self.udp_listener = UDPListener()
        self.udp_listener.start()
        
        self.tcp_listener = TCPListener()
        self.tcp_listener.start()
        
        print("DEBUG: Sieťoví poslucháči spustení pre komunikáciu so senzormi")
        
        # Start web application server
        self.web_app = web_app
        self.web_app.start()
        print(f"DEBUG: Webová aplikácia spustená na porte {self.web_app.port}")
        
        # Create and configure the screen manager
        self.sm = ScreenManager()
        
        # Create all application screens
        screens = [
            LoginScreen(name='login'),
            MainScreen(name='main'),
            SettingsScreen(name='settings'),
            AlertsScreen(name='alerts'),
            DashboardScreen(name='dashboard')
        ]
        
        # Apply theme to all screens before adding them to the manager
        for screen in screens:
            style_screen(screen)
            self.sm.add_widget(screen)
        
        # Set the initial screen
        self.sm.current = 'login'
        
        return self.sm
    
    def on_start(self):
        """Called after the application starts"""
        # Ensure the theme is completely applied
        style_screen(self.sm)
    
    def on_stop(self):
        """Called when the application is closing"""
        # Stop all network listeners
        if hasattr(self, 'discovery_listener'):
            self.discovery_listener.stop()
        if hasattr(self, 'udp_listener'):
            self.udp_listener.stop()
        if hasattr(self, 'tcp_listener'):
            self.tcp_listener.stop()
        
        # Stop web application server
        if hasattr(self, 'web_app'):
            self.web_app.stop()
        
if __name__ == '__main__':
    MainApp().run()