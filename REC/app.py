from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from config.settings import load_settings
from main_screen import MainScreen
from login_screen import LoginScreen
from settings_screen import SettingsScreen
from alerts_screen import AlertsScreen

class MainApp(App):
    def build(self):
        # Load application settings
        settings = load_settings()
        print("DEBUG: Application starting with loaded settings")
        
        # Create screen manager
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(AlertsScreen(name='alerts'))
        
        # Set the initial screen
        sm.current = 'login'
        
        return sm

if __name__ == '__main__':
    MainApp().run()