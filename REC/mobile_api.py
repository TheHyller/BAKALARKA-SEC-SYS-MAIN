import os
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from threading import Thread
from config.settings import (get_setting, get_alerts, mark_alert_as_read, 
                           get_sensor_devices, get_sensor_status, toggle_system_state, 
                           validate_pin)

class MobileApiServer:
    """API Server for the mobile companion app"""
    
    def __init__(self, host='0.0.0.0', port=5000):
        """Initialize the API server
        
        Args:
            host (str): Host to listen on
            port (int): Port to listen on
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.running = False
        self.server_thread = None
        self.setup_routes()
    
    def setup_routes(self):
        """Configure the API routes"""
        
        # API Authentication helper
        def authenticate():
            """Authenticate API requests with PIN"""
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return False
            
            # Extract PIN from Bearer token
            pin = auth_header.split(' ')[1]
            return validate_pin(pin)
        
        @self.app.route('/api/status', methods=['GET'])
        def system_status():
            """Get the current system status"""
            if not authenticate():
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Get system status
            system_active = get_setting("system_active", False)
            
            # Get device information
            devices = get_sensor_devices()
            active_devices = 0
            
            for device_id, device_data in devices.items():
                if 'last_seen' in device_data:
                    try:
                        last_seen = datetime.fromisoformat(device_data['last_seen'])
                        if (datetime.now() - last_seen).total_seconds() < 3600:  # Active in the last hour
                            active_devices += 1
                    except (ValueError, TypeError):
                        pass
            
            # Get alert information
            alerts = get_alerts()
            unread_alerts = sum(1 for a in alerts if not a.get('read', False))
            
            return jsonify({
                'system_active': system_active,
                'devices': {
                    'total': len(devices),
                    'active': active_devices,
                    'offline': len(devices) - active_devices
                },
                'alerts': {
                    'total': len(alerts),
                    'unread': unread_alerts
                },
                'timestamp': time.time()
            })
        
        @self.app.route('/api/alerts', methods=['GET'])
        def get_system_alerts():
            """Get the system alerts"""
            if not authenticate():
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Get alert information, optionally filtering by count and read status
            count = request.args.get('count', None)
            if count:
                try:
                    count = int(count)
                except ValueError:
                    count = None
                    
            unread_only = request.args.get('unread', 'false').lower() == 'true'
            
            alerts = get_alerts(count=count, unread_only=unread_only)
            
            # Format timestamps for JSON
            formatted_alerts = []
            for alert in alerts:
                alert_copy = alert.copy()
                if isinstance(alert_copy.get('timestamp'), (int, float)):
                    alert_copy['timestamp'] = datetime.fromtimestamp(
                        alert_copy['timestamp']).isoformat()
                formatted_alerts.append(alert_copy)
            
            return jsonify({
                'alerts': formatted_alerts,
                'total': len(alerts),
                'unread': sum(1 for a in alerts if not a.get('read', False))
            })
        
        @self.app.route('/api/alerts/<int:alert_index>/read', methods=['POST'])
        def mark_alert_read(alert_index):
            """Mark an alert as read"""
            if not authenticate():
                return jsonify({'error': 'Unauthorized'}), 401
            
            success = mark_alert_as_read(alert_index)
            
            return jsonify({
                'success': success,
                'message': 'Alert marked as read' if success else 'Failed to mark alert as read'
            })
        
        @self.app.route('/api/sensors', methods=['GET'])
        def get_sensors():
            """Get the sensor information"""
            if not authenticate():
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Get device and sensor information
            devices = get_sensor_devices()
            statuses = get_sensor_status()
            
            # Format data for JSON response
            result = []
            for device_id, device_data in devices.items():
                # Format timestamps
                last_seen = device_data.get('last_seen', '')
                if last_seen:
                    try:
                        last_seen = datetime.fromisoformat(last_seen)
                        device_data['last_seen'] = last_seen.isoformat()
                    except ValueError:
                        pass
                
                # Get sensor status for this device
                device_status = statuses.get(device_id, {})
                
                # Format timestamps in status
                for sensor, data in device_status.items():
                    if isinstance(data.get('timestamp'), (int, float)):
                        data['timestamp'] = datetime.fromtimestamp(
                            data['timestamp']).isoformat()
                
                result.append({
                    'id': device_id,
                    'name': device_data.get('name', 'Unknown Device'),
                    'ip': device_data.get('ip', 'Unknown'),
                    'last_seen': device_data.get('last_seen', ''),
                    'status': device_status
                })
            
            return jsonify({'sensors': result})
        
        @self.app.route('/api/images/<path:image_path>', methods=['GET'])
        def get_image(image_path):
            """Get an image from the captures directory"""
            if not authenticate():
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Get the captures directory
            storage_path = get_setting("images.storage_path", "captures")
            
            # If not an absolute path, create path relative to project
            if not os.path.isabs(storage_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_path = os.path.join(base_dir, storage_path)
            
            # Construct full path (ensure it's within the captures directory for security)
            file_path = os.path.join(storage_path, os.path.basename(image_path))
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_file(file_path)
            else:
                return jsonify({'error': 'Image not found'}), 404
        
        @self.app.route('/api/images', methods=['GET'])
        def list_images():
            """List available capture images"""
            if not authenticate():
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Get the captures directory
            storage_path = get_setting("images.storage_path", "captures")
            
            # If not an absolute path, create path relative to project
            if not os.path.isabs(storage_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_path = os.path.join(base_dir, storage_path)
            
            # List images with their metadata
            images = []
            if os.path.exists(storage_path):
                for filename in os.listdir(storage_path):
                    if filename.endswith(('.jpg', '.jpeg', '.png')):
                        file_path = os.path.join(storage_path, filename)
                        timestamp = os.path.getmtime(file_path)
                        
                        # Try to extract sensor type from filename (format: type_timestamp.jpg)
                        sensor_type = "unknown"
                        if '_' in filename:
                            sensor_type = filename.split('_')[0]
                        
                        images.append({
                            'filename': filename,
                            'path': f'/api/images/{filename}',
                            'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                            'sensor_type': sensor_type
                        })
            
            # Sort by timestamp (newest first)
            images.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return jsonify({'images': images})
        
        @self.app.route('/api/system/toggle', methods=['POST'])
        def toggle_system():
            """Toggle the system active state"""
            if not authenticate():
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Optional new state parameter
            data = request.get_json() or {}
            new_state = data.get('active', None)
            
            toggled = toggle_system_state(new_state)
            current_state = get_setting("system_active", False)
            
            return jsonify({
                'success': toggled,
                'system_active': current_state,
                'message': f'System {"activated" if current_state else "deactivated"}'
            })
    
    def start(self):
        """Start the API server in a separate thread"""
        if self.running:
            print("API server is already running")
            return
        
        def run_server():
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.running = True
        print(f"Mobile API server started on {self.host}:{self.port}")
    
    def stop(self):
        """Stop the API server"""
        self.running = False
        print("Mobile API server stopped")

# Create a global instance
mobile_api = MobileApiServer(port=get_setting("network.api_port", 5000))