import os
import json
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, session, flash
from threading import Thread, Event
from werkzeug.serving import make_server
from config.settings import (get_setting, get_alerts, mark_alert_as_read, 
                           get_sensor_devices, get_sensor_status, toggle_system_state, 
                           validate_pin)

# Disable Flask's default logging to reduce console spam
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class WebAppServer:
    """Web Application Server for browser-based access"""
    
    def __init__(self, host='0.0.0.0', port=8080):
        """Initialize the Web App server
        
        Args:
            host (str): Host to listen on
            port (int): Port to listen on
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__, 
                        static_folder='web/static',
                        template_folder='web/templates')
        self.app.secret_key = os.urandom(24)  # For session management
        self.running = False
        self.server = None
        self.server_thread = None
        self.shutdown_event = Event()
        self.setup_routes()
    
    def setup_routes(self):
        """Configure the web app routes"""
        
        # Add template context processor to include datetime
        @self.app.context_processor
        def inject_now():
            return {'now': datetime.now()}
        
        # Authentication middleware
        def login_required(route_function):
            """Decorator to require login for routes"""
            def wrapper(*args, **kwargs):
                if not session.get('logged_in'):
                    return redirect(url_for('login'))
                return route_function(*args, **kwargs)
            # Preserve the original function name and attributes
            wrapper.__name__ = route_function.__name__
            return wrapper
        
        # API Authentication for programmatic access
        def api_authenticate():
            """Authenticate API requests with PIN"""
            # Support session-based auth for browser requests
            if session.get('logged_in'):
                return True
                
            # Support token-based auth for programmatic access
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                # Extract PIN from Bearer token
                pin = auth_header.split(' ')[1]
                return validate_pin(pin)
                
            return False
        
        # Login routes
        @self.app.route('/', methods=['GET', 'POST'])
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login page"""
            error = None
            if request.method == 'POST':
                pin = request.form.get('pin')
                if validate_pin(pin):
                    session['logged_in'] = True
                    flash('You were successfully logged in')
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid PIN'
            
            return render_template('login.html', error=error)
        
        @self.app.route('/logout', methods=['GET'])
        def logout():
            """Logout route"""
            session.pop('logged_in', None)
            flash('You were logged out')
            return redirect(url_for('login'))
        
        # Dashboard
        @self.app.route('/dashboard', methods=['GET'])
        @login_required
        def dashboard():
            """Dashboard page showing system status"""
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
            alerts = get_alerts(5)  # Get 5 most recent alerts
            unread_alerts = sum(1 for a in alerts if not a.get('read', False))
            
            # Format timestamps for display
            formatted_alerts = []
            for alert in alerts:
                alert_copy = alert.copy()
                if isinstance(alert_copy.get('timestamp'), (int, float)):
                    alert_copy['timestamp'] = datetime.fromtimestamp(
                        alert_copy['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                formatted_alerts.append(alert_copy)
            
            return render_template('dashboard.html', 
                                  system_active=system_active,
                                  devices=devices,
                                  active_devices=active_devices,
                                  total_devices=len(devices),
                                  alerts=formatted_alerts,
                                  unread_alerts=unread_alerts,
                                  total_alerts=len(get_alerts()))
        
        # Alerts
        @self.app.route('/alerts', methods=['GET'])
        @login_required
        def alerts_page():
            """Alerts page showing all alerts"""
            unread_only = request.args.get('unread_only') == 'true'
            
            # Get all alerts
            alerts = get_alerts(unread_only=unread_only)
            
            # Format timestamps for display
            formatted_alerts = []
            for i, alert in enumerate(alerts):
                alert_copy = alert.copy()
                alert_copy['index'] = i  # Add index for marking as read
                if isinstance(alert_copy.get('timestamp'), (int, float)):
                    alert_copy['timestamp'] = datetime.fromtimestamp(
                        alert_copy['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                
                # Check if alert has associated images
                alert_copy['has_image'] = False
                if 'sensor_type' in alert_copy:
                    sensor_type = alert_copy['sensor_type']
                    if sensor_type in ['motion', 'camera']:
                        alert_copy['has_image'] = True
                
                formatted_alerts.append(alert_copy)
            
            return render_template('alerts.html', 
                                  alerts=formatted_alerts,
                                  unread_only=unread_only,
                                  total_unread=sum(1 for a in alerts if not a.get('read', False)))
        
        @self.app.route('/alerts/mark_read/<int:alert_index>', methods=['POST'])
        @login_required
        def mark_alert_read_route(alert_index):
            """Mark alert as read"""
            success = mark_alert_as_read(alert_index)
            if success:
                flash('Alert marked as read')
            else:
                flash('Failed to mark alert as read')
            
            # Return to referring page or alerts page
            return redirect(request.referrer or url_for('alerts_page'))
        
        @self.app.route('/alerts/mark_all_read', methods=['POST'])
        @login_required
        def mark_all_alerts_read():
            """Mark all alerts as read"""
            alerts = get_alerts()
            for i in range(len(alerts)):
                mark_alert_as_read(i)
            
            flash('All alerts marked as read')
            return redirect(url_for('alerts_page'))
        
        # Sensors
        @self.app.route('/sensors', methods=['GET'])
        @login_required
        def sensors_page():
            """Sensors page showing all sensor devices"""
            # Get device and sensor information
            devices = get_sensor_devices()
            statuses = get_sensor_status()
            
            # Format data for template
            sensors = []
            for device_id, device_data in devices.items():
                # Format last seen time
                last_seen = device_data.get('last_seen', '')
                if last_seen:
                    try:
                        last_seen = datetime.fromisoformat(last_seen)
                        last_seen_str = last_seen.strftime("%Y-%m-%d %H:%M:%S")
                        # Calculate if device is active (seen in last hour)
                        active = (datetime.now() - last_seen).total_seconds() < 3600
                    except (ValueError, TypeError):
                        last_seen_str = 'Unknown'
                        active = False
                else:
                    last_seen_str = 'Never'
                    active = False
                
                # Get sensor status for this device
                device_status = statuses.get(device_id, {})
                
                # Format timestamps in status
                for sensor, data in device_status.items():
                    if isinstance(data.get('timestamp'), (int, float)):
                        data['timestamp_str'] = datetime.fromtimestamp(
                            data['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                
                sensors.append({
                    'id': device_id,
                    'name': device_data.get('name', 'Unknown Device'),
                    'ip': device_data.get('ip', 'Unknown'),
                    'last_seen': last_seen_str,
                    'active': active,
                    'status': device_status
                })
            
            return render_template('sensors.html', sensors=sensors)
        
        # Images
        @self.app.route('/images', methods=['GET'])
        @login_required
        def images_page():
            """Images page showing capture images"""
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
                            'path': f'/image/{filename}',
                            'timestamp': datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                            'sensor_type': sensor_type
                        })
            
            # Sort by timestamp (newest first)
            images.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Filter by sensor type if requested
            sensor_filter = request.args.get('sensor_type')
            if sensor_filter:
                images = [img for img in images if img['sensor_type'] == sensor_filter]
            
            # Get unique sensor types for filter dropdown
            sensor_types = sorted(set(img['sensor_type'] for img in images))
            
            return render_template('images.html', 
                                  images=images, 
                                  sensor_types=sensor_types, 
                                  current_filter=sensor_filter)
        
        @self.app.route('/image/<path:image_path>', methods=['GET'])
        @login_required
        def get_image(image_path):
            """Get an image from the captures directory"""
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
                return "Image not found", 404
        
        # Settings
        @self.app.route('/settings', methods=['GET', 'POST'])
        @login_required
        def settings_page():
            """Settings page"""
            if request.method == 'POST':
                # Toggle system state if requested
                if 'toggle_system' in request.form:
                    toggle_system_state()
                    flash(f'System {"deactivated" if get_setting("system_active", False) else "activated"}')
                
                # Other settings could be handled here
            
            system_active = get_setting("system_active", False)
            
            return render_template('settings.html', system_active=system_active)
        
        # API endpoints that return JSON (for AJAX requests and programmatic access)
        @self.app.route('/api/status', methods=['GET'])
        def api_status():
            """API endpoint for system status"""
            if not api_authenticate():
                return jsonify({'error': 'Unauthorized'}), 401
                
            system_active = get_setting("system_active", False)
            devices = get_sensor_devices()
            active_devices = 0
            
            for device_id, device_data in devices.items():
                if 'last_seen' in device_data:
                    try:
                        last_seen = datetime.fromisoformat(device_data['last_seen'])
                        if (datetime.now() - last_seen).total_seconds() < 3600:
                            active_devices += 1
                    except (ValueError, TypeError):
                        pass
            
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
        
        @self.app.route('/api/toggle', methods=['POST'])
        def api_toggle():
            """API endpoint for toggling system state"""
            if not api_authenticate():
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
            
        @self.app.route('/api/alerts', methods=['GET'])
        def api_alerts():
            """API endpoint for alerts"""
            if not api_authenticate():
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
        def api_mark_alert_read(alert_index):
            """API endpoint to mark an alert as read"""
            if not api_authenticate():
                return jsonify({'error': 'Unauthorized'}), 401
                
            success = mark_alert_as_read(alert_index)
            
            return jsonify({
                'success': success,
                'message': 'Alert marked as read' if success else 'Failed to mark alert as read'
            })
            
        @self.app.route('/api/sensors', methods=['GET'])
        def api_sensors():
            """API endpoint for sensor information"""
            if not api_authenticate():
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
            
        @self.app.route('/api/images', methods=['GET'])
        def api_images():
            """API endpoint to list available capture images"""
            if not api_authenticate():
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
            
            # Filter by sensor type if requested
            sensor_filter = request.args.get('sensor_type')
            if sensor_filter:
                images = [img for img in images if img['sensor_type'] == sensor_filter]
            
            return jsonify({'images': images})
            
        @self.app.route('/api/images/<path:image_path>', methods=['GET'])
        def api_get_image(image_path):
            """API endpoint to get an image from the captures directory"""
            if not api_authenticate():
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
    
    def start(self):
        """Start the Web App server in a separate thread"""
        if self.running:
            print("Web App server is already running")
            return
        
        def run_server():
            """Function to run the server in a separate thread"""
            # Create a proper WSGI server instead of using app.run()
            self.server = make_server(self.host, self.port, self.app, threaded=True)
            self.server.timeout = 0.5  # Short timeout to handle shutdown requests
            
            # Run the server until shutdown event is set
            while not self.shutdown_event.is_set():
                self.server.handle_request()
        
        # Reset shutdown event
        self.shutdown_event.clear()
        
        # Start server in a daemon thread
        self.server_thread = Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.running = True
        
        print(f"Web App server started on {self.host}:{self.port}")
    
    def stop(self):
        """Stop the Web App server"""
        if not self.running:
            return
            
        # Signal shutdown and wait for the server to stop
        self.shutdown_event.set()
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
            
        self.running = False
        print("Web App server stopped")

# Create a global instance
web_app = WebAppServer(port=get_setting("network.web_port", 8090))