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
| Web (HTTP) | 8090 | Webové rozhranie pre vzdialený prístup z prehliadača |

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

### Štruktúra REC Komponentu

REC komponent má nasledujúcu štruktúru súborov:

```
REC/
├── __init__.py
├── alerts_screen.py        # Obrazovka správy upozornení
├── app.py                  # Hlavná Kivy aplikácia
├── base_screen.py          # Základná trieda obrazovky
├── dashboard_screen.py     # Obrazovka monitorovania zariadení
├── listeners.py            # Sieťoví poslucháči
├── login_screen.py         # Obrazovka PIN autentifikácie
├── main_screen.py          # Hlavná navigačná obrazovka
├── main.py                 # Vstupný bod aplikácie
├── network.py              # Sieťové nástroje
├── notification_service.py # Služba upozornení
├── settings_manager.py     # Správa nastavení
├── settings_screen.py      # Obrazovka nastavení
├── theme_helper.py         # Témy používateľského rozhrania
├── web_app.py              # Webové rozhranie
├── assets/                 # Multimediálne súbory
│   ├── alarm.wav           # Zvuk alarmu
│   └── security_logo.png   # Logo aplikácie
├── config/                 # Konfiguračné súbory
│   ├── alerts_log.py       # Správa upozornení
│   ├── alerts.log          # História upozornení
│   ├── settings.json       # Nastavenia vo formáte JSON
│   └── settings.py         # Nástroje nastavení
└── web/                    # Súbory webového rozhrania
    ├── static/             # Statické súbory (CSS, JavaScript)
    └── templates/          # HTML šablóny
        ├── alerts.html     # Stránka upozornení
        ├── base.html       # Základná šablóna
        ├── dashboard.html  # Prístrojová doska
        ├── images.html     # Prehliadač obrázkov
        ├── login.html      # Prihlasovacia stránka
        ├── sensors.html    # Správa senzorov
        └── settings.html   # Stránka nastavení
```

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

#### Obrazovka upozornení (`alerts_screen.py`)

Systém upozornení umožňuje prezeranie, správu a interakciu s bezpečnostnými upozorneniami:

```python
class AlertsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(AlertsScreen, self).__init__(**kwargs)
        
        # Nastavenie titulku a tlačidla späť
        self.set_title("Systémové upozornenia")
        self.add_back_button('main')
        
        # Zoznam upozornení s možnosťou prezerania obrázkov a označenia ako prečítané
        # ...
        
    def refresh_alerts(self, *args):
        """Načítanie a zobrazenie upozornení zo systému"""
        # Načítanie upozornení z databázy
        alerts = get_alerts()
        
        # Zobrazenie upozornení v UI
        # ...
        
    def show_images_popup(self, image_paths, alert):
        """Zobrazenie obrázkov v popup okne"""
        # Zobrazenie zachytených obrázkov pre konkrétne upozornenie
        # ...
        
    def mark_alert_read(self, instance):
        """Označí upozornenie ako prečítané"""
        # Aktualizácia stavu upozornenia
        # ...
```

Trieda `GracePeriodAlert` poskytuje intervenovať pri spustení alarmu:

```python
class GracePeriodAlert(Popup):
    """Vyskakovacie upozornenie zobrazujúce odpočet ochrannej doby pred spustením plného alarmu"""
    
    def __init__(self, alert_data, grace_seconds=30, **kwargs):
        # Inicializácia popup okna s časovačom
        # ...
        
    def on_number_press(self, instance):
        """Spracovanie stlačenia číselného tlačidla"""
        # Zadanie PIN kódu pre deaktiváciu alarmu
        # ...
    
    def on_enter(self, instance):
        """Overenie PIN kódu a vypnutie systému, ak je správny"""
        # Validácia PIN kódu a deaktivácia systému
        # ...
```

#### Prístrojová doska (`dashboard_screen.py`)

Prístrojová doska poskytuje prehľad stavu všetkých senzorov v reálnom čase:

