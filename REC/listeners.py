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
        """Add a callback function to be called when data is received"""
        self.callbacks.append(callback)
        
    def run(self):
        """Start the TCP listener thread"""
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(5)
            print(f"DEBUG: TCP Listener started on port {self.port}")
            
            while self.running:
                try:
                    client, address = self.socket.accept()
                    data = client.recv(1024).decode('utf-8')
                    print(f"DEBUG: TCP data received from {address}: {data}")
                    
                    for callback in self.callbacks:
                        callback(data, address)
                        
                    client.close()
                except Exception as e:
                    print(f"ERROR: TCP connection error: {e}")
                    time.sleep(1)
        except Exception as e:
            print(f"ERROR: TCP listener failed to start: {e}")
        finally:
            self.socket.close()
            
    def stop(self):
        """Stop the TCP listener thread"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        print("DEBUG: TCP Listener stopped")


class UDPListener(threading.Thread):
    def __init__(self):
        super(UDPListener, self).__init__()
        self.daemon = True
        self.running = False
        self.port = get_setting("network", {}).get("udp_port", 8081)
        self.callbacks = []
        
    def add_callback(self, callback):
        """Add a callback function to be called when data is received"""
        self.callbacks.append(callback)
        
    def run(self):
        """Start the UDP listener thread"""
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind(('0.0.0.0', self.port))
            print(f"DEBUG: UDP Listener started on port {self.port}")
            
            while self.running:
                try:
                    data, address = self.socket.recvfrom(1024)
                    data = data.decode('utf-8')
                    print(f"DEBUG: UDP data received from {address}: {data}")
                    
                    # Process sensor data
                    if data.startswith("SENSOR:"):
                        parts = data.split(":")
                        if len(parts) >= 5:  # We expect SENSOR:ID:NAME:TYPE:STATUS
                            device_id = parts[1]
                            device_name = parts[2]
                            sensor_type = parts[3]
                            status = parts[4]
                            
                            # Register or update device info
                            device_data = {
                                "name": device_name,
                                "ip": address[0],
                                "last_seen": datetime.now().isoformat(),
                            }
                            add_sensor_device(device_id, device_data)
                            
                            # Update sensor status
                            update_sensor_status(device_id, sensor_type, status)
                            
                    for callback in self.callbacks:
                        callback(data, address)
                except Exception as e:
                    print(f"ERROR: UDP reception error: {e}")
                    time.sleep(1)
        except Exception as e:
            print(f"ERROR: UDP listener failed to start: {e}")
        finally:
            self.socket.close()
            
    def stop(self):
        """Stop the UDP listener thread"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        print("DEBUG: UDP Listener stopped")


class DiscoveryListener(threading.Thread):
    def __init__(self):
        super(DiscoveryListener, self).__init__()
        self.daemon = True
        self.running = False
        self.port = get_setting("network", {}).get("discovery_port", 8082)
        self.callbacks = []
        
    def add_callback(self, callback):
        """Add a callback function to be called when a device is discovered"""
        self.callbacks.append(callback)
        
    def run(self):
        """Start the discovery listener thread"""
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            self.socket.bind(('0.0.0.0', self.port))
            print(f"DEBUG: Discovery Listener started on port {self.port}")
            
            while self.running:
                try:
                    data, address = self.socket.recvfrom(1024)
                    data = data.decode('utf-8')
                    print(f"DEBUG: Discovery message received from {address}: {data}")
                    
                    # Register discovered devices
                    if data.startswith("SECURITY_DEVICE:ONLINE:"):
                        parts = data.split(":")
                        if len(parts) >= 4:
                            device_id = parts[2]
                            device_name = parts[3]
                            
                            # Register or update device
                            device_data = {
                                "name": device_name,
                                "ip": address[0],
                                "last_seen": datetime.now().isoformat(),
                            }
                            add_sensor_device(device_id, device_data)
                            print(f"DEBUG: Registered sensor device {device_name} ({device_id})")
                    
                    # Send response to discovery request with our IP address
                    if data.startswith("DISCOVER:"):
                        # Get local IP address (the one used to communicate with the sender)
                        local_ip = socket.gethostbyname(socket.gethostname())
                        
                        # For cases where gethostbyname returns localhost, try a different approach
                        if local_ip.startswith("127."):
                            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            # This doesn't actually send any packets
                            s.connect((address[0], 1))
                            local_ip = s.getsockname()[0]
                            s.close()
                            
                        response = f"SECURITY_SYSTEM:ONLINE:{local_ip}"
                        self.socket.sendto(response.encode('utf-8'), address)
                        print(f"DEBUG: Sent discovery response to {address} with IP {local_ip}")
                    
                    for callback in self.callbacks:
                        callback(data, address)
                except Exception as e:
                    print(f"ERROR: Discovery reception error: {e}")
                    time.sleep(1)
        except Exception as e:
            print(f"ERROR: Discovery listener failed to start: {e}")
        finally:
            self.socket.close()
            
    def stop(self):
        """Stop the discovery listener thread"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        print("DEBUG: Discovery Listener stopped")