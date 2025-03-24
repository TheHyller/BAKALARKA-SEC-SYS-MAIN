#!/usr/bin/env python3
"""
Security System - Sender Component (SEND)
Motion detection and image transmission for Raspberry Pi

This module interfaces with GPIO sensors and camera to detect movement
and send alerts to the receiver component.
"""

import os
import time
import socket
import json
import threading
import logging
import uuid
from datetime import datetime
try:
    import RPi.GPIO as GPIO
    from picamera import PiCamera
    RPI_AVAILABLE = True
except ImportError:
    print("Warning: Running in simulation mode (RPi.GPIO or picamera not available)")
    RPI_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("security_sender.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SecuritySender")

# Configuration
CONFIG = {
    "receiver_ip": "192.168.1.100",  # IP address of the receiver (REC component)
    "tcp_port": 8080,                # Port for image transmission
    "udp_port": 8081,                # Port for sensor status updates
    "discovery_port": 8082,          # Port for discovery service
    "motion_pin": 17,                # GPIO pin for motion sensor
    "door_pin": 18,                  # GPIO pin for door sensor
    "window_pin": 27,                # GPIO pin for window sensor
    "led_pin": 22,                   # GPIO pin for status LED
    "capture_interval": 5,           # Minimum seconds between captures
    "discovery_interval": 30,        # Seconds between discovery broadcasts
    "image_path": "captures",        # Folder to store captured images
    "device_id": "",                 # Unique device ID (will be generated)
    "device_name": "Security Sensor" # Human-readable device name
}