```python
class DashboardScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(DashboardScreen, self).__init__(**kwargs)
        
        # Nastavenie titulku a tlačidla späť
        self.set_title("Prehľad senzorov")
        self.add_back_button('main')
        
        # Vytvorenie oblasti obsahu
        content_area = self.create_content_area()
        
        # Vytvorenie kariet zariadení
        self.device_container = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.device_container.bind(minimum_height=self.device_container.setter('height'))
        
        # Pridanie posúvateľného zobrazenia pre zariadenia
        scroll_view = ScrollView(size_hint_y=0.9)
        scroll_view.add_widget(self.device_container)
        content_area.add_widget(scroll_view)
        
        # Spodný panel s aktualizáciou a stavom systému
        # ...
        
    def refresh_devices(self, *args):
        """Aktualizácia zobrazovania zariadení a ich stavov"""
        # Obnovenie stavu zariadení z nastavení
        devices = self.get_devices_from_settings()
        
        # Aktualizácia alebo vytvorenie kariet zariadení
        # ...
        
    def toggle_system_state(self, instance):
        """Prepnutie stavu systému medzi aktívnym a neaktívnym"""
        # Aktivácia/deaktivácia bezpečnostného systému
        # ...
```

#### Prihlasovacia obrazovka (`login_screen.py`)

Prihlasovacia obrazovka implementuje bezpečnú autentifikáciu pomocou PIN kódu:

```python
class LoginScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        
        # Nastavenie titulku
        self.set_title("Prihlásenie do bezpečnostného systému")
        
        # Vytvorenie oblasti obsahu
        content_area = self.create_content_area()
        
        # Vstupné pole pre PIN
        self.pin_input = ""
        self.pin_display = TextInput(
            multiline=False,
            readonly=True,
            halign="center",
            font_size=24,
            password=True,
            size_hint_y=0.1
        )
        content_area.add_widget(self.pin_display)
        
        # Klávesnica
        keypad_layout = GridLayout(cols=3, spacing=[10, 10], size_hint_y=0.5)
        
        # Vytvorenie tlačidiel s číslami
        for i in range(1, 10):  # Vytvorí tlačidlá 1 až 9
            btn = Button(text=str(i), font_size=24)
            btn.bind(on_release=self.on_button_press)
            keypad_layout.add_widget(btn)
            
        # Pridanie tlačidiel vymazať, 0 a potvrdiť
        # ...
        
    def on_enter_pressed(self, instance):
        """Spracuje stlačenie tlačidla Potvrdiť"""
        if validate_pin(self.pin_input):
            print("DEBUG: PIN úspešne overený, prístup povolený")
            self.status_label.text = "Prístup povolený"
            self.manager.current = 'main'
        else:
            print(f"DEBUG: Zadaný neplatný PIN: {self.pin_input}")
            self.status_label.text = "Neplatný PIN, skúste znova"
            self.pin_input = ""
            self.pin_display.text = ""
```

#### Notifikačná služba (`notification_service.py`)

Notifikačná služba spravuje upozornenia, alarmy a ochranné doby:

```python
class NotificationService:
    """Služba pre správu upozornení, zvukových alarmov a ochrannú dobu"""
    
    def __init__(self):
        """Inicializácia služby notifikácií"""
        from config.settings import get_setting
        
        # Načítanie nastavení
        self.sound_manager = SoundManager()
        self.settings = get_setting('notifications', {})
        self.enabled = self.settings.get('enabled', True)
        self.grace_period = get_setting('system.grace_period', 30)  # Sekúnd
        
        # Inicializácia stavu
        self.active_grace_timer = None
        self.alarm_active = False
        
    def start_grace_period(self, alert_data):
        """Spustenie ochrannej doby pred aktiváciou alarmu"""
        # Zobrazenie odpočtu a možnosti deaktivácie
        # ...
        
    def cancel_grace_period(self):
        """Zrušenie aktívnej ochrannej doby"""
        # Zrušenie časovača a vyčistenie stavu
        # ...
        
    def trigger_alarm(self, alert_data=None):
        """Spustenie alarmu po uplynutí ochrannej doby"""
        # Zvukový alarm a zaznamenanie upozornenia
        # ...
        
    def stop_alarm(self):
        """Zastavenie aktívneho alarmu"""
        # Zastavenie zvukov a aktualizácia stavu
        # ...
```

