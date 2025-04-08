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

### Podrobná Analýza Kódu

#### Hlavná Aplikácia (`app.py`)

Trieda `MainApp` slúži ako vstupný bod aplikácie a kontrolér:

```python
class MainApp(App):
    def build(self):
        # Načítanie nastavení aplikácie
        settings = load_settings()
        
        # Spustenie sieťových poslucháčov
        self.discovery_listener = DiscoveryListener()
        self.udp_listener = UDPListener()
        self.tcp_listener = TCPListener()
        
        # Inicializácia správcu obrazoviek so všetkými obrazovkami
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(AlertsScreen(name='alerts'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        
        return sm
```

Kľúčové aspekty:
- Aplikácia nasleduje dizajn frameworku Kivy s `ScreenManager` pre navigáciu
- Rozsiahlo sa používa vláknenie pre sieťovú komunikáciu (všetci poslucháči bežia v samostatných vláknach)
- Zdroje sú správne spravované s inicializáciou v `build()` a čistením v `on_stop()`
- Prechody medzi obrazovkami riadia tok aplikácie

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

## Body Rozšírenia

Systém je navrhnutý na rozšíriteľnosť:

1. **Dodatočné Senzory**: SEND komponent môže byť rozšírený o nové typy senzorov
2. **Vylepšená Autentifikácia**: Prihlasovacie systém by mohol byť rozšírený o viacfaktorovú autentifikáciu
3. **Cloudová Integrácia**: Systém by mohol byť rozšírený o zálohovanie udalostí do cloudového úložiska
4. **Mobilná Aplikácia**: Sprievodná mobilná aplikácia by mohla byť vyvinutá s použitím rovnakých protokolov

## Záver

Tento bezpečnostný systém poskytuje flexibilnú, rozšíriteľnú platformu pre domáce monitorovanie s viacerými senzormi a kamerami. Distribuovaná architektúra umožňuje umiestniť senzory po celom objekte pri zachovaní centralizovaného monitorovania a riadenia.

Kód demonštruje niekoľko dôležitých princípov návrhu softvéru:
- Oddelenie zodpovedností s jasnými zodpovednosťami komponentov
- Architektúra riadená udalosťami pre responzívne používateľské rozhranie a integráciu hardvéru
- Súbežnosť založená na vláknach pre sieťové operácie
- Komponentový návrh používateľského rozhrania s opätovne použiteľnými prvkami
- Perzistentná konfigurácia s predvolenými hodnotami a validáciou
- Mechanizmy spracovávania chýb a obnovy pre robustnosť
