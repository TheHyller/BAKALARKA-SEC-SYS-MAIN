import os
import threading
import pygame
from config.settings import get_setting

class SoundManager:
    """Sound manager for playing alert and notification sounds"""
    
    def __init__(self):
        """Initialize the sound manager"""
        # Initialize pygame mixer module
        try:
            pygame.mixer.init()
            self.initialized = True
            print("Sound system initialized successfully")
        except Exception as e:
            self.initialized = False
            print(f"Failed to initialize sound system: {e}")
        
        # Find sound files
        self.assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        
        # Default sound paths
        self.sounds = {
            "alarm": os.path.join(self.assets_dir, "alarm.wav"),
            "notification": os.path.join(self.assets_dir, "notification.wav"),
            "error": os.path.join(self.assets_dir, "error.wav")
        }
        
        # Flags to control sound playback
        self.playing_alarm = False
        self.alarm_thread = None
    
    def play_sound(self, sound_type="notification", loops=0):
        """Play a sound of specified type
        
        Args:
            sound_type (str): Type of sound to play ('alarm', 'notification', 'error')
            loops (int): Number of times to loop the sound (-1 for infinite)
        """
        # Check if sounds are enabled in settings
        if not get_setting("alerts.sound_enabled", True):
            print("Sound is disabled in settings")
            return False
        
        # Check if sound system is initialized
        if not self.initialized:
            print("Cannot play sound: Sound system not initialized")
            return False
        
        # Check if the sound file exists
        if sound_type not in self.sounds or not os.path.exists(self.sounds[sound_type]):
            print(f"Cannot play sound: Sound file {sound_type} not found")
            return False
        
        try:
            # Load and play the sound
            sound = pygame.mixer.Sound(self.sounds[sound_type])
            sound.play(loops=loops)
            return True
        except Exception as e:
            print(f"Failed to play sound: {e}")
            return False
    
    def play_alarm(self, duration_seconds=30):
        """Play alarm sound in a separate thread with duration
        
        Args:
            duration_seconds (int): Duration to play the alarm in seconds
        """
        if self.playing_alarm:
            print("Alarm is already playing")
            return
        
        def alarm_thread():
            self.playing_alarm = True
            # Play alarm sound
            if self.play_sound("alarm", -1):  # -1 means loop indefinitely
                # Wait for the specified duration
                import time
                time.sleep(duration_seconds)
                # Stop the alarm
                self.stop_alarm()
        
        # Create and start the alarm thread
        self.alarm_thread = threading.Thread(target=alarm_thread)
        self.alarm_thread.daemon = True
        self.alarm_thread.start()
    
    def stop_alarm(self):
        """Stop the currently playing alarm sound"""
        if not self.playing_alarm:
            return
        
        try:
            # Stop all channels
            pygame.mixer.stop()
            self.playing_alarm = False
            print("Alarm stopped")
        except Exception as e:
            print(f"Failed to stop alarm: {e}")

# Create a global instance for easy access
sound_manager = SoundManager()