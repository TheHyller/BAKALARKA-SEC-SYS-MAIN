# Bezpečnostný Systém pre Domácnosť - Technická Dokumentácia

## Prehľad Systému

Tento dokument poskytuje podrobný technický prehľad aplikácie bezpečnostného systému pre domácnosť. Systém pozostáva z dvoch hlavných komponentov:

1. **SEND Komponent**: Beží na zariadeniach Raspberry Pi, komunikuje so senzormi a kamerou
2. **REC Komponent**: Beží na monitorovacom zariadení, poskytuje používateľské rozhranie a správu upozornení

## Architektúra

Systém implementuje distribuovanú architektúru klient-server:

- Viacero **SEND** zariadení (klientov) sa môže pripojiť k jednému **REC** serveru
- Každé SEND zariadenie má jedinečné ID a môže fungovať nezávisle
- REC komponent poskytuje centralizované monitorovanie a konfiguráciu 
- Sieťová komunikácia prebieha prostredníctvom UDP, TCP a vysielania pre objavovanie zariadení

### Komunikačné Protokoly

| Protokol | Port | Účel |
|----------|------|------|
| UDP | 8081 | Aktualizácie stavu senzorov, malé a časté správy |
| TCP | 8080 | Prenos obrázkov, spoľahlivé doručovanie zachytených snímok |
| UDP (Discovery) | 8082 | Objavovanie zariadení a sieťová konfigurácia |

## SEND Komponent

### Základná Funkcionalita

SEND komponent (`SEND/SEND.py`) je zodpovedný za:

1. Rozhranie s hardvérovými senzormi (pohyb, dvere, okno) prostredníctvom GPIO pinov
2. Zachytávanie snímok pri detekcii bezpečnostných udalostí
3. Odosielanie aktualizácií stavu v reálnom čase do REC komponentu
4. Vysielanie svojej prítomnosti prostredníctvom správ pre objavovanie
5. Udržiavanie jedinečnej identity zariadenia

### Kľúčové Triedy

#### `SecuritySender`

Hlavná trieda, ktorá orchestruje odosielací komponent:

```python
def __init__(self):
    # Inicializácia s jedinečným ID zariadenia, nastavením kamery, atď.

def _on_motion_detected(self, channel):
    # Volaná pri spustení senzora pohybu
    # Odosiela aktualizáciu a zachytáva snímku

def _on_door_change(self, channel):
    # Volaná pri zmene stavu dverového senzora
    # Odosiela aktualizáciu a zachytáva snímku ak sa otvorí

def _on_window_change(self, channel):
    # Volaná pri zmene stavu okenného senzora
    # Odosiela aktualizáciu a zachytáva snímku ak sa otvorí

def _capture_image(self, trigger_type):
    # Zachytáva snímku z kamery
    # Odosiela snímku do REC komponentu

def _send_sensor_update(self, sensor_type, status):
    # Odosiela UDP správu so stavom senzora
    # Formát: SENSOR:{DEVICE_ID}:{DEVICE_NAME}:{TYPE}:{STATUS}

def _discovery_service(self):
    # Vysiela prítomnosť v sieti
    # Odpovedá na požiadavky na objavenie
```

## REC Komponent

### Základná Funkcionalita

REC komponent poskytuje:

1. Grafické používateľské rozhranie pre monitorovanie a konfiguráciu
2. Zobrazovanie bezpečnostných udalostí v reálnom čase 
3. Sieťových poslucháčov pre rôzne komunikačné kanály
4. Trvalé ukladanie nastavení a stavu zariadenia
5. Autentifikáciu prostredníctvom PIN kódu
6. Prehľadnú prístrojovú dosku pre rýchle monitorovanie všetkých zariadení
7. Webové rozhranie pre vzdialený prístup k monitorovaniu a konfigurácii

### Podrobná Analýza Kódu

#### Hlavná Aplikácia (`app.py`)

Trieda `MainApp` slúži ako vstupný bod aplikácie a kontrolér:

