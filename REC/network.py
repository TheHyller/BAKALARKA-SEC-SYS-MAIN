"""
Modul pre kompletnú správu sieťovej komunikácie.
Obsahuje implementáciu sieťových poslucháčov aj centralizovaného správcu.
"""
import socket
import threading
import time
import json
import os
from datetime import datetime
try:
    from config.settings import get_setting, add_sensor_device, update_sensor_status, get_sensor_devices
except ImportError:
    def get_setting(section, default):
        return default
    def add_sensor_device(device_id, data):
        pass
    def update_sensor_status(device_id, sensor_type, status):
        pass
    def get_sensor_devices():
        return {}

class TCPListener(threading.Thread):
    def __init__(self):
        super(TCPListener, self).__init__()
        self.daemon = True
        self.running = False
        self.port = get_setting("network", {}).get("tcp_port", 8080)
        self.callbacks = []
        
    def add_callback(self, callback):
        """Pridanie callback funkcie, ktorá sa zavolá pri prijatí dát"""
        self.callbacks.append(callback)
        
    def run(self):
        """Spustenie vlákna TCP poslucháča"""
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(5)
            print(f"DEBUG: TCP poslucháč spustený na porte {self.port}")
            
            while self.running:
                try:
                    client, address = self.socket.accept()
                    
                    # Vytvorenie vlákna pre obsluhu klienta
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    print(f"ERROR: Chyba TCP pripojenia: {e}")
                    time.sleep(1)
        except Exception as e:
            print(f"ERROR: TCP poslucháč sa nepodarilo spustiť: {e}")
        finally:
            self.socket.close()
            
    def _handle_client(self, client, address):
        """Spracovanie pripojenia klienta a prijatia dát"""
        try:
            # Príjem hlavičky (prvé 4 bajty obsahujú dĺžku hlavičky JSON)
            header_length_data = client.recv(4)
            if not header_length_data:
                print(f"DEBUG: Klient {address} sa odpojil bez odoslania dát")
                return
                
            header_length = int.from_bytes(header_length_data, byteorder='big')
            header_data = client.recv(header_length)
            
            if not header_data:
                print(f"DEBUG: Klient {address} sa odpojil bez odoslania hlavičky")
                return
                
            # Parsovanie hlavičky
            header = json.loads(header_data.decode('utf-8'))
            
            print(f"DEBUG: Prijatá TCP hlavička z {address}: {header}")
            
            # Spracovanie rôznych typov dát
            if header.get('type') == 'image':
                self._handle_image_data(client, header, address)
            else:
                print(f"WARNING: Neznámy typ dát v hlavičke: {header.get('type')}")
                
            # Volanie všetkých callbackov
            data_info = {
                "header": header,
                "address": address,
            }
            for callback in self.callbacks:
                callback(data_info, address)
                
        except Exception as e:
            print(f"ERROR: Chyba pri spracovaní TCP pripojenia z {address}: {e}")
        finally:
            client.close()
            
    def _handle_image_data(self, client, header, address):
        """Spracovanie prijatia obrazových dát"""
        try:
            # Čítanie dĺžky obrazových dát
            image_length_data = client.recv(4)
            image_length = int.from_bytes(image_length_data, byteorder='big')
            
            # Postupne načítavanie obrazových dát
            received_data = bytearray()
            bytes_received = 0
            
            while bytes_received < image_length:
                chunk = client.recv(min(4096, image_length - bytes_received))
                if not chunk:
                    break
                received_data.extend(chunk)
                bytes_received += len(chunk)
                
            if bytes_received < image_length:
                print(f"WARNING: Nepodarilo sa prijať všetky obrazové dáta. Očakávané: {image_length}, Prijaté: {bytes_received}")
                return
                
            print(f"DEBUG: Prijaté obrazové dáta, {bytes_received} bajtov")
            
            # Získanie potrebných metadát
            trigger_type = header.get('trigger', 'unknown')
            timestamp = header.get('timestamp')
            filename = header.get('filename', f"{trigger_type}_{int(time.time())}.jpg")
            
            # Uloženie obrazových dát
            self._save_image_data(received_data, trigger_type, timestamp, filename, address[0])
            
        except Exception as e:
            print(f"ERROR: Zlyhalo spracovanie obrazových dát: {e}")
            
    def _save_image_data(self, image_data, trigger_type, timestamp, filename, sender_ip):
        """Uloženie prijatých obrazových dát do súboru"""
        try:
            # Získanie cesty z nastavení
            storage_path = get_setting("images.storage_path", "captures")
            
            # Ak nie je absolútna cesta, vytvor cestu relatívnu k projektu
            if not os.path.isabs(storage_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_path = os.path.join(base_dir, storage_path)
                
            # Zaisti existenciu adresára
            os.makedirs(storage_path, exist_ok=True)
            
            # Vytvorenie súboru
            filepath = os.path.join(storage_path, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
            print(f"DEBUG: Uložený obrázok: {filepath}")
            
            # Volanie notifikácií alebo logovanie
            # Tu by sme mohli pridať kód na správu upozornení alebo logovanie udalosti
            
            # Ak je to obrázok zo senzora, aktualizuj stav senzora
            if trigger_type in ['motion', 'door', 'window']:
                # Hľadanie ID zariadenia na základe IP adresy
                device_id = None
                device_name = None
                
                devices = get_sensor_devices()
                
                for d_id, d_data in devices.items():
                    if d_data.get('ip') == sender_ip:
                        device_id = d_id
                        device_name = d_data.get('name', 'Unknown Device')
                        break
                        
                if device_id:
                    status = "DETECTED" if trigger_type == "motion" else "OPEN"
                    status_data = {
                        trigger_type: status,
                        "last_updated": time.time()
                    }
                    update_sensor_status(device_id, status_data)
                    print(f"DEBUG: Aktualizovaný stav senzora {trigger_type} na {status} pre zariadenie {device_name}")
            
        except Exception as e:
            print(f"ERROR: Zlyhalo uloženie obrázka: {e}")
            
    def stop(self):
        """Zastavenie vlákna TCP poslucháča"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        print("DEBUG: TCP poslucháč zastavený")


class UDPListener(threading.Thread):
    def __init__(self):
        super(UDPListener, self).__init__()
        self.daemon = True
        self.running = False
        self.port = get_setting("network", {}).get("udp_port", 8081)
        self.callbacks = []
        
    def add_callback(self, callback):
        """Pridanie callback funkcie, ktorá sa zavolá pri prijatí dát"""
        self.callbacks.append(callback)
        
    def run(self):
        """Spustenie vlákna UDP poslucháča"""
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind(('0.0.0.0', self.port))
            print(f"DEBUG: UDP poslucháč spustený na porte {self.port}")
            
            while self.running:
                try:
                    data, address = self.socket.recvfrom(1024)
                    data = data.decode('utf-8')
                    print(f"DEBUG: UDP dáta prijaté z {address}: {data}")
                    
                    # Spracovanie dát zo senzora
                    if data.startswith("SENSOR:"):
                        parts = data.split(":")
                        if len(parts) >= 5:  # Očakávame SENSOR:ID:NAME:TYPE:STATUS
                            device_id = parts[1]
                            device_name = parts[2]
                            sensor_type = parts[3]
                            status = parts[4]
                            
                            # Registrácia alebo aktualizácia informácií o zariadení
                            device_data = {
                                "name": device_name,
                                "ip": address[0],
                                "last_seen": datetime.now().isoformat(),
                            }
                            add_sensor_device(device_id, device_data)
                            
                            # Aktualizácia stavu senzora
                            status_data = {
                                sensor_type: status,
                                "last_updated": time.time()
                            }
                            update_sensor_status(device_id, status_data)
                            
                            # Vytvorenie upozornenia pre senzorové udalosti
                            # Importuj až tu, aby sa zabránilo cyklickému importu
                            try:
                                from config.settings import add_alert, get_setting
                                
                                # Vytvor alert pre dôležité senzorové udalosti
                                if (sensor_type == "motion" and status == "DETECTED") or \
                                   ((sensor_type == "door" or sensor_type == "window") and status == "OPEN"):
                                    alert_data = {
                                        "device_id": device_id,
                                        "device_name": device_name,
                                        "sensor_type": sensor_type,
                                        "status": status,
                                        "timestamp": time.time(),
                                        "read": False
                                    }
                                    
                                    # Vždy pridaj upozornenie do histórie alertov
                                    add_alert(alert_data)
                                    print(f"DEBUG: Vytvorené upozornenie pre {device_name} - {sensor_type} {status}")
                                    
                                    # Kontrola, či je systém aktívny a spustenie ochrannej doby pre alarm
                                    system_active = get_setting("system_active", False)
                                    if system_active:
                                        try:
                                            # Import notification service pre spustenie ochrannej doby
                                            from notification_service import notification_service
                                            # Spustenie ochrannej doby pre alarm - 30 sekúnd
                                            notification_service.start_grace_period(alert_data, 30)
                                            print(f"DEBUG: Spustená ochranná doba pre {device_name} - {sensor_type}")
                                        except Exception as e:
                                            print(f"ERROR: Zlyhalo spustenie ochrannej doby: {e}")
                            except Exception as e:
                                print(f"ERROR: Zlyhalo vytvorenie upozornenia: {e}")
                    
                    for callback in self.callbacks:
                        callback(data, address)
                except Exception as e:
                    print(f"ERROR: Chyba príjmu UDP: {e}")
                    time.sleep(1)
        except Exception as e:
            print(f"ERROR: UDP poslucháč sa nepodarilo spustiť: {e}")
        finally:
            self.socket.close()
            
    def stop(self):
        """Zastavenie vlákna UDP poslucháča"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        print("DEBUG: UDP poslucháč zastavený")


class DiscoveryListener(threading.Thread):
    def __init__(self):
        super(DiscoveryListener, self).__init__()
        self.daemon = True
        self.running = False
        self.port = get_setting("network", {}).get("discovery_port", 8082)
        self.callbacks = []
        
    def add_callback(self, callback):
        """Pridanie callback funkcie, ktorá sa zavolá pri objavení zariadenia"""
        self.callbacks.append(callback)
        
    def run(self):
        """Spustenie vlákna poslucháča objavovania"""
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            self.socket.bind(('0.0.0.0', self.port))
            print(f"DEBUG: Poslucháč objavovania spustený na porte {self.port}")
            
            while self.running:
                try:
                    data, address = self.socket.recvfrom(1024)
                    data = data.decode('utf-8')
                    print(f"DEBUG: Správa objavovania prijatá z {address}: {data}")
                    
                    # Registrácia objavených zariadení
                    if data.startswith("SECURITY_DEVICE:ONLINE:"):
                        parts = data.split(":")
                        if len(parts) >= 4:
                            device_id = parts[2]
                            device_name = parts[3]
                            
                            # Registrácia alebo aktualizácia zariadenia
                            device_data = {
                                "name": device_name,
                                "ip": address[0],
                                "last_seen": datetime.now().isoformat(),
                            }
                            add_sensor_device(device_id, device_data)
                            print(f"DEBUG: Registrované zariadenie senzora {device_name} ({device_id})")
                    
                    for callback in self.callbacks:
                        callback(data, address)
                except Exception as e:
                    print(f"ERROR: Chyba príjmu objavovania: {e}")
                    time.sleep(1)
        except Exception as e:
            print(f"ERROR: Poslucháč objavovania sa nepodarilo spustiť: {e}")
        finally:
            self.socket.close()
            
    def stop(self):
        """Zastavenie vlákna poslucháča objavovania"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        print("DEBUG: Poslucháč objavovania zastavený")


class NetworkManager:
    """Centralizovaný správca všetkých sieťových poslucháčov systému"""
    
    def __init__(self):
        """Inicializácia správcu siete"""
        self.tcp_listener = None
        self.udp_listener = None
        self.discovery_listener = None
        self.is_running = False
        
    def start_listeners(self):
        """Spustenie všetkých sieťových poslucháčov"""
        if self.is_running:
            print("DEBUG: Sieťoví poslucháči už bežia")
            return

        # Inicializácia a spustenie TCP poslucháča
        self.tcp_listener = TCPListener()
        self.tcp_listener.start()
        
        # Inicializácia a spustenie UDP poslucháča
        self.udp_listener = UDPListener()
        self.udp_listener.start()
        
        # Inicializácia a spustenie poslucháča objavovania
        self.discovery_listener = DiscoveryListener()
        self.discovery_listener.start()
        
        self.is_running = True
        print("DEBUG: Všetci sieťoví poslucháči úspešne spustení")
        
    def stop_listeners(self):
        """Zastavenie všetkých sieťových poslucháčov"""
        if not self.is_running:
            print("DEBUG: Sieťoví poslucháči nie sú spustení")
            return
            
        # Zastavenie všetkých poslucháčov
        if self.tcp_listener:
            self.tcp_listener.stop()
            self.tcp_listener = None
            
        if self.udp_listener:
            self.udp_listener.stop()
            self.udp_listener = None
            
        if self.discovery_listener:
            self.discovery_listener.stop()
            self.discovery_listener = None
            
        self.is_running = False
        print("DEBUG: Všetci sieťoví poslucháči úspešne zastavení")
    
    def add_tcp_callback(self, callback):
        """Pridanie spätného volania pre TCP udalosti"""
        if self.tcp_listener:
            self.tcp_listener.add_callback(callback)
            
    def add_udp_callback(self, callback):
        """Pridanie spätného volania pre UDP udalosti"""
        if self.udp_listener:
            self.udp_listener.add_callback(callback)
            
    def add_discovery_callback(self, callback):
        """Pridanie spätného volania pre udalosti objavovania"""
        if self.discovery_listener:
            self.discovery_listener.add_callback(callback)
            
    def restart_listeners(self):
        """Reštartovanie všetkých sieťových poslucháčov"""
        self.stop_listeners()
        self.start_listeners()
        
    def is_active(self):
        """Kontrola, či sú poslucháči aktívni"""
        return self.is_running

# Vytvorenie globálnej inštancie pre jednoduchý prístup
network_manager = NetworkManager()