from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from config.settings import load_settings
from main_screen import MainScreen
from login_screen import LoginScreen
from settings_screen import SettingsScreen
from alerts_screen import AlertsScreen
from dashboard_screen import DashboardScreen  # Nový import
from listeners import DiscoveryListener, UDPListener, TCPListener

class MainApp(App):
    def build(self):
        # Načítanie nastavení aplikácie
        settings = load_settings()
        print("DEBUG: Aplikácia sa spúšťa s načítanými nastaveniami")
        
        # Spustenie poslucháčov
        self.discovery_listener = DiscoveryListener()
        self.discovery_listener.start()
        
        self.udp_listener = UDPListener()
        self.udp_listener.start()
        
        self.tcp_listener = TCPListener()
        self.tcp_listener.start()
        
        print("DEBUG: Sieťoví poslucháči spustení pre komunikáciu so senzormi")
        
        # Vytvorenie správcu obrazoviek
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(AlertsScreen(name='alerts'))
        sm.add_widget(DashboardScreen(name='dashboard'))  # Pridanie novej obrazovky dashboardu
        
        # Nastavenie počiatočnej obrazovky
        sm.current = 'login'
        
        return sm
    
    def on_stop(self):
        # Zastavenie poslucháčov pri zatvorení aplikácie
        if hasattr(self, 'discovery_listener'):
            self.discovery_listener.stop()
        if hasattr(self, 'udp_listener'):
            self.udp_listener.stop()
        if hasattr(self, 'tcp_listener'):
            self.tcp_listener.stop()
        
if __name__ == '__main__':
    MainApp().run()