```python
class MainApp(App):
    def build(self):
        # Načítanie nastavení aplikácie
        settings = load_settings()
        print("DEBUG: Aplikácia sa spúšťa s načítanými nastaveniami")
        
        # Spustenie poslucháčov
        self.discovery_listener = DiscoveryListener()
        self.discovery_listener.start()
        
        self.udp_listener = UDPListener()
        self.udp_listener.start()
        
        self.tcp_listener = TCPListener()
        self.tcp_listener.start()
        
        print("DEBUG: Sieťoví poslucháči spustení pre komunikáciu so senzormi")
        
        # Vytvorenie správcu obrazoviek
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(AlertsScreen(name='alerts'))
        sm.add_widget(DashboardScreen(name='dashboard'))  # Pridanie obrazovky dashboardu
        
        # Nastavenie počiatočnej obrazovky
        sm.current = 'login'
        
        return sm
    
    def on_stop(self):
        # Zastavenie poslucháčov pri zatvorení aplikácie
        if hasattr(self, 'discovery_listener'):
            self.discovery_listener.stop()
        if hasattr(self, 'udp_listener'):
            self.udp_listener.stop()
        if hasattr(self, 'tcp_listener'):
            self.tcp_listener.stop()
```

Kľúčové aspekty:
- Aplikácia nasleduje dizajn frameworku Kivy s `ScreenManager` pre navigáciu medzi obrazovkami
- Rozsiahlo sa používa vláknenie pre sieťovú komunikáciu (všetci poslucháči bežia v samostatných vláknach)
- Zdroje sú správne spravované s inicializáciou v `build()` a čistením v `on_stop()`
- Prechody medzi obrazovkami riadia tok aplikácie
- Aplikácia obsahuje 5 hlavných obrazoviek: prihlásenie, hlavnú obrazovku, nastavenia, upozornenia a prístrojovú dosku

#### Systém Upozornení (`alerts_screen.py`)

Systém upozornení demonštruje, ako sú bezpečnostné udalosti zobrazované používateľom:

```python
class AlertsScreen(Screen):
    def __init__(self, **kwargs):
        super(AlertsScreen, self).__init__(**kwargs)
        
        # Vytvorenie rozloženia UI
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Nastavenie posúvateľného zoznamu upozornení
        scroll_view = ScrollView(size_hint_y=0.7)
        self.alerts_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.alerts_list.bind(minimum_height=self.alerts_list.setter('height'))
        scroll_view.add_widget(self.alerts_list)
        
        # Pridanie upozornení do zoznamu
        self.add_alert("Pohyb zaznamenaný - Predné dvere", "2025-03-24 10:15:22")
        # Viac upozornení...
        
    def add_alert(self, message, timestamp):
        """Pridanie upozornenia do zoznamu upozornení"""
        alert_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        alert_layout.add_widget(Label(text=message, font_size=18, halign='left'))
        alert_layout.add_widget(Label(text=timestamp, font_size=14, halign='left'))
        self.alerts_list.add_widget(alert_layout)
```

Detaily implementácie:
- Systém upozornení používa posúvateľné zobrazenie na spracovanie potenciálne mnohých upozornení
- Každé upozornenie sa zobrazuje s obsahom správy a časovou pečiatkou
- Metóda `add_alert()` vytvára štruktúrované zobrazenie pre každé upozornenie
- UI je navrhnuté tak, aby bolo responzívne s flexibilným rozmerovaním
- Navigácia je riešená prostredníctvom metódy `go_back()`

#### Sieťoví Poslucháči (`listeners.py`)

Poslucháči spracúvajú rôzne typy prichádzajúcej sieťovej komunikácie:

##### DiscoveryListener

```python
class DiscoveryListener(threading.Thread):
    def run(self):
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Počúvanie na vysielania objavovania
        try:
            self.socket.bind(('0.0.0.0', self.port))
            while self.running:
                data, address = self.socket.recvfrom(1024)
                data = data.decode('utf-8')
                
                # Spracovanie správ objavovania
                if data.startswith("SECURITY_DEVICE:ONLINE:"):
                    parts = data.split(":")
                    device_id = parts[2]
                    device_name = parts[3]
                    # Registrácia zariadenia...
                    
                # Odoslanie odpovede na požiadavky objavovania
                if data.startswith("DISCOVER:"):
                    # Odpoveď s informáciami o systéme...
```

Detaily implementácie:
- Používa vláknenie na zabránenie blokovania hlavného vlákna UI
- Implementuje UDP socketové programovanie s možnosťami vysielania
- Parsuje protokolovo špecifické správy pre objavovanie zariadení
- Umožňuje automatické objavovanie SEND zariadení v sieti
- Elegantne zvláda sieťové chyby a vypnutie socketov