class SecuritySender:
    def __init__(self):
        self.last_capture_time = 0
        self.running = False
        self.camera = None
        self.discovery_thread = None
        
        # Load or generate unique device ID
        self._load_or_generate_device_id()
        
        # Create image directory if it doesn't exist
        os.makedirs(CONFIG["image_path"], exist_ok=True)
        
        # Initialize GPIO if available
        if RPI_AVAILABLE:
            self._setup_gpio()
            self._setup_camera()
    
    def _load_or_generate_device_id(self):
        """Load existing device ID or generate a new one"""
        config_file = "sender_config.json"
        
        try:
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    saved_config = json.load(f)
                    if "device_id" in saved_config and saved_config["device_id"]:
                        CONFIG["device_id"] = saved_config["device_id"]
                        CONFIG["device_name"] = saved_config.get("device_name", CONFIG["device_name"])
                        logger.info(f"Loaded device ID: {CONFIG['device_id']}")
                    else:
                        self._generate_new_device_id()
            else:
                self._generate_new_device_id()
                
        except Exception as e:
            logger.error(f"Error loading device ID: {e}")
            self._generate_new_device_id()
    
    def _generate_new_device_id(self):
        """Generate a new unique device ID"""
        CONFIG["device_id"] = str(uuid.uuid4())
        
        # Set default device name with hostname and partial ID
        hostname = socket.gethostname()
        CONFIG["device_name"] = f"{hostname}-{CONFIG['device_id'][:8]}"
        
        logger.info(f"Generated new device ID: {CONFIG['device_id']}")
        
        # Save to config file
        config_file = "sender_config.json"
        try:
            with open(config_file, "w") as f:
                json.dump({
                    "device_id": CONFIG["device_id"],
                    "device_name": CONFIG["device_name"]
                }, f)
        except Exception as e:
            logger.error(f"Failed to save device ID: {e}")
    
    def _setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        
        # Setup input pins with pull-down resistors
        GPIO.setup(CONFIG["motion_pin"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(CONFIG["door_pin"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(CONFIG["window_pin"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # Setup output pin for LED
        GPIO.setup(CONFIG["led_pin"], GPIO.OUT)
        GPIO.output(CONFIG["led_pin"], GPIO.LOW)
        
        # Setup event detection
        GPIO.add_event_detect(CONFIG["motion_pin"], GPIO.RISING, 
                             callback=self._on_motion_detected)
        GPIO.add_event_detect(CONFIG["door_pin"], GPIO.BOTH, 
                             callback=self._on_door_change)
        GPIO.add_event_detect(CONFIG["window_pin"], GPIO.BOTH, 
                             callback=self._on_window_change)
        
        logger.info("GPIO pins initialized")
    
    def _setup_camera(self):
        """Initialize the camera"""
        try:
            self.camera = PiCamera()
            self.camera.resolution = (1280, 720)
            self.camera.rotation = 0  # Adjust based on camera orientation
            logger.info("Camera initialized")
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
    
    def _on_motion_detected(self, channel):
        """Callback for motion detection"""
        logger.info("Motion detected!")
        self._send_sensor_update("motion", "DETECTED")
        self._capture_image("motion")
    
    def _on_door_change(self, channel):
        """Callback for door sensor state change"""
        state = "OPEN" if GPIO.input(CONFIG["door_pin"]) else "CLOSED"
        logger.info(f"Door {state}")
        self._send_sensor_update("door", state)
        if state == "OPEN":
            self._capture_image("door")
    
    def _on_window_change(self, channel):
        """Callback for window sensor state change"""
        state = "OPEN" if GPIO.input(CONFIG["window_pin"]) else "CLOSED"
        logger.info(f"Window {state}")
        self._send_sensor_update("window", state)
        if state == "OPEN":
            self._capture_image("window")
    
    def _capture_image(self, trigger_type):
        """Capture an image from the camera if available"""
        # Check if enough time has passed since last capture
        current_time = time.time()
        if current_time - self.last_capture_time < CONFIG["capture_interval"]:
            logger.debug("Skipping capture, too soon after previous capture")
            return
        
        self.last_capture_time = current_time
        
        # Flash LED to indicate capture
        if RPI_AVAILABLE:
            GPIO.output(CONFIG["led_pin"], GPIO.HIGH)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(CONFIG["image_path"], f"{trigger_type}_{timestamp}.jpg")
        
        try:
            if self.camera:
                # Allow camera to adjust to lighting
                time.sleep(0.5)
                # Capture the image
                self.camera.capture(image_path)
                logger.info(f"Image captured: {image_path}")
                # Send the image to the receiver
                self._send_image(image_path, trigger_type)
            else:
                logger.warning("Camera not available, skipping capture")
        except Exception as e:
            logger.error(f"Failed to capture image: {e}")
        finally:
            # Turn off LED
            if RPI_AVAILABLE:
                GPIO.output(CONFIG["led_pin"], GPIO.LOW)
    
    def _send_sensor_update(self, sensor_type, status):
        """Send sensor update via UDP"""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Prepare message - include device ID and name
            message = f"SENSOR:{CONFIG['device_id']}:{CONFIG['device_name']}:{sensor_type}:{status}"
            
            # Send message
            sock.sendto(message.encode(), (CONFIG["receiver_ip"], CONFIG["udp_port"]))
            logger.debug(f"Sent UDP update: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send sensor update: {e}")
        finally:
            sock.close()
    
    def _send_image(self, image_path, trigger_type):
        """Send image via TCP"""
        try:
            # Create TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((CONFIG["receiver_ip"], CONFIG["tcp_port"]))
            
            # Send header with image info
            header = {
                "type": "image",
                "trigger": trigger_type,
                "timestamp": datetime.now().isoformat(),
                "filename": os.path.basename(image_path)
            }
            header_json = json.dumps(header).encode()
            header_length = len(header_json).to_bytes(4, byteorder='big')
            
            sock.sendall(header_length)
            sock.sendall(header_json)
            
            # Send image data
            with open(image_path, "rb") as f:
                image_data = f.read()
                sock.sendall(len(image_data).to_bytes(4, byteorder='big'))
                sock.sendall(image_data)
            
            logger.info(f"Image sent: {image_path}")
            
        except Exception as e:
            logger.error(f"Failed to send image: {e}")
        finally:
            sock.close()
    
    def _discovery_service(self):
        """Run discovery service to broadcast presence"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            while self.running:
                # Broadcast discovery message with device ID and name
                message = f"SECURITY_DEVICE:ONLINE:{CONFIG['device_id']}:{CONFIG['device_name']}"
                sock.sendto(message.encode(), ('<broadcast>', CONFIG["discovery_port"]))
                logger.debug("Sent discovery broadcast")
                
                # Listen for discovery requests
                sock.settimeout(CONFIG["discovery_interval"])
                try:
                    data, addr = sock.recvfrom(1024)
                    data = data.decode()
                    
                    if data.startswith("DISCOVER:"):
                        # Send direct response with device ID and name
                        response = f"SECURITY_DEVICE:ONLINE:{CONFIG['device_id']}:{CONFIG['device_name']}"
                        sock.sendto(response.encode(), addr)
                        logger.info(f"Responded to discovery request from {addr}")
                except socket.timeout:
                    pass
                except Exception as e:
                    logger.error(f"Discovery listen error: {e}")
                
                time.sleep(CONFIG["discovery_interval"])
        except Exception as e:
            logger.error(f"Discovery service error: {e}")
        finally:
            sock.close()
    
    def discover_receiver(self):
        """Discover the receiver IP address using broadcast"""
        logger.info("Discovering receiver...")
        
        # Create a UDP socket for discovery
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(5)  # 5-second timeout for discovery
        
        discovered_ip = None
        max_attempts = 5
        attempt = 0
        
        while not discovered_ip and attempt < max_attempts:
            attempt += 1
            try:
                # Broadcast discovery message
                discovery_message = "DISCOVER:SENDER"
                sock.sendto(discovery_message.encode(), ('<broadcast>', CONFIG["discovery_port"]))
                logger.info(f"Sent discovery broadcast (attempt {attempt}/{max_attempts})")
                
                # Wait for response
                try:
                    data, addr = sock.recvfrom(1024)
                    data = data.decode()
                    
                    if data.startswith("SECURITY_SYSTEM:ONLINE:"):
                        # Extract IP from response
                        discovered_ip = data.split(":")[2]
                        logger.info(f"Discovered receiver at {discovered_ip}")
                        
                        # Update CONFIG with discovered IP
                        CONFIG["receiver_ip"] = discovered_ip
                        return discovered_ip
                except socket.timeout:
                    logger.warning("Discovery timeout, retrying...")
                    
            except Exception as e:
                logger.error(f"Discovery error: {e}")
                
            time.sleep(2)  # Wait before next attempt
        
        if not discovered_ip:
            logger.warning("Failed to discover receiver, using default IP")
        
        return discovered_ip
    
    def start(self):
        """Start the security sender"""
        self.running = True
        
        # Try to discover the receiver first
        discovered_ip = self.discover_receiver()
        if discovered_ip:
            logger.info(f"Using discovered receiver IP: {discovered_ip}")
        else:
            logger.info(f"Using default receiver IP: {CONFIG['receiver_ip']}")
        
        # Start discovery service
        self.discovery_thread = threading.Thread(target=self._discovery_service)
        self.discovery_thread.daemon = True
        self.discovery_thread.start()
        
        logger.info("Security sender started")
        
        # For testing in development, simulate a motion detection
        if not RPI_AVAILABLE:
            def simulation():
                while self.running:
                    logger.info("SIMULATION: Motion detected")
                    self._send_sensor_update("motion", "DETECTED")
                    time.sleep(10)
            
            sim_thread = threading.Thread(target=simulation)
            sim_thread.daemon = True
            sim_thread.start()
        
        try:
            # Keep running until interrupted
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.stop()
    
    def stop(self):
        """Stop the security sender and clean up resources"""
        self.running = False
        
        if self.camera:
            self.camera.close()
        
        if RPI_AVAILABLE:
            GPIO.cleanup()
        
        logger.info("Security sender stopped")

if __name__ == "__main__":
    sender = SecuritySender()
    sender.start()