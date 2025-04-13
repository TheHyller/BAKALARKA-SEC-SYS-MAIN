from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from config.settings import load_settings
from main_screen import MainScreen
from login_screen import LoginScreen
from settings_screen import SettingsScreen
from alerts_screen import AlertsScreen
from dashboard_screen import DashboardScreen
from network import network_manager
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.config import Config
from theme_helper import COLORS, style_screen
from web_app import web_app
import kivy

# Nastavenie konfigurácie Kivy pred spustením aplikácie
kivy.require('2.0.0')  
Config.set('kivy', 'default_font', ['Roboto', 'data/fonts/Roboto-Regular.ttf', 'data/fonts/Roboto-Italic.ttf', 'data/fonts/Roboto-Bold.ttf', 'data/fonts/Roboto-BoldItalic.ttf'])
Config.set('graphics', 'window_state', 'maximized')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand') 
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
Config.write()

class MainApp(App):
    title = 'Security System'
    
    def build(self):
        # Zabezpečenie, že okno má biele pozadie
        Window.clearcolor = COLORS['background']
        
        # Načítanie nastavení aplikácie
        settings = load_settings()
        print("DEBUG: Aplikácia sa spúšťa s načítanými nastaveniami")
        
        # Spustenie sieťových poslucháčov pomocou NetworkManager
        network_manager.start_listeners()
        print("DEBUG: Sieťoví poslucháči spustení pre komunikáciu so senzormi")
        
        # Spustenie webového aplikačného servera
        self.web_app = web_app
        self.web_app.start()
        print(f"DEBUG: Webová aplikácia spustená na porte {self.web_app.port}")
        
        # Vytvorenie a konfigurácia správcu obrazoviek
        self.sm = ScreenManager()
        
        # Vytvorenie všetkých obrazoviek aplikácie
        screens = [
            LoginScreen(name='login'),
            MainScreen(name='main'),
            SettingsScreen(name='settings'),
            AlertsScreen(name='alerts'),
            DashboardScreen(name='dashboard')
        ]
        
        # Aplikácia témy na všetky obrazovky pred ich pridaním do správcu
        for screen in screens:
            style_screen(screen)
            self.sm.add_widget(screen)
        
        # Nastavenie počiatočnej obrazovky
        self.sm.current = 'login'
        
        return self.sm
    
    def on_start(self):
        """Volané po spustení aplikácie"""
        # Zabezpečenie, že téma je úplne aplikovaná
        style_screen(self.sm)
    
    def on_stop(self):
        """Volané pri zatváraní aplikácie"""
        # Zastavenie všetkých sieťových poslucháčov pomocou NetworkManager
        network_manager.stop_listeners()
        
        # Zastavenie webového aplikačného servera
        if hasattr(self, 'web_app'):
            self.web_app.stop()
        
if __name__ == '__main__':
    MainApp().run()