##### UDPListener

```python
class UDPListener(threading.Thread):
    def run(self):
        # Inicializácia UDP socketu
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            self.socket.bind(('0.0.0.0', self.port))
            while self.running:
                # Príjem aktualizácií senzorov
                data, address = self.socket.recvfrom(1024)
                data = data.decode('utf-8')
                
                # Spracovanie údajov zo senzora
                if data.startswith("SENSOR:"):
                    parts = data.split(":")
                    device_id = parts[1]
                    device_name = parts[2]
                    sensor_type = parts[3]
                    status = parts[4]
                    
                    # Aktualizácia informácií o zariadení a stave senzora
                    # ...
```

Detaily implementácie:
- Konfigurovaný pre ľahkú UDP komunikáciu pre aktualizácie senzorov
- Zahŕňa parsovanie protokolu pre formát aktualizácie senzorov
- Aktualizácie sú okamžite dostupné prostredníctvom systému spätného volania
- Navrhnutý pre vysokofrekvenčné aktualizácie s nízkou latenciou

##### TCPListener

```python
class TCPListener(threading.Thread):
    def run(self):
        # Inicializácia TCP server socketu
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(5)
            
            while self.running:
                # Prijatie pripojení klientov
                client, address = self.socket.accept()
                
                # Vytvorenie vlákna na obsluhu tohto klienta
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
    def _handle_client(self, client, address):
        # Príjem hlavičky s typom obsahu a veľkosťou
        # Príjem obrazových údajov alebo iného veľkého obsahu
        # Spracovanie na základe typu obsahu
        # ...
```

Detaily implementácie:
- Používa spojovo orientovaný TCP pre spoľahlivý prenos údajov
- Implementuje vláknový server na spracovanie viacerých klientskych pripojení
- Navrhnutý pre väčšie dátové prenosy, ako sú prenosy obrázkov
- Zahŕňa protokol na identifikáciu typu obsahu a určenie veľkosti
- Podporuje prenos plných binárnych údajov

#### Vzory Implementácie UI

Systém používa konzistentné vzory UI naprieč obrazovkami:

1. **Inicializácia Obrazovky**:
```python
def __init__(self, **kwargs):
    super(ScreenClassName, self).__init__(**kwargs)
    layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
    # Pridanie widgetov do rozloženia
    self.add_widget(layout)
```

2. **Hierarchia Widgetov**:
```
Screen
└── BoxLayout (hlavné rozloženie)
    ├── Hlavička (Label)
    ├── Oblasť Obsahu (napr. ScrollView s GridLayout)
    └── Ovládacie Tlačidlá (napr. tlačidlo Späť)
```

3. **Vzor Navigácie**:
```python
def go_back(self, instance):
    self.manager.current = 'main'  # Návrat na predchádzajúcu obrazovku
```

4. **Vzor Zobrazenia Dát** (napr. z `AlertsScreen`):
```python
def add_alert(self, message, timestamp):
    """Pridanie upozornenia do zoznamu upozornení"""
    alert_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
    alert_layout.add_widget(Label(text=message, font_size=18, halign='left'))
    alert_layout.add_widget(Label(text=timestamp, font_size=14, halign='left'))
    self.alerts_list.add_widget(alert_layout)
```

#### Implementácia Prístrojovej Dosky (`dashboard_screen.py`)

Prístrojová doska používa komponentový prístup s opätovne použiteľnými widgetmi:

```python
class SensorCard(BoxLayout):
    """Widget na zobrazenie jedného senzorového zariadenia"""
    
    def __init__(self, device_id, device_data, **kwargs):
        super(SensorCard, self).__init__(**kwargs)
        self.device_id = device_id
        # Nastavenie rozloženia karty a obsahu
        
    def update_status(self, sensor_status):
        """Aktualizácia zobrazenia stavu senzora"""
        self.status_area.clear_widgets()
        
        for sensor_type, data in sensor_status.items():
            # Pridanie vizuálnych indikátorov pre každý typ senzora
```

