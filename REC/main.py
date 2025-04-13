# Inicializácia balíka
from app import MainApp
import os
from config.settings import load_settings, get_setting, cleanup_old_images
from kivy.clock import Clock

def ensure_image_directory():
    """Zabezpečenie, že adresár na ukladanie obrázkov existuje"""
    storage_path = get_setting("images.storage_path", "captures")
    
    # Ak nie je absolútna cesta, vytvorenie cesty relatívnej k projektu
    if not os.path.isabs(storage_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        storage_path = os.path.join(base_dir, '..', storage_path)
        
    # Vytvorenie adresára, ak neexistuje
    if not os.path.exists(storage_path):
        os.makedirs(storage_path, exist_ok=True)
        print(f"Vytvorený adresár na ukladanie obrázkov: {storage_path}")

if __name__ == '__main__':
    # Najprv načítanie nastavení
    load_settings()
    
    # Zabezpečenie, že adresár obrázkov existuje
    ensure_image_directory()
    
    # Spustenie aplikácie
    app = MainApp()
    
    # Naplánovanie pravidelného čistenia starých obrázkov (každých 6 hodín)
    Clock.schedule_interval(lambda dt: cleanup_old_images(), 6 * 60 * 60)
    
    # Spustenie aplikácie
    app.run()