# BAKALARKA-SEC-SYS-MAIN
Home Security System - Bachelor Thesis Project

A comprehensive security solution with real-time monitoring, multi-device support, web interface, alert management, and flexible configuration options.

## 🔐 Overview

This project is a complete home security system with two main components:
1. **Sender (SEND)**: Runs on Raspberry Pi to detect motion, capture images, and send alerts
2. **Receiver (REC)**: Provides monitoring through both desktop GUI and web interfaces with real-time alerts and configuration management

## ✨ Features

### Sender Component (SEND)
- Motion detection using Raspberry Pi GPIO sensors
- Image capture with PiCamera on security events
- Door and window sensor integration
- Network discovery for easy setup
- Real-time alerts and status updates
- Unique device identification for multi-device systems
- Persistent logging with security_sender.log

### Receiver Component (REC)
- Secure PIN-based authentication system
- Real-time sensor status dashboard
- Multi-platform support:
  - Desktop GUI with Kivy/KivyMD
  - Web interface with responsive design
- Support for multiple sensor devices with unique IDs
- Alert history and management
- Image capture review
- Notification service with audio alerts
- Customizable system settings
- TCP/UDP network communication
- Auto-discovery of sender devices

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Raspberry Pi (for the sender component)
- Camera module (for the sender component)
- Motion sensors, door sensors, and window sensors (optional)

### Step 1: Clone the repository
```bash
git clone https://github.com/yourusername/BAKALARKA-SEC-SYS-MAIN.git
cd BAKALARKA-SEC-SYS-MAIN
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### Receiver Configuration
The system uses JSON configuration files located in the `REC/config` directory:

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

### Sender Configuration
The sender uses a `sender_config.json` file in the root directory:

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

## 📱 Usage

### Running the Sender (on Raspberry Pi)
```bash
python -m SEND.SEND
```

### Running the Receiver (desktop interface)
```bash
python -m REC.main
```

### Accessing the Web Interface
Once the receiver is running, access the web interface at:
```
http://localhost:8080
```
or replace localhost with the IP address of the system running the receiver.

### Basic Operation
1. Log in using the PIN code (default: 0000)
2. Use the dashboard to monitor sensor status
3. Activate/deactivate the system using the toggle button
4. View alerts and captured images
5. Configure settings as needed

## 🏗️ Architecture

The system architecture consists of:

- **REC module**: 
  - Desktop GUI built with Kivy/KivyMD
  - Web interface with Flask
  - Login authentication
  - Dashboard screen for sensor monitoring
  - Alert history and management
  - Settings management
  - Notification service with audio alerts
  - Network listeners for sensor data

- **SEND module**: 
  - Sensor interface for Raspberry Pi
  - Motion, door, and window sensor integration
  - Camera control for image capture
  - Network communication with the receiver
  - Status broadcasting and server discovery

## 👨‍💻 Development

### Project Structure
```
├── LICENSE                   # License file
├── README.md                 # Project documentation
├── requirements.txt          # Common dependencies
├── security_sender.log       # Sender log file
├── sender_config.json        # Sender configuration
├── technical_documentation_sk.md # Technical documentation (Slovak)
├── captures/                 # Directory for captured images
├── REC/                      # Receiver component
│   ├── __init__.py
│   ├── alerts_screen.py      # Alerts management UI
│   ├── app.py                # Main Kivy application
│   ├── base_screen.py        # Base screen class
│   ├── dashboard_screen.py   # Sensor monitoring UI
│   ├── listeners.py          # Network listeners
│   ├── login_screen.py       # PIN authentication UI
│   ├── main_screen.py        # Main UI container
│   ├── main.py               # Entry point
│   ├── network.py            # Network utilities
│   ├── notification_service.py # Notification and sound services
│   ├── settings_manager.py   # Settings management
│   ├── settings_screen.py    # Configuration UI
│   ├── theme_helper.py       # UI theme utilities
│   ├── web_app.py            # Web interface
│   ├── assets/               # UI assets
│   │   ├── alarm.wav         # Alarm sound
│   │   └── security_logo.png # Application logo
│   ├── config/               # Configuration files
│   │   ├── settings.json     # Main settings
│   │   └── settings.py       # Settings utilities
│   └── web/                  # Web interface files
│       ├── static/           # Static web assets
│       │   └── css/          # CSS stylesheets
│       └── templates/        # HTML templates
│           ├── alerts.html   # Alerts page
│           ├── base.html     # Base template
│           ├── dashboard.html # Dashboard page
│           ├── images.html   # Image gallery
│           ├── login.html    # Login page
│           ├── sensors.html  # Sensors status
│           └── settings.html # Settings page
└── SEND/                     # Sender component
    ├── __init__.py
    └── SEND.py               # Raspberry Pi script
```

## 📋 Technical Documentation

Detailed technical documentation is available in [technical_documentation_sk.md](technical_documentation_sk.md) (in Slovak).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📅 Last Updated

April 13, 2025