Detaily implementácie:
- Používa vlastné opätovne použiteľné widgety (`SensorCard`) pre každé zariadenie
- Implementuje mechanizmus dynamickej aktualizácie pre zmeny stavu v reálnom čase
- Používa vizuálne indikátory (farby) na zobrazenie rôznych stavov
- Spravuje viacero typov senzorov na zariadení
- Aktualizuje sa automaticky prostredníctvom načítavania alebo spätných volaní udalostí

#### Správa Nastavení (`config/settings.py`)

Modul nastavení poskytuje centralizovaný konfiguračný systém:

```python
def load_settings():
    """Načítanie nastavení zo súboru alebo vytvorenie predvolených nastavení"""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return create_default_settings()

def save_settings():
    """Uloženie aktuálnych nastavení do súboru"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception:
        return False

def get_setting(key, default=None):
    """Získanie nastavenia podľa kľúča s voliteľnou predvolenou hodnotou"""
    keys = key.split('.')
    current = settings
    
    for k in keys:
        if k not in current:
            return default
        current = current[k]
    
    return current

def update_setting(key, value):
    """Aktualizácia nastavenia a uloženie do súboru"""
    keys = key.split('.')
    current = settings
    
    # Navigácia na príslušný vnorený slovník
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    # Aktualizácia hodnoty
    current[keys[-1]] = value
    return save_settings()
```

Detaily implementácie:
- Používa JSON pre ľudsky čitateľné ukladanie konfigurácie
- Podporuje vnorené konfigurácie prostredníctvom bodkovej notácie (napr. `network.tcp_port`)
- Poskytuje predvolené hodnoty pre chýbajúce konfigurácie
- Elegantne zvláda výnimky pri vstupe/výstupe súborov
- Udržiava vyrovnávaciu pamäť nastavení počas behu pre výkon

### Autentifikačný Systém (`login_screen.py`)

Autentifikačný systém založený na PIN kóde:

```python
def on_enter_pressed(self, instance):
    """Spracovanie stlačenia tlačidla Enter"""
    if validate_pin(self.pin_input):
        self.manager.current = 'main'
        self.pin_input = ""
        self.pin_display.text = ""
        self.status_label.text = "Zadajte PIN pre prístup do systému"
    else:
        self.status_label.text = "Neplatný PIN. Skúste znova."
        self.pin_input = ""
        self.pin_display.text = ""
        
def on_button_press(self, instance):
    """Spracovanie stlačení číselných tlačidiel"""
    if len(self.pin_input) < 4:  # Obmedzenie PIN na 4 čísla
        self.pin_input += instance.text
        self.pin_display.text = "*" * len(self.pin_input)
```

Detaily implementácie:
- Používa virtuálnu klávesnicu pre bezpečné zadávanie PIN kódu
- Maskuje vstup PIN kódu hviezdičkami pre súkromie
- Obmedzuje PIN na štandardné 4 číslice
- Poskytuje okamžitú spätnú väzbu pri zlyhaniach autentifikácie
- Validuje voči šifrovanému alebo hašovanému PIN kódu v nastaveniach

### Webové Rozhranie (`web_app.py`)

Systém poskytuje webové rozhranie pre vzdialený prístup:

```python
def create_web_app():
    """Vytvorenie Flask webovej aplikácie"""
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'web/templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'web/static'))
    app.secret_key = 'security_system_secret_key'  # Pre správu relácie
    
    @app.route('/')
    def index():
        """Hlavná trasa - presmerovanie na prihlásenie alebo prístrojovú dosku"""
        if 'logged_in' in session and session['logged_in']:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
        
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Prihlasovacia stránka s odoslaním formulára"""
        error = None
        # Spracovanie prihlásenia...
        
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Prístrojová doska so stavom zariadení"""
        devices = get_devices()
        system_active = get_setting('system_active', False)
        return render_template('dashboard.html', 
                              devices=devices, 
                              system_active=system_active)
    
    # Ďalšie trasy...
    
    return app
```

Detaily implementácie:
- Používa framework Flask pre ľahké vytváranie webových rozhraní
- Implementuje správu relácií pre bezpečnú autentifikáciu
- Obsahuje rozhrania API pre mobilné aplikácie alebo iné klientské aplikácie
- Používa šablóny pre konzistentnú prezentáciu údajov
- Implementuje zabezpečené trasy s dekorátorom `@login_required`
- Používa Bootstrap pre responzívny dizajn vhodný pre mobily aj počítače

#### Rozhranie Mobilného API (`mobile_api.py`)

