# Inicializácia balíka
from app import MainApp
import os
from config.settings import load_settings, get_setting, cleanup_old_images
from kivy.clock import Clock
from mobile_api import mobile_api

def ensure_image_directory():
    """Ensure the image storage directory exists"""
    storage_path = get_setting("images.storage_path", "captures")
    
    # If not an absolute path, create path relative to project
    if not os.path.isabs(storage_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        storage_path = os.path.join(base_dir, '..', storage_path)
        
    # Create directory if it doesn't exist
    if not os.path.exists(storage_path):
        os.makedirs(storage_path, exist_ok=True)
        print(f"Created image storage directory: {storage_path}")

if __name__ == '__main__':
    # Load settings first
    load_settings()
    
    # Ensure image directory exists
    ensure_image_directory()
    
    # Start the mobile API server if enabled
    api_enabled = get_setting("network.enable_api", True)
    if api_enabled:
        try:
            mobile_api.start()
        except Exception as e:
            print(f"ERROR: Failed to start mobile API server: {e}")
    
    # Start the application
    app = MainApp()
    
    # Schedule periodic cleanup of old images (every 6 hours)
    Clock.schedule_interval(lambda dt: cleanup_old_images(), 6 * 60 * 60)
    
    # Run the app
    app.run()