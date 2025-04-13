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

# Zakázať predvolené logovanie Flasku na zníženie spamu v konzole
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class WebAppServer:
    """Webový aplikačný server pre prístup cez prehliadač"""
    
    def __init__(self, host='0.0.0.0', port=8080):
        """Inicializácia webového aplikačného servera
        
        Args:
            host (str): Hostiteľ, na ktorom server počúva
            port (int): Port, na ktorom server počúva
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__, 
                        static_folder='web/static',
                        template_folder='web/templates')
        self.app.secret_key = os.urandom(24)  # Pre správu relácií
        self.running = False
        self.server = None
        self.server_thread = None
        self.shutdown_event = Event()
        self.setup_routes()
    
    def setup_routes(self):
        """Konfigurácia ciest webovej aplikácie"""
        
        # Pridanie procesora kontextu šablóny pre zahrnutie aktuálneho času
        @self.app.context_processor
        def inject_now():
            return {'now': datetime.now()}
        
        # Middleware pre autentifikáciu
        def login_required(route_function):
            """Dekorátor na vyžadovanie prihlásenia pre prístup k cestám"""
            def wrapper(*args, **kwargs):
                if not session.get('logged_in'):
                    return redirect(url_for('login'))
                return route_function(*args, **kwargs)
            # Zachovanie pôvodného názvu funkcie a atribútov
            wrapper.__name__ = route_function.__name__
            return wrapper
        
        # API autentifikácia pre programový prístup
        def api_authenticate():
            """Autentifikácia API požiadaviek pomocou PIN kódu"""
            # Podpora autentifikácie na základe relácií pre požiadavky z prehliadača
            if session.get('logged_in'):
                return True
                
            # Podpora autentifikácie na základe tokenov pre programový prístup
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                # Extrahovanie PIN kódu z Bearer tokenu
                pin = auth_header.split(' ')[1]
                return validate_pin(pin)
                
            return False
        
        # Cesty pre prihlásenie
        @self.app.route('/', methods=['GET', 'POST'])
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Prihlasovacia stránka"""
            error = None
            if request.method == 'POST':
                pin = request.form.get('pin')
                if validate_pin(pin):
                    session['logged_in'] = True
                    flash('Úspešne ste sa prihlásili')
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Neplatný PIN'
            
            return render_template('login.html', error=error)
        
        @self.app.route('/logout', methods=['GET'])
        def logout():
            """Cesta odhlásenia"""
            session.pop('logged_in', None)
            flash('Boli ste odhlásení')
            return redirect(url_for('login'))
        
        # Dashboard
        @self.app.route('/dashboard', methods=['GET'])
        @login_required
        def dashboard():
            """Stránka prístrojovej dosky zobrazujúca stav systému"""
            # Získanie stavu systému
            system_active = get_setting("system_active", False)
            
            # Získanie informácií o zariadeniach
            devices = get_sensor_devices()
            active_devices = 0
            now = datetime.now()
            
            for device_id, device_data in devices.items():
                if 'last_seen' in device_data:
                    try:
                        last_seen = datetime.fromisoformat(device_data['last_seen'])
                        # Add active flag to each device
                        device_data['active'] = (now - last_seen).total_seconds() < 3600  # Aktívne v poslednej hodine
                        if device_data['active']:
                            active_devices += 1
                    except (ValueError, TypeError):
                        device_data['active'] = False
                else:
                    device_data['active'] = False
            
            # Získanie informácií o upozorneniach
            alerts = get_alerts(5)  # Získanie 5 najnovších upozornení
            unread_alerts = sum(1 for a in alerts if not a.get('read', False))
            
            # Formátovanie časových pečiatok pre zobrazenie
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
        
        # Upozornenia
        @self.app.route('/alerts', methods=['GET'])
        @login_required
        def alerts_page():
            """Stránka upozornení zobrazujúca všetky upozornenia"""
            unread_only = request.args.get('unread_only') == 'true'
            
            # Získanie všetkých upozornení
            alerts = get_alerts(unread_only=unread_only)
            
            # Formátovanie časových pečiatok pre zobrazenie
            formatted_alerts = []
            for i, alert in enumerate(alerts):
                alert_copy = alert.copy()
                alert_copy['index'] = i  # Pridanie indexu pre označenie ako prečítané
                if isinstance(alert_copy.get('timestamp'), (int, float)):
                    alert_copy['timestamp'] = datetime.fromtimestamp(
                        alert_copy['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                
                # Kontrola, či má upozornenie súvisiace obrázky
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
            """Označenie upozornenia ako prečítané"""
            success = mark_alert_as_read(alert_index)
            if success:
                flash('Upozornenie označené ako prečítané')
            else:
                flash('Nepodarilo sa označiť upozornenie ako prečítané')
            
            # Návrat na odkazujúcu stránku alebo stránku upozornení
            return redirect(request.referrer or url_for('alerts_page'))
        
        @self.app.route('/alerts/mark_all_read', methods=['POST'])
        @login_required
        def mark_all_alerts_read():
            """Označenie všetkých upozornení ako prečítané"""
            alerts = get_alerts()
            for i in range(len(alerts)):
                mark_alert_as_read(i)
            
            flash('Všetky upozornenia označené ako prečítané')
            return redirect(url_for('alerts_page'))
        
        # Senzory
        @self.app.route('/sensors', methods=['GET'])
        @login_required
        def sensors_page():
            """Stránka senzorov zobrazujúca všetky senzorové zariadenia"""
            # Získanie informácií o zariadeniach a senzoroch
            devices = get_sensor_devices()
            statuses = get_sensor_status()
            
            # Formátovanie údajov pre šablónu
            sensors = []
            for device_id, device_data in devices.items():
                # Formátovanie času posledného videnia
                last_seen = device_data.get('last_seen', '')
                if last_seen:
                    try:
                        last_seen = datetime.fromisoformat(last_seen)
                        last_seen_str = last_seen.strftime("%Y-%m-%d %H:%M:%S")
                        # Výpočet, či je zariadenie aktívne (videné v poslednej hodine)
                        active = (datetime.now() - last_seen).total_seconds() < 3600
                    except (ValueError, TypeError):
                        last_seen_str = 'Neznáme'
                        active = False
                else:
                    last_seen_str = 'Nikdy'
                    active = False
                
                # Získanie stavu senzora pre toto zariadenie
                device_status = statuses.get(device_id, {})
                
                # Formátovanie časových pečiatok v stave
                for sensor_type, data in device_status.items():
                    # Check if data is a dictionary or string
                    if isinstance(data, dict) and isinstance(data.get('timestamp'), (int, float)):
                        data['timestamp_str'] = datetime.fromtimestamp(
                            data['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                
                sensors.append({
                    'id': device_id,
                    'name': device_data.get('name', 'Neznáme zariadenie'),
                    'ip': device_data.get('ip', 'Neznáma'),
                    'last_seen': last_seen_str,
                    'active': active,
                    'status': device_status
                })
            
            return render_template('sensors.html', sensors=sensors)
        
        # Obrázky
        @self.app.route('/images', methods=['GET'])
        @login_required
        def images_page():
            """Stránka obrázkov zobrazujúca zachytené obrázky"""
            # Získanie adresára so zachytenými obrázkami
            storage_path = get_setting("images.storage_path", "captures")
            
            # Ak nie je absolútna cesta, vytvorenie cesty relatívnej k projektu
            if not os.path.isabs(storage_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_path = os.path.join(base_dir, storage_path)
            
            # Zoznam obrázkov s ich metadátami
            images = []
            if os.path.exists(storage_path):
                for filename in os.listdir(storage_path):
                    if filename.endswith(('.jpg', '.jpeg', '.png')):
                        file_path = os.path.join(storage_path, filename)
                        timestamp = os.path.getmtime(file_path)
                        
                        # Pokus o extrakciu typu senzora z názvu súboru (formát: type_timestamp.jpg)
                        sensor_type = "neznámy"
                        if '_' in filename:
                            sensor_type = filename.split('_')[0]
                        
                        images.append({
                            'filename': filename,
                            'path': f'/image/{filename}',
                            'timestamp': datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                            'sensor_type': sensor_type
                        })
            
            # Zoradenie podľa časovej pečiatky (najnovšie prvé)
            images.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Filtrovanie podľa typu senzora, ak je vyžiadané
            sensor_filter = request.args.get('sensor_type')
            if sensor_filter:
                images = [img for img in images if img['sensor_type'] == sensor_filter]
            
            # Získanie jedinečných typov senzorov pre rozbaľovací zoznam filtra
            sensor_types = sorted(set(img['sensor_type'] for img in images))
            
            return render_template('images.html', 
                                  images=images, 
                                  sensor_types=sensor_types, 
                                  current_filter=sensor_filter)
        
        @self.app.route('/image/<path:image_path>', methods=['GET'])
        @login_required
        def get_image(image_path):
            """Získanie obrázka z adresára so zachytenými obrázkami"""
            # Získanie adresára so zachytenými obrázkami
            storage_path = get_setting("images.storage_path", "captures")
            
            # Ak nie je absolútna cesta, vytvorenie cesty relatívnej k projektu
            if not os.path.isabs(storage_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_path = os.path.join(base_dir, storage_path)
            
            # Vytvorenie úplnej cesty (zabezpečenie, že je v rámci adresára so zachytenými obrázkami kvôli bezpečnosti)
            file_path = os.path.join(storage_path, os.path.basename(image_path))
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_file(file_path)
            else:
                return "Obrázok nenájdený", 404
        
        # Nastavenia
        @self.app.route('/settings', methods=['GET', 'POST'])
        @login_required
        def settings_page():
            """Stránka nastavení"""
            if request.method == 'POST':
                # Prepnutie stavu systému, ak je požadované
                if 'toggle_system' in request.form:
                    toggle_system_state()
                    flash(f'Systém {"deaktivovaný" if get_setting("system_active", False) else "aktivovaný"}')
                
                # Tu by sa mohli spracovať ďalšie nastavenia
            
            system_active = get_setting("system_active", False)
            
            return render_template('settings.html', system_active=system_active)
        
        # API koncové body vracajúce JSON (pre AJAX požiadavky a programový prístup)
        @self.app.route('/api/status', methods=['GET'])
        def api_status():
            """API koncový bod pre stav systému"""
            if not api_authenticate():
                return jsonify({'error': 'Neautorizovaný'}), 401
                
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
            """API koncový bod pre prepínanie stavu systému"""
            if not api_authenticate():
                return jsonify({'error': 'Neautorizovaný'}), 401
                
            # Voliteľný parameter pre nový stav
            data = request.get_json() or {}
            new_state = data.get('active', None)
            
            toggled = toggle_system_state(new_state)
            current_state = get_setting("system_active", False)
            
            return jsonify({
                'success': toggled,
                'system_active': current_state,
                'message': f'Systém {"aktivovaný" if current_state else "deaktivovaný"}'
            })
            
        @self.app.route('/api/alerts', methods=['GET'])
        def api_alerts():
            """API koncový bod pre upozornenia"""
            if not api_authenticate():
                return jsonify({'error': 'Neautorizovaný'}), 401
                
            # Získanie informácií o upozorneniach, voliteľne filtrovaných podľa počtu a stavu prečítania
            count = request.args.get('count', None)
            if count:
                try:
                    count = int(count)
                except ValueError:
                    count = None
                    
            unread_only = request.args.get('unread', 'false').lower() == 'true'
            
            alerts = get_alerts(count=count, unread_only=unread_only)
            
            # Formátovanie časových pečiatok pre JSON
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
            """API koncový bod pre označenie upozornenia ako prečítané"""
            if not api_authenticate():
                return jsonify({'error': 'Neautorizovaný'}), 401
                
            success = mark_alert_as_read(alert_index)
            
            return jsonify({
                'success': success,
                'message': 'Upozornenie označené ako prečítané' if success else 'Nepodarilo sa označiť upozornenie ako prečítané'
            })
            
        @self.app.route('/api/sensors', methods=['GET'])
        def api_sensors():
            """API koncový bod pre informácie o senzoroch"""
            if not api_authenticate():
                return jsonify({'error': 'Neautorizovaný'}), 401
                
            # Získanie informácií o zariadeniach a senzoroch
            devices = get_sensor_devices()
            statuses = get_sensor_status()
            
            # Formátovanie údajov pre JSON odpoveď
            result = []
            for device_id, device_data in devices.items():
                # Formátovanie časových pečiatok
                last_seen = device_data.get('last_seen', '')
                if last_seen:
                    try:
                        last_seen = datetime.fromisoformat(last_seen)
                        device_data['last_seen'] = last_seen.isoformat()
                    except ValueError:
                        pass
                
                # Získanie stavu senzora pre toto zariadenie
                device_status = statuses.get(device_id, {})
                
                # Formátovanie časových pečiatok v stave
                for sensor, data in device_status.items():
                    if isinstance(data.get('timestamp'), (int, float)):
                        data['timestamp'] = datetime.fromtimestamp(
                            data['timestamp']).isoformat()
                
                result.append({
                    'id': device_id,
                    'name': device_data.get('name', 'Neznáme zariadenie'),
                    'ip': device_data.get('ip', 'Neznáma'),
                    'last_seen': device_data.get('last_seen', ''),
                    'status': device_status
                })
            
            return jsonify({'sensors': result})
            
        @self.app.route('/api/images', methods=['GET'])
        def api_images():
            """API koncový bod na výpis dostupných zachytených obrázkov"""
            if not api_authenticate():
                return jsonify({'error': 'Neautorizovaný'}), 401
                
            # Získanie adresára so zachytenými obrázkami
            storage_path = get_setting("images.storage_path", "captures")
            
            # Ak nie je absolútna cesta, vytvorenie cesty relatívnej k projektu
            if not os.path.isabs(storage_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_path = os.path.join(base_dir, storage_path)
            
            # Zoznam obrázkov s ich metadátami
            images = []
            if os.path.exists(storage_path):
                for filename in os.listdir(storage_path):
                    if filename.endswith(('.jpg', '.jpeg', '.png')):
                        file_path = os.path.join(storage_path, filename)
                        timestamp = os.path.getmtime(file_path)
                        
                        # Pokus o extrakciu typu senzora z názvu súboru (formát: type_timestamp.jpg)
                        sensor_type = "neznámy"
                        if '_' in filename:
                            sensor_type = filename.split('_')[0]
                        
                        images.append({
                            'filename': filename,
                            'path': f'/api/images/{filename}',
                            'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                            'sensor_type': sensor_type
                        })
            
            # Zoradenie podľa časovej pečiatky (najnovšie prvé)
            images.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Filtrovanie podľa typu senzora, ak je vyžiadané
            sensor_filter = request.args.get('sensor_type')
            if sensor_filter:
                images = [img for img in images if img['sensor_type'] == sensor_filter]
            
            return jsonify({'images': images})
            
        @self.app.route('/api/images/<path:image_path>', methods=['GET'])
        def api_get_image(image_path):
            """API koncový bod na získanie obrázka z adresára so zachytenými obrázkami"""
            if not api_authenticate():
                return jsonify({'error': 'Neautorizovaný'}), 401
                
            # Získanie adresára so zachytenými obrázkami
            storage_path = get_setting("images.storage_path", "captures")
            
            # Ak nie je absolútna cesta, vytvorenie cesty relatívnej k projektu
            if not os.path.isabs(storage_path):
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                storage_path = os.path.join(base_dir, storage_path)
            
            # Vytvorenie úplnej cesty (zabezpečenie, že je v rámci adresára so zachytenými obrázkami kvôli bezpečnosti)
            file_path = os.path.join(storage_path, os.path.basename(image_path))
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_file(file_path)
            else:
                return jsonify({'error': 'Obrázok nenájdený'}), 404

        @self.app.route('/api/grace_period_status', methods=['GET'])
        def api_grace_period_status():
            """API endpoint to check the status of any active grace period"""
            if not api_authenticate():
                return jsonify({'error': 'Unauthorized'}), 401
                
            # Import notification service here to avoid circular imports
            from notification_service import notification_service
            
            # Get current grace period status
            grace_status = notification_service.get_grace_period_status()
            
            if grace_status and grace_status.get('active'):
                # Return active grace period details
                return jsonify({
                    'active': True,
                    'alert_data': grace_status.get('alert_data', {}),
                    'seconds_remaining': notification_service.get_grace_period_remaining_time()
                })
            else:
                # No active grace period
                return jsonify({
                    'active': False
                })
    
    def cancel_all_alerts(self, instance):
        """Cancel all active alerts and disable system"""
        from notification_service import notification_service
        from config.settings import toggle_system_state
        
        # Disable the system
        toggle_system_state(False)
        
        # Cancel grace periods
        notification_service.cancel_grace_period()
        
        # Stop any playing alarms
        notification_service.stop_alarm()
        
        # Refresh the alerts display
        self.refresh_alerts()
    
    def start(self):
        """Spustenie webového aplikačného servera v samostatnom vlákne"""
        if self.running:
            print("Webový aplikačný server je už spustený")
            return
        
        def run_server():
            """Funkcia na spustenie servera v samostatnom vlákne"""
            # Vytvorenie správneho WSGI servera namiesto použitia app.run()
            self.server = make_server(self.host, self.port, self.app, threaded=True)
            self.server.timeout = 0.5  # Krátky časový limit na spracovanie požiadaviek na vypnutie
            
            # Spustenie servera, kým nie je nastavená udalosť vypnutia
            while not self.shutdown_event.is_set():
                self.server.handle_request()
        
        # Resetovanie udalosti vypnutia
        self.shutdown_event.clear()
        
        # Spustenie servera v démonovom vlákne
        self.server_thread = Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.running = True
        
        print(f"Webový aplikačný server spustený na {self.host}:{self.port}")
    
    def stop(self):
        """Zastavenie webového aplikačného servera"""
        if not self.running:
            return
            
        # Signalizácia vypnutia a čakanie na zastavenie servera
        self.shutdown_event.set()
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
            
        self.running = False
        print("Webový aplikačný server zastavený")

# Vytvorenie globálnej inštancie
web_app = WebAppServer(port=get_setting("network.web_port", 8090))