Systém poskytuje API rozhranie pre mobilné aplikácie:

```python
def register_mobile_api(app):
    """Registrácia trás API pre mobilnú aplikáciu na Flask aplikácii"""
    
    @app.route('/api/login', methods=['POST'])
    def api_login():
        """API koncový bod pre prihlásenie z mobilnej aplikácie"""
        data = request.get_json()
        if not data or 'pin' not in data:
            return jsonify({'error': 'Chýbajúce prihlasovacie údaje'}), 400
            
        pin = data['pin']
        if validate_pin(pin):
            token = generate_auth_token()
            # Uloženie tokenu pre budúce požiadavky
            return jsonify({'success': True, 'token': token})
        
        return jsonify({'error': 'Neplatné prihlasovacie údaje'}), 401
        
    @app.route('/api/devices', methods=['GET'])
    @api_auth_required
    def api_get_devices():
        """API koncový bod pre získanie zoznamu zariadení"""
        devices = get_devices()
        return jsonify({'devices': devices})
        
    @app.route('/api/alerts', methods=['GET'])
    @api_auth_required
    def api_get_alerts():
        """API koncový bod pre získanie zoznamu upozornení"""
        start = request.args.get('start', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        alerts = get_alerts(start, limit)
        return jsonify({'alerts': alerts})
        
    # Ďalšie API koncové body...
```

Detaily implementácie:
- Používa RESTful dizajn API pre štandardizovanú komunikáciu
- Implementuje autentifikáciu založenú na tokenoch pre bezpečný mobilný prístup
- Poskytuje filtrovanie a stránkovanie pre efektívne načítanie údajov
- Vracia odpovede JSON pre ľahkú integráciu s mobilnými platformami
- Obsahuje správu chýb a validáciu vstupu pre robustnosť

## Tok Dát

### Spracovanie Udalostí Senzorov

Keď sa aktivuje senzor, nastane nasledujúci tok:

1. **Hardvérový Spúšťač**: Fyzický senzor zmení stav (napr. detekcia pohybu)
2. **GPIO Udalosť**: Prerušenie GPIO na Raspberry Pi spúšťa callback v SEND komponente
```python
def _setup_gpio(self):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(CONFIG["motion_pin"], GPIO.IN)
    GPIO.add_event_detect(CONFIG["motion_pin"], GPIO.RISING, callback=self._on_motion_detected)
```

3. **Spracovateľ Udalostí**: Callback spracuje udalosť senzora
```python
def _on_motion_detected(self, channel):
    logger.info("Pohyb detekovaný")
    self._send_sensor_update("motion", "DETECTED")
    self._capture_image("motion")
```

4. **Sieťový Prenos**: Aktualizácia stavu sa odosiela cez UDP
```python
def _send_sensor_update(self, sensor_type, status):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = f"SENSOR:{CONFIG['device_id']}:{CONFIG['device_name']}:{sensor_type}:{status}"
    sock.sendto(message.encode(), (CONFIG["receiver_ip"], CONFIG["udp_port"]))
```

5. **REC Príjem**: UDP poslucháč prijme aktualizáciu stavu
```python
# V UDPListener
data, address = self.socket.recvfrom(1024)
data = data.decode('utf-8')
# Spracovanie SENSOR: správy...
```

6. **Aktualizácia Databázy**: Stav uložený v nastaveniach a databáze
```python
# Uloženie aktualizovaného stavu senzora
update_sensor_status(device_id, sensor_type, status)
```

7. **Aktualizácia UI**: Prístrojová doska a upozornenia aktualizované na zobrazenie nového stavu
```python
# V MainScreen alebo DashboardScreen
def update_sensor_ui(self, data, address):
    # Parsovanie údajov zo senzora
    # Aktualizácia príslušných prvkov UI
    # Pridanie do upozornení, ak je to potrebné
```

8. **Generovanie Upozornení**: Ak je systém aktivovaný, vytvorí sa upozornenie
```python
# Kontrola, či je systém aktivovaný
if get_setting("system_active", False):
    # Vytvorenie upozornenia
    alerts_screen = self.manager.get_screen('alerts')
    alerts_screen.add_alert(f"{sensor_type.capitalize()} senzor aktivovaný", timestamp)
```

9. **Zvukové Upozornenia**: Prehratie zvuku alarmu pre kritické upozornenia
```python
# V SoundManager
def play_alarm():
    """Prehrá zvuk alarmu"""
    if self.sound:
        self.sound.play()
```

10. **Notifikácie**: Odoslanie upozornení prostredníctvom notifikačnej služby
```python
# V NotificationService
def send_notification(title, message):
    """Odosiela notifikáciu prostredníctvom nakonfigurovaných kanálov"""
    # Odoslanie e-mailu, SMS alebo push notifikácie
```

### Tok Zachytávania Obrázkov

1. **Spúšťacia Udalosť**: Udalosť senzora spúšťa zachytávanie obrázka
```python
def _capture_image(self, trigger_type):
    # Kontrola, či uplynulo dostatok času od posledného zachytenia
    current_time = time.time()
    if current_time - self.last_capture_time < CONFIG["capture_interval"]:
        return
        
    self.last_capture_time = current_time
    
    # Generovanie názvu súboru s časovou značkou
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{CONFIG['image_path']}/{trigger_type}_{timestamp}.jpg"
    
    # Zachytenie obrázka
    with self.camera as camera:
        camera.capture(filename)
    
    # Odoslanie obrázka príjemcovi
    self._send_image(filename, trigger_type)
```

2. **TCP Prenos**: Obrázok odoslaný cez TCP pre spoľahlivosť
```python
def _send_image(self, image_path, trigger_type):
    try:
        # Čítanie údajov obrázka
        with open(image_path, "rb") as img_file:
            image_data = img_file.read()
        
        # Pripojenie k príjemcovi
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((CONFIG["receiver_ip"], CONFIG["tcp_port"]))
        
        # Odoslanie hlavičky s metadátami
        header = f"IMAGE:{CONFIG['device_id']}:{trigger_type}:{len(image_data)}"
        sock.send(header.encode() + b'\n')
        
        # Odoslanie údajov obrázka
        sock.sendall(image_data)
    except Exception as e:
        logger.error(f"Nepodarilo sa odoslať obrázok: {e}")
    finally:
        sock.close()
```

3. **REC Príjem**: TCP poslucháč prijme a spracuje obrázok
```python
# V metóde _handle_client TCP poslucháča
header = client.recv(1024).decode('utf-8').strip()
if header.startswith("IMAGE:"):
    parts = header.split(":")
    device_id = parts[1]
    trigger_type = parts[2]
    size = int(parts[3])
    
    # Príjem údajov obrázka
    data = b''
    while len(data) < size:
        packet = client.recv(4096)
        if not packet:
            break
        data += packet
    
    # Uloženie obrázka a upozornenie UI
    # ...
```

4. **Ukladanie Obrázkov**: Obrázok uložený v REC komponente
5. **Aktualizácia Upozornení**: Príslušné upozornenia aktualizované s referenciou na obrázok
6. **Webové Rozhranie**: Obrázok dostupný prostredníctvom webového rozhrania v galérii obrázkov

### Tok Konfigurácie Systému

1. **Obrazovka Nastavení**: Používateľ upraví nastavenia
```python
def save_settings(self, instance):
    # Validácia vstupu
    try:
        tcp_port = int(self.tcp_port.text)
        udp_port = int(self.udp_port.text)
        discovery_port = int(self.discovery_port.text)
        
        # Aktualizácia nastavení
        network_settings = {
            "tcp_port": tcp_port,
            "udp_port": udp_port,
            "discovery_port": discovery_port
        }
        
        update_setting("network", network_settings)
        self.status_label.text = "Nastavenia uložené!"
    except ValueError:
        self.status_label.text = "Neplatné čísla portov"
```

2. **Aktualizácia Nastavení**: Zmeny zapísané do konfiguračného súboru
3. **Aplikovanie Nastavení**: Nové nastavenia nadobúdajú účinnosť
   - Pre niektoré nastavenia môže byť potrebný reštart komponentov
   - Sieťoví poslucháči zvyčajne potrebujú reštart s novými nastaveniami portov

