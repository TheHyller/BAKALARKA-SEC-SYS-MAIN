#!/usr/bin/env python3
"""
Bezpečnostný systém - Komponent odosielateľa (SEND)
Detekcia pohybu a prenos obrázkov pre Raspberry Pi

Tento modul komunikuje s GPIO senzormi a kamerou na detekciu pohybu
a odosiela upozornenia do komponenty prijímača.
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
    print("Upozornenie: Beží v simulačnom režime (RPi.GPIO alebo picamera nie sú dostupné)")
    RPI_AVAILABLE = False

# Konfigurácia logovania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("security_sender.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SecuritySender")

# Konfigurácia
CONFIG = {
    "receiver_ip": "192.168.1.100",  # IP adresa prijímača (REC komponenta)
    "tcp_port": 8080,                # Port pre prenos obrázkov
    "udp_port": 8081,                # Port pre aktualizácie stavu senzorov
    "discovery_port": 8082,          # Port pre službu objavovania
    "motion_pin": 17,                # GPIO pin pre senzor pohybu
    "door_pin": 18,                  # GPIO pin pre dverový senzor
    "window_pin": 27,                # GPIO pin pre okenný senzor
    "led_pin": 22,                   # GPIO pin pre stavovú LED
    "capture_interval": 5,           # Minimálny počet sekúnd medzi zachyteniami
    "discovery_interval": 30,        # Sekundy medzi vysielaním objavovania
    "image_path": "captures",        # Priečinok na ukladanie zachytených obrázkov
    "device_id": "",                 # Unikátne ID zariadenia (bude vygenerované)
    "device_name": "Security Sensor" # Ľudsky čitateľný názov zariadenia
}

class SecuritySender:
    def __init__(self):
        self.last_capture_time = 0
        self.running = False
        self.camera = None
        self.discovery_thread = None
        
        # Načítanie alebo generovanie unikátneho ID zariadenia
        self._load_or_generate_device_id()
        
        # Vytvorenie adresára pre obrázky, ak neexistuje
        os.makedirs(CONFIG["image_path"], exist_ok=True)
        
        # Inicializácia GPIO, ak je dostupné
        if RPI_AVAILABLE:
            self._setup_gpio()
            self._setup_camera()
    
    def _load_or_generate_device_id(self):
        """Načíta existujúce ID zariadenia alebo vygeneruje nové"""
        config_file = "sender_config.json"
        
        try:
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    saved_config = json.load(f)
                    if "device_id" in saved_config and saved_config["device_id"]:
                        CONFIG["device_id"] = saved_config["device_id"]
                        CONFIG["device_name"] = saved_config.get("device_name", CONFIG["device_name"])
                        logger.info(f"Načítané ID zariadenia: {CONFIG['device_id']}")
                    else:
                        self._generate_new_device_id()
            else:
                self._generate_new_device_id()
                
        except Exception as e:
            logger.error(f"Chyba pri načítaní ID zariadenia: {e}")
            self._generate_new_device_id()
    
    def _generate_new_device_id(self):
        """Vygeneruje nové unikátne ID zariadenia"""
        CONFIG["device_id"] = str(uuid.uuid4())
        
        # Nastavenie predvoleného názvu zariadenia s názvom hostiteľa a čiastočným ID
        hostname = socket.gethostname()
        CONFIG["device_name"] = f"{hostname}-{CONFIG['device_id'][:8]}"
        
        logger.info(f"Vygenerované nové ID zariadenia: {CONFIG['device_id']}")
        
        # Uloženie do konfiguračného súboru
        config_file = "sender_config.json"
        try:
            with open(config_file, "w") as f:
                json.dump({
                    "device_id": CONFIG["device_id"],
                    "device_name": CONFIG["device_name"]
                }, f)
        except Exception as e:
            logger.error(f"Zlyhalo uloženie ID zariadenia: {e}")
    
    def _setup_gpio(self):
        """Inicializácia GPIO pinov"""
        GPIO.setmode(GPIO.BCM)
        
        # Nastavenie vstupných pinov s pull-down rezistormi
        GPIO.setup(CONFIG["motion_pin"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(CONFIG["door_pin"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(CONFIG["window_pin"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # Nastavenie výstupného pinu pre LED
        GPIO.setup(CONFIG["led_pin"], GPIO.OUT)
        GPIO.output(CONFIG["led_pin"], GPIO.LOW)
        
        # Nastavenie detekcie udalostí
        GPIO.add_event_detect(CONFIG["motion_pin"], GPIO.RISING, 
                             callback=self._on_motion_detected)
        GPIO.add_event_detect(CONFIG["door_pin"], GPIO.BOTH, 
                             callback=self._on_door_change)
        GPIO.add_event_detect(CONFIG["window_pin"], GPIO.BOTH, 
                             callback=self._on_window_change)
        
        logger.info("GPIO piny inicializované")
    
    def _setup_camera(self):
        """Inicializácia kamery"""
        try:
            self.camera = PiCamera()
            self.camera.resolution = (1280, 720)
            self.camera.rotation = 0  # Úprava podľa orientácie kamery
            logger.info("Kamera inicializovaná")
        except Exception as e:
            logger.error(f"Zlyhala inicializácia kamery: {e}")
    
    def _on_motion_detected(self, channel):
        """Callback pre detekciu pohybu"""
        logger.info("Pohyb detekovaný!")
        self._send_sensor_update("motion", "DETECTED")
        self._capture_image("motion")
    
    def _on_door_change(self, channel):
        """Callback pre zmenu stavu dverového senzora"""
        state = "OPEN" if GPIO.input(CONFIG["door_pin"]) else "CLOSED"
        logger.info(f"Dvere {state}")
        self._send_sensor_update("door", state)
        if state == "OPEN":
            self._capture_image("door")
    
    def _on_window_change(self, channel):
        """Callback pre zmenu stavu okenného senzora"""
        state = "OPEN" if GPIO.input(CONFIG["window_pin"]) else "CLOSED"
        logger.info(f"Okno {state}")
        self._send_sensor_update("window", state)
        if state == "OPEN":
            self._capture_image("window")
    
    def _capture_image(self, trigger_type):
        """Zachytenie obrázka z kamery, ak je dostupná"""
        # Kontrola, či uplynul dostatočný čas od posledného zachytenia
        current_time = time.time()
        if current_time - self.last_capture_time < CONFIG["capture_interval"]:
            logger.debug("Preskakujem zachytenie, príliš krátky čas od predchádzajúceho zachytenia")
            return
        
        self.last_capture_time = current_time
        
        # Zablikanie LED na indikáciu zachytenia
        if RPI_AVAILABLE:
            GPIO.output(CONFIG["led_pin"], GPIO.HIGH)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(CONFIG["image_path"], f"{trigger_type}_{timestamp}.jpg")
        
        try:
            if self.camera:
                # Daj kamere čas na prispôsobenie sa osvetleniu
                time.sleep(0.5)
                # Zachyť obrázok
                self.camera.capture(image_path)
                logger.info(f"Obrázok zachytený: {image_path}")
                # Odošli obrázok prijímaču
                self._send_image(image_path, trigger_type)
            else:
                logger.warning("Kamera nie je dostupná, preskakujem zachytenie")
        except Exception as e:
            logger.error(f"Zlyhalo zachytenie obrázka: {e}")
        finally:
            # Vypni LED
            if RPI_AVAILABLE:
                GPIO.output(CONFIG["led_pin"], GPIO.LOW)
    
    def _send_sensor_update(self, sensor_type, status):
        """Odoslanie aktualizácie senzora cez UDP"""
        try:
            # Vytvorenie UDP socketu
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Príprava správy - zahrnutie ID zariadenia a názvu
            message = f"SENSOR:{CONFIG['device_id']}:{CONFIG['device_name']}:{sensor_type}:{status}"
            
            # Odoslanie správy
            sock.sendto(message.encode(), (CONFIG["receiver_ip"], CONFIG["udp_port"]))
            logger.debug(f"Odoslaná UDP aktualizácia: {message}")
            
        except Exception as e:
            logger.error(f"Zlyhalo odoslanie aktualizácie senzora: {e}")
        finally:
            sock.close()
    
    def _send_image(self, image_path, trigger_type):
        """Odoslanie obrázka cez TCP"""
        try:
            # Vytvorenie TCP socketu
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((CONFIG["receiver_ip"], CONFIG["tcp_port"]))
            
            # Odoslanie hlavičky s informáciami o obrázku
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
            
            # Odoslanie dát obrázka
            with open(image_path, "rb") as f:
                image_data = f.read()
                sock.sendall(len(image_data).to_bytes(4, byteorder='big'))
                sock.sendall(image_data)
            
            logger.info(f"Obrázok odoslaný: {image_path}")
            
        except Exception as e:
            logger.error(f"Zlyhalo odoslanie obrázka: {e}")
        finally:
            sock.close()
    
    def _discovery_service(self):
        """Spustenie služby objavovania na vysielanie prítomnosti"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            while self.running:
                # Vysielanie správy objavovania s ID zariadenia a názvom
                message = f"SECURITY_DEVICE:ONLINE:{CONFIG['device_id']}:{CONFIG['device_name']}"
                sock.sendto(message.encode(), ('<broadcast>', CONFIG["discovery_port"]))
                logger.debug("Odoslané vysielanie objavovania")
                
                # Načúvanie na požiadavky objavovania
                sock.settimeout(CONFIG["discovery_interval"])
                try:
                    data, addr = sock.recvfrom(1024)
                    data = data.decode()
                    
                    if data.startswith("DISCOVER:"):
                        # Odošli priamu odpoveď s ID zariadenia a názvom
                        response = f"SECURITY_DEVICE:ONLINE:{CONFIG['device_id']}:{CONFIG['device_name']}"
                        sock.sendto(response.encode(), addr)
                        logger.info(f"Odpovedané na požiadavku objavovania z {addr}")
                except socket.timeout:
                    pass
                except Exception as e:
                    logger.error(f"Chyba načúvania objavovania: {e}")
                
                time.sleep(CONFIG["discovery_interval"])
        except Exception as e:
            logger.error(f"Chyba služby objavovania: {e}")
        finally:
            sock.close()
    
    def discover_receiver(self):
        """Objavenie IP adresy prijímača pomocou vysielania"""
        logger.info("Objavovanie prijímača...")
        
        # Vytvorenie UDP socketu pre objavovanie
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(5)  # 5-sekundový časový limit pre objavovanie
        
        discovered_ip = None
        max_attempts = 5
        attempt = 0
        
        while not discovered_ip and attempt < max_attempts:
            attempt += 1
            try:
                # Vysielanie správy objavovania
                discovery_message = "DISCOVER:SENDER"
                sock.sendto(discovery_message.encode(), ('<broadcast>', CONFIG["discovery_port"]))
                logger.info(f"Odoslané vysielanie objavovania (pokus {attempt}/{max_attempts})")
                
                # Čakanie na odpoveď
                try:
                    data, addr = sock.recvfrom(1024)
                    data = data.decode()
                    
                    if data.startswith("SECURITY_SYSTEM:ONLINE:"):
                        # Extrahovanie IP z odpovede
                        discovered_ip = data.split(":")[2]
                        logger.info(f"Objavený prijímač na {discovered_ip}")
                        
                        # Aktualizácia CONFIG s objavenou IP
                        CONFIG["receiver_ip"] = discovered_ip
                        return discovered_ip
                except socket.timeout:
                    logger.warning("Časový limit objavovania, skúšam znova...")
                    
            except Exception as e:
                logger.error(f"Chyba objavovania: {e}")
                
            time.sleep(2)  # Čakanie pred ďalším pokusom
        
        if not discovered_ip:
            logger.warning("Zlyhalo objavenie prijímača, používam predvolenú IP")
        
        return discovered_ip
    
    def start(self):
        """Spustenie odosielateľa zabezpečenia"""
        self.running = True
        
        # Najprv sa pokús objaviť prijímač
        discovered_ip = self.discover_receiver()
        if discovered_ip:
            logger.info(f"Používam objavenú IP prijímača: {discovered_ip}")
        else:
            logger.info(f"Používam predvolenú IP prijímača: {CONFIG['receiver_ip']}")
        
        # Spusti službu objavovania
        self.discovery_thread = threading.Thread(target=self._discovery_service)
        self.discovery_thread.daemon = True
        self.discovery_thread.start()
        
        logger.info("Odosielateľ zabezpečenia spustený")
        
        # Pre testovanie vo vývoji, simuluj detekciu pohybu
        if not RPI_AVAILABLE:
            def simulation():
                while self.running:
                    logger.info("SIMULÁCIA: Pohyb detekovaný")
                    self._send_sensor_update("motion", "DETECTED")
                    time.sleep(10)
            
            sim_thread = threading.Thread(target=simulation)
            sim_thread.daemon = True
            sim_thread.start()
        
        try:
            # Bež, kým nie je prerušený
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Vypínanie...")
            self.stop()
    
    def stop(self):
        """Zastavenie odosielateľa zabezpečenia a vyčistenie zdrojov"""
        self.running = False
        
        if self.camera:
            self.camera.close()
        
        if RPI_AVAILABLE:
            GPIO.cleanup()
        
        logger.info("Odosielateľ zabezpečenia zastavený")

if __name__ == "__main__":
    sender = SecuritySender()
    sender.start()