import socket
import threading
import time
import json
from datetime import datetime
try:
    from config.settings import get_setting, add_sensor_device, update_sensor_status
except ImportError:
    def get_setting(section, default):
        return default
    def add_sensor_device(device_id, data):
        pass
    def update_sensor_status(device_id, sensor_type, status):
        pass

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
                    data = client.recv(1024).decode('utf-8')
                    print(f"DEBUG: TCP dáta prijaté z {address}: {data}")
                    
                    for callback in self.callbacks:
                        callback(data, address)
                        
                    client.close()
                except Exception as e:
                    print(f"ERROR: Chyba TCP pripojenia: {e}")
                    time.sleep(1)
        except Exception as e:
            print(f"ERROR: TCP poslucháč sa nepodarilo spustiť: {e}")
        finally:
            self.socket.close()
            
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
                            update_sensor_status(device_id, sensor_type, status)
                            
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
                    
                    # Odoslanie odpovede na požiadavku objavovania s našou IP adresou
                    if data.startswith("DISCOVER:"):
                        # Získanie lokálnej IP adresy (tej, ktorá sa používa na komunikáciu s odosielateľom)
                        local_ip = socket.gethostbyname(socket.gethostname())
                        
                        # Pre prípady, keď gethostbyname vráti localhost, skúsime iný prístup
                        if local_ip.startswith("127."):
                            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            # Toto v skutočnosti neodosiela žiadne pakety
                            s.connect((address[0], 1))
                            local_ip = s.getsockname()[0]
                            s.close()
                            
                        response = f"SECURITY_SYSTEM:ONLINE:{local_ip}"
                        self.socket.sendto(response.encode('utf-8'), address)
                        print(f"DEBUG: Odoslaná odpoveď objavovania na {address} s IP {local_ip}")
                    
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