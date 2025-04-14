# BAKALARKA-SEC-SYS-MAIN
Domáci bezpečnostný systém - Bakalárska práca

Komplexné bezpečnostné riešenie s monitorovaním v reálnom čase, podporou viacerých zariadení, webovým rozhraním, správou upozornení a flexibilnými možnosťami konfigurácie.

## 🔐 Prehľad

Tento projekt je kompletný domáci bezpečnostný systém s dvoma hlavnými komponentmi:
1. **Odosielateľ (SEND)**: Beží na Raspberry Pi na detekciu pohybu, zachytávanie obrázkov a odosielanie upozornení
2. **Prijímač (REC)**: Poskytuje monitorovanie prostredníctvom desktopového grafického rozhrania aj webového rozhrania s upozorneniami v reálnom čase a správou nastavení

## ✨ Funkcie

### Komponent odosielateľa (SEND)
- Detekcia pohybu pomocou GPIO senzorov Raspberry Pi
- Zachytávanie obrázkov pomocou PiCamera pri bezpečnostných udalostiach
- Integrácia senzorov dverí a okien
- Sieťové vyhľadávanie pre jednoduché nastavenie
- Upozornenia a aktualizácie stavu v reálnom čase
- Jedinečná identifikácia zariadenia pre systémy s viacerými zariadeniami
- Trvalé protokolovanie so súborom security_sender.log

### Komponent prijímača (REC)
- Zabezpečený autentifikačný systém založený na PIN kóde
- Dashboard stavu senzorov v reálnom čase
- Podpora viacerých platforiem:
  - Desktopové grafické rozhranie pomocou Kivy/KivyMD
  - Webové rozhranie s responzívnym dizajnom
- Podpora viacerých senzorových zariadení s jedinečnými ID
- História a správa upozornení
- Prehliadanie zachytených obrázkov
- Notifikačná služba so zvukovými upozorneniami
- Prispôsobiteľné systémové nastavenia
- TCP/UDP sieťová komunikácia
- Automatické vyhľadávanie odosielacích zariadení
- Kompletné slovenské používateľské rozhranie

## 🚀 Inštalácia

### Požiadavky
- Python 3.8 alebo vyšší
- Raspberry Pi (pre komponent odosielateľa)
- Kamerový modul (pre komponent odosielateľa)
- Pohybové senzory, senzory dverí a senzory okien (voliteľné)

### Krok 1: Klonovanie repozitára
```bash
git clone https://github.com/yourusername/BAKALARKA-SEC-SYS-MAIN.git
cd BAKALARKA-SEC-SYS-MAIN
```

### Krok 2: Inštalácia závislostí
```bash
pip install -r requirements.txt
```

## ⚙️ Konfigurácia

### Konfigurácia prijímača
Systém používa konfiguračné súbory JSON umiestnené v adresári `REC/config`:

```json
{
    "pin_code": "0000",
    "system_active": false,
    "network": {
        "tcp_port": 8080,
        "udp_port": 8081,
        "discovery_port": 8082
    },
    "sensors": []
}
```

### Konfigurácia odosielateľa
Odosielateľ používa súbor `sender_config.json` v koreňovom adresári:

```json
{
    "device_id": "rpi_sensor_1",
    "server_ip": "auto", 
    "tcp_port": 8080,
    "udp_port": 8081,
    "discovery_port": 8082,
    "gpio_pins": {
        "motion_sensor": 17,
        "door_sensor": 18,
        "window_sensor": 27
    },
    "camera": {
        "enabled": true,
        "resolution": [1280, 720],
        "framerate": 30,
        "rotation": 0
    }
}
```

## 📱 Použitie

### Spustenie odosielateľa (na Raspberry Pi)
```bash
python -m SEND.SEND
```

### Spustenie prijímača (desktopové rozhranie)
```bash
python -m REC.main
```

### Prístup k webovému rozhraniu
Po spustení prijímača pristupujte k webovému rozhraniu na:
```
http://localhost:8090
```
alebo nahraďte localhost IP adresou systému, na ktorom beží prijímač.

### Základné operácie
1. Prihláste sa pomocou PIN kódu (predvolený: 0000)
2. Použite dashboard na monitorovanie stavu senzorov
3. Aktivujte/deaktivujte systém pomocou prepínacieho tlačidla
4. Prezerajte upozornenia a zachytené obrázky
5. Podľa potreby nakonfigurujte nastavenia

## 🏗️ Architektúra

Architektúra systému pozostáva z:

- **Modul REC**: 
  - Desktopové grafické rozhranie postavené na Kivy/KivyMD
  - Webové rozhranie s Flaskom
  - Prihlasovacia autentifikácia
  - Obrazovka dashboardu na monitorovanie senzorov
  - História a správa upozornení
  - Správa nastavení
  - Notifikačná služba so zvukovými upozorneniami
  - Sieťoví poslucháči pre údaje zo senzorov

- **Modul SEND**: 
  - Rozhranie senzorov pre Raspberry Pi
  - Integrácia senzorov pohybu, dverí a okien
  - Ovládanie kamery na zachytávanie obrázkov
  - Sieťová komunikácia s prijímačom
  - Vysielanie stavu a objavovanie servera

## 👨‍💻 Vývoj

### Štruktúra projektu
```
├── LICENSE                   # Licenčný súbor
├── README.md                 # Dokumentácia projektu
├── requirements.txt          # Spoločné závislosti
├── security_sender.log       # Protokolový súbor odosielateľa
├── sender_config.json        # Konfigurácia odosielateľa
├── technical_documentation_sk.md # Technická dokumentácia (slovenčina)
├── captures/                 # Adresár pre zachytené obrázky
├── REC/                      # Komponent prijímača
│   ├── __init__.py
│   ├── alerts_screen.py      # UI správy upozornení
│   ├── app.py                # Hlavná Kivy aplikácia
│   ├── base_screen.py        # Základná trieda obrazovky
│   ├── dashboard_screen.py   # UI monitorovania senzorov
│   ├── listeners.py          # Sieťoví poslucháči
│   ├── login_screen.py       # UI autentifikácie PIN
│   ├── main_screen.py        # Hlavný UI kontajner
│   ├── main.py               # Vstupný bod
│   ├── network.py            # Sieťové nástroje
│   ├── notification_service.py # Notifikačné a zvukové služby
│   ├── settings_manager.py   # Správa nastavení
│   ├── settings_screen.py    # UI konfigurácie
│   ├── theme_helper.py       # Nástroje pre tému UI
│   ├── web_app.py            # Webové rozhranie
│   ├── assets/               # UI aktíva
│   │   ├── alarm.wav         # Zvuk alarmu
│   │   └── security_logo.png # Logo aplikácie
│   ├── config/               # Konfiguračné súbory
│   │   ├── alerts_log.py     # Manažér upozornení
│   │   ├── alerts.log        # Log upozornení
│   │   ├── settings.json     # Hlavné nastavenia
│   │   └── settings.py       # Nástroje nastavení
│   └── web/                  # Súbory webového rozhrania
│       ├── static/           # Statické webové aktíva
│       │   └── css/          # CSS štýly
│       └── templates/        # HTML šablóny
│           ├── alerts.html   # Stránka upozornení
│           ├── base.html     # Základná šablóna
│           ├── dashboard.html # Stránka dashboardu
│           ├── images.html   # Galéria obrázkov
│           ├── login.html    # Prihlasovacia stránka
│           ├── sensors.html  # Stav senzorov
│           └── settings.html # Stránka nastavení
└── SEND/                     # Komponent odosielateľa
    ├── __init__.py
    └── SEND.py               # Skript pre Raspberry Pi
```

## 📋 Technická dokumentácia

Podrobná technická dokumentácia je k dispozícii v [technical_documentation_sk.md](technical_documentation_sk.md) (v slovenčine).

## 🌍 Jazykové rozhranie

Celé používateľské rozhranie systému je lokalizované v slovenčine, vrátane:
- Všetkých obrazoviek a tlačidiel
- Chybových hlásení a upozornení
- Webového rozhrania
- Notifikácií a systémových správ

Používateľské rozhranie je navrhnuté tak, aby bolo intuitívne a zrozumiteľné pre slovensky hovoriacich používateľov.

## 🤝 Prispievanie

Príspevky sú vítané! Neváhajte predložiť pull request alebo otvoriť problém pre akékoľvek návrhy alebo vylepšenia.

1. Forkni repozitár
2. Vytvor svoju vlastností (`git checkout -b feature/amazing-feature`)
3. Commitni svoje zmeny (`git commit -m 'Add some amazing feature'`)
4. Pushni do vetvičky (`git push origin feature/amazing-feature`)
5. Otvor Pull Request

## 📄 Licencia

Tento projekt je licencovaný pod licenciou MIT - podrobnosti nájdete v súbore LICENSE.

## 📅 Posledná aktualizácia

14. apríl 2025