4. **Vysielanie Zmien Nastavení**: Odoslanie aktualizácií do SEND zariadení
```python
def broadcast_settings_update(self):
    """Odosiela aktualizácie nastavení do všetkých známych zariadení"""
    devices = get_known_devices()
    updated_settings = get_shared_settings()
    
    for device in devices:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = f"SETTINGS_UPDATE:{json.dumps(updated_settings)}"
            sock.sendto(message.encode(), (device['ip'], device['udp_port']))
        except Exception as e:
            logger.error(f"Nepodarilo sa odoslať aktualizáciu nastavení zariadeniu {device['id']}: {e}")
        finally:
            sock.close()
```

## Témy a Prispôsobenie Používateľského Rozhrania (`theme_helper.py`)

Systém podporuje rôzne témy a personalizáciu používateľského rozhrania:

```python
class ThemeManager:
    """Správca tém pre aplikáciu"""
    
    def __init__(self):
        self.themes = {
            'light': {
                'background_color': [0.95, 0.95, 0.95, 1],
                'text_color': [0.2, 0.2, 0.2, 1],
                'primary_color': [0.2, 0.5, 0.8, 1],
                'accent_color': [0.8, 0.2, 0.2, 1],
                'card_color': [1, 1, 1, 1]
            },
            'dark': {
                'background_color': [0.1, 0.1, 0.1, 1],
                'text_color': [0.9, 0.9, 0.9, 1],
                'primary_color': [0.3, 0.6, 0.9, 1],
                'accent_color': [0.9, 0.3, 0.3, 1],
                'card_color': [0.2, 0.2, 0.2, 1]
            }
        }
        
        # Načítanie aktuálnej témy z nastavení
        self.current_theme = get_setting('ui.theme', 'light')
        
    def get_theme_color(self, color_name):
        """Získa farbu z aktuálnej témy"""
        theme = self.themes.get(self.current_theme, self.themes['light'])
        return theme.get(color_name, [0, 0, 0, 1])
        
    def apply_theme_to_widget(self, widget):
        """Aplikuje aktuálnu tému na widget"""
        if hasattr(widget, 'background_color'):
            widget.background_color = self.get_theme_color('background_color')
            
        if hasattr(widget, 'color'):
            widget.color = self.get_theme_color('text_color')
            
        # Rekurzívne aplikovanie témy na podwidgety
        if hasattr(widget, 'children'):
            for child in widget.children:
                self.apply_theme_to_widget(child)
                
    def switch_theme(self, theme_name):
        """Prepne na inú tému a uloží nastavenie"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            update_setting('ui.theme', theme_name)
            return True
        return False
```

## Body Rozšírenia

Systém je navrhnutý na rozšíriteľnosť:

1. **Dodatočné Senzory**: SEND komponent môže byť rozšírený o nové typy senzorov
2. **Vylepšená Autentifikácia**: Prihlasovacie systém by mohol byť rozšírený o viacfaktorovú autentifikáciu
3. **Cloudová Integrácia**: Systém by mohol byť rozšírený o zálohovanie udalostí do cloudového úložiska
4. **Mobilná Aplikácia**: Sprievodná mobilná aplikácia by mohla byť vyvinutá s použitím rovnakých protokolov
5. **Integrácie s Tretími Stranami**: Systém by mohol byť rozšírený o integrácie s HomeKit, Google Home alebo Alexa
6. **Analytika a Reportovanie**: Implementácia modelov strojového učenia pre odhalenie vzorov a identifikáciu falošných poplachov

## Správa Zvukov (`sound_manager.py`)

Systém zahŕňa správu zvukových oznámení a alarmov:

```python
class SoundManager:
    """Trieda pre správu zvukových efektov a alarmov v systéme"""
    
    def __init__(self):
        """Inicializácia správcu zvuku"""
        self.sound = None
        self.muted = get_setting('audio.muted', False)
        self.volume = get_setting('audio.volume', 1.0)
        self._load_sounds()
        
    def _load_sounds(self):
        """Načítanie zvukových efektov"""
        try:
            sound_file = os.path.join(os.path.dirname(__file__), 'assets/alarm.wav')
            self.sound = SoundLoader.load(sound_file)
            if self.sound:
                self.sound.volume = 0 if self.muted else self.volume
        except Exception as e:
            print(f"Chyba pri načítavaní zvuku: {e}")
            
    def play_alarm(self):
        """Prehrá zvuk alarmu"""
        if self.sound and not self.muted:
            self.sound.play()
            
    def stop_alarm(self):
        """Zastaví prehrávanie alarmu"""
        if self.sound:
            self.sound.stop()
            
    def set_volume(self, volume):
        """Nastaví hlasitosť v rozsahu 0.0 - 1.0"""
        self.volume = max(0.0, min(1.0, volume))
        update_setting('audio.volume', self.volume)
        if self.sound and not self.muted:
            self.sound.volume = self.volume
            
    def toggle_mute(self):
        """Prepne stav stlmenia zvuku"""
        self.muted = not self.muted
        update_setting('audio.muted', self.muted)
        if self.sound:
            self.sound.volume = 0 if self.muted else self.volume
```