#### Webové rozhranie (`web_app.py`)

Webové rozhranie poskytuje vzdialený prístup k monitarovacím a konfiguračným funkciám:

```python
class WebAppThread(threading.Thread):
    """Vlákno pre spustenie webovej aplikácie"""
    
    def __init__(self, host='0.0.0.0', port=8090):
        threading.Thread.__init__(self, daemon=True)
        self.host = host
        self.port = port
        self.app = Flask(__name__,
                         static_folder='web/static',
                         template_folder='web/templates')
        self.setup_routes()
        
    def setup_routes(self):
        """Nastavenie trás pre webovú aplikáciu"""
        
        @self.app.route('/')
        def index():
            """Hlavná stránka - presmerovanie na prihlásenie alebo prístrojovú dosku"""
            # ...
            
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Prihlasovacia stránka"""
            # ...
            
        @self.app.route('/dashboard')
        @login_required
        def dashboard():
            """Prístrojová doska so stavom zariadení"""
            # ...
            
        @self.app.route('/alerts')
        @login_required
        def alerts():
            """Zobrazenie histórie upozornení"""
            # ...
            
        @self.app.route('/settings', methods=['GET', 'POST'])
        @login_required
        def settings():
            """Konfigurácia systému"""
            # ...
            
        @self.app.route('/toggle_system', methods=['POST'])
        @login_required
        def toggle_system():
            """Aktivácia/deaktivácia systému"""
            # ...
            
        @self.app.route('/cancel_alarm', methods=['POST'])
        @login_required
        def cancel_alarm():
            """Zrušenie aktívneho alarmu"""
            # ...
    
    def run(self):
        """Spustenie webovej aplikácie"""
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
```

### Služba zvukových upozornení

V rámci notifikačnej služby je implementovaná podpora pre zvukové upozornenia:

```python
class SoundManager:
    """Trieda pre správu zvukových efektov v systéme"""
    
    def __init__(self):
        """Inicializácia správcu zvuku"""
        from kivy.core.audio import SoundLoader
        
        self.sound = None
        self.volume = 1.0
        self.muted = False
        
        # Načítanie zvukového súboru
        try:
            sound_file = os.path.join(os.path.dirname(__file__), 'assets/alarm.wav')
            self.sound = SoundLoader.load(sound_file)
            if self.sound:
                self.sound.volume = self.volume
                print(f"DEBUG: Zvuk alarmu úspešne načítaný z {sound_file}")
        except Exception as e:
            print(f"CHYBA: Nemožno načítať zvuk alarmu: {e}")
            
    def play_alarm(self):
        """Prehrá zvuk alarmu"""
        if self.sound and not self.muted:
            self.sound.loop = True  # Nastavenie opakovania zvuku
            self.sound.play()
            
    def stop_alarm(self):
        """Zastaví prehrávanie alarmu"""
        if self.sound and self.sound.state == 'play':
            self.sound.stop()
```

### Jazyková lokalizácia

Celý systém je lokalizovaný v slovenčine, od komentárov v kóde až po používateľské rozhranie:

1. **Systémové správy**: Všetky textové reťazce, upozornenia a informačné správy sú v slovenčine
2. **UI elementy**: Všetky tlačidlá, popisky, nadpisy a menu sú v slovenčine
3. **Komentáre v kóde**: Dokumentácia funkcií a tried v kóde používa slovenčinu
4. **Webové rozhranie**: HTML šablóny používajú slovenčinu pre konzistentný používateľský zážitok
5. **Chybové hlásenia**: Všetky chybové hlásenia a diagnostické správy sú v slovenčine

## Tok Dát