## Služba Notifikácií (`notification_service.py`)

Systém obsahuje službu pre odosielanie notifikácií cez rôzne kanály:

```python
class NotificationService:
    """Služba pre odosielanie notifikácií na rôzne kanály"""
    
    def __init__(self):
        """Inicializácia služby notifikácií"""
        self.settings = get_setting('notifications', {})
        self.enabled = self.settings.get('enabled', True)
        
    def send_notification(self, title, message, importance='normal'):
        """Odosiela notifikáciu cez všetky nakonfigurované kanály"""
        if not self.enabled:
            return False
            
        success = False
        
        # Kontrola úrovne dôležitosti a filtrovanie notifikácií
        min_importance = self.settings.get('min_importance', 'normal')
        if not self._should_send(importance, min_importance):
            return False
            
        # Odoslanie e-mailových notifikácií
        if self.settings.get('email', {}).get('enabled', False):
            email_success = self._send_email_notification(title, message)
            success = success or email_success
            
        # Odoslanie SMS notifikácií
        if self.settings.get('sms', {}).get('enabled', False):
            sms_success = self._send_sms_notification(title, message)
            success = success or sms_success
            
        # Odoslanie push notifikácií
        if self.settings.get('push', {}).get('enabled', False):
            push_success = self._send_push_notification(title, message)
            success = success or push_success
            
        return success
        
    def _send_email_notification(self, title, message):
        """Odosiela e-mailovú notifikáciu"""
        # Implementácia odosielania e-mailu...
        
    def _send_sms_notification(self, title, message):
        """Odosiela SMS notifikáciu"""
        # Implementácia odosielania SMS...
        
    def _send_push_notification(self, title, message):
        """Odosiela push notifikáciu na mobilné zariadenia"""
        # Implementácia odosielania push notifikácie...
        
    def _should_send(self, importance, min_importance):
        """Rozhodne, či by sa mala odoslať notifikácia na základe dôležitosti"""
        importance_levels = {
            'low': 0,
            'normal': 1,
            'high': 2,
            'critical': 3
        }
        
        current_level = importance_levels.get(importance, 1)
        min_level = importance_levels.get(min_importance, 1)
        
        return current_level >= min_level
```

## Záver

Tento bezpečnostný systém poskytuje flexibilnú, rozšíriteľnú platformu pre domáce monitorovanie s viacerými senzormi a kamerami. Distribuovaná architektúra umožňuje umiestniť senzory po celom objekte pri zachovaní centralizovaného monitorovania a riadenia.

Systém bol navrhnutý s dôrazom na:
- **Modularitu**: Jasne definované komponenty s jednotlivými zodpovednosťami
- **Rozšíriteľnosť**: Architektúra umožňujúca pridanie nových funkčností a integrácie
- **Bezpečnosť**: Implementácia autentifikácie a zabezpečenia údajov
- **Používateľskú skúsenosť**: Intuitívne používateľské rozhranie s responzívnym dizajnom
- **Spoľahlivosť**: Robustné spracovanie chýb a mechanizmy obnovy

Kód demonštruje niekoľko dôležitých princípov návrhu softvéru:
- Oddelenie zodpovedností s jasnými zodpovednosťami komponentov
- Architektúra riadená udalosťami pre responzívne používateľské rozhranie a integráciu hardvéru
- Súbežnosť založená na vláknách pre sieťové operácie
- Komponentový návrh používateľského rozhrania s opätovne použiteľnými prvkami
- Perzistentná konfigurácia s predvolenými hodnotami a validáciou
- Mechanizmy spracovávania chýb a obnovy pre robustnosť

S týmito prvkami systém poskytuje komplexné a flexibilné riešenie pre domácu bezpečnosť s možnosťami ďalšieho vývoja a customizácie.