### Spracovanie Udalostí Senzorov

Keď sa aktivuje senzor, nastane nasledujúci tok:

1. **Hardvérový Spúšťač**: Fyzický senzor zmení stav (napr. detekcia pohybu)
2. **GPIO Udalosť**: Prerušenie GPIO na Raspberry Pi spúšťa callback v SEND komponente
3. **Spracovateľ Udalostí**: Callback spracuje udalosť senzora
4. **Sieťový Prenos**: Aktualizácia stavu sa odosiela cez UDP do REC komponentu
5. **REC Príjem**: UDP poslucháč prijme aktualizáciu stavu
6. **Aktualizácia Databázy**: Stav uložený v nastaveniach a databáze
7. **Aktualizácia UI**: Prístrojová doska a upozornenia aktualizované na zobrazenie nového stavu
8. **Generovanie Upozornení**: Ak je systém aktivovaný, vytvorí sa upozornenie
9. **Zvukové Upozornenia**: Prehratie zvuku alarmu pre kritické upozornenia
10. **E-mailové Notifikácie**: Odoslanie upozornení prostredníctvom e-mailu (ak je nakonfigurované)

### Tok Zachytávania Obrázkov

Pri bezpečnostných udalostiach systém zachytáva a spracúva obrázkové dôkazy:

1. **Spúšťacia Udalosť**: Udalosť senzora spúšťa zachytávanie obrázka z kamery
2. **TCP Prenos**: Obrázok odoslaný cez TCP pre spoľahlivosť do REC komponentu
3. **REC Príjem**: TCP poslucháč prijme a spracuje obrázok
4. **Ukladanie Obrázkov**: Obrázok uložený v lokálnom úložisku REC komponentu
5. **Aktualizácia Upozornení**: Príslušné upozornenia prepojené s uloženými obrázkami
6. **Webové Rozhranie**: Obrázok dostupný prostredníctvom webového rozhrania v galérii obrázkov

## Body Rozšírenia

Systém je navrhnutý s ohľadom na budúce rozšírenia:

1. **Dodatočné Senzory**: Podpora pre nové typy senzorov a detektorov
2. **Vylepšená Autentifikácia**: Rozšírenie o viacfaktorovú autentifikáciu
3. **Cloudová Integrácia**: Zálohovanie udalostí a obrázkov do cloudového úložiska
4. **Mobilná Aplikácia**: Vývoj natívnej mobilnej aplikácie pre Android a iOS
5. **Integrácie s Tretími Stranami**: Podpora pre HomeKit, Google Home alebo Alexa
6. **Analytika a Štatistiky**: Pokročilé nástroje pre analýzu bezpečnostných udalostí
7. **Rozpoznávanie Objektov**: Implementácia strojového učenia pre rozpoznávanie objektov na zachytených obrázkoch

## Záver

Tento bezpečnostný systém poskytuje komplexné riešenie pre monitorovanie domácnosti a detekciu neoprávneného vniknutia. Vďaka kompletnej lokalizácii v slovenčine je systém priateľský a intuitívny pre slovensky hovoriacich používateľov. Modulárna architektúra umožňuje flexibilnú konfiguráciu aj rozšíriteľnosť pre budúce vylepšenia.

Hlavné silné stránky systému:
- **Flexibilná inštalácia**: Podpora mnohých typov senzorov a rôznych usporiadaní
- **Jednoduché používanie**: Intuitívne používateľské rozhranie v slovenčine
- **Viacero rozhraní**: Desktopové a webové rozhranie pre rôzne spôsoby prístupu
- **Spoľahlivosť**: Robustné spracovanie chýb a zotavenie z výnimiek
- **Bezpečnosť**: Viacúrovňová autentifikácia a ochrana údajov

Systém bol navrhnutý s dôrazom na použiteľnosť, spoľahlivosť a rozšíriteľnosť, a poskytuje solídny základ pre domáci bezpečnostný monitoring s možnosťami ďalšieho vývoja a prispôsobenia.
