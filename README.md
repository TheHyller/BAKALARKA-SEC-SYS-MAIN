# BAKALARKA-SEC-SYS-MAIN
 School thesis work for security system

A comprehensive home security solution with real-time monitoring, custom alert management, and flexible configuration options.

## 🔐 Overview

This project is a comprehensive home security system with two main components: a sender (for Raspberry Pi) that detects motion and captures images, and a receiver that provides monitoring and alerts through a user interface.

## ✨ Features

This project provides a complete home security system with two main components:

### Sender Component (SEND)
- Motion detection using Raspberry Pi GPIO sensors
- Image capture with PiCamera on security events
- Door and window sensor integration
- Network discovery for easy setup
- Real-time alerts and status updates

### Receiver Component (REC)
- Secure PIN-based authentication system
- Real-time sensor status dashboard
- Alert history and management
- Customizable system settings
- TCP/UDP network communication
- Auto-discovery of sender devices

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Raspberry Pi (for the sender component)
- Camera module (for the sender component)
- Motion, door, and window sensors (optional)

### Step 1: Clone the repository
```bash
git clone https://github.com/yourusername/home-security-system.git
cd home-security-system
```

### Step 2: Install dependencies
For the receiver component:
```bash
cd REC
pip install -r requirements.txt
```

For the sender component:
```bash
cd SEND
pip install -r requirements.txt
```

## ⚙️ Configuration
The system uses JSON configuration files located in the `REC/config` directory. You can modify these settings:

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

Key configuration options:
- PIN code for system access
- Network ports
- System state (active/inactive)
- Sensor settings

## 📱 Usage

### Running the Sender (on Raspberry Pi)
```bash
cd SEND
python SEND.py
```

### Running the Receiver (on monitoring device)
```bash
cd REC
python main.py
```

### Basic Operation
1. Log in using the PIN code (default: 1234)
2. Use the main screen to monitor sensor status
3. Activate/deactivate the system using the toggle button
4. Configure settings as needed

## 🏗️ Architecture

The system architecture consists of:

- **REC module**: GUI interface built with Kivy/KivyMD
  - Login authentication
  - Sensor status display
  - Settings management
  - Alerts history

- **SEND module**: Sensor interface for Raspberry Pi
  - Motion detection
  - Image capture
  - Network communication
  - Status broadcasting

## 👨‍💻 Development

### Project Structure
```
.
├── LICENSE.txt              # MIT License
├── README.md                # Project documentation
├── requirements.txt         # Common dependencies
├── REC/                     # Receiver component
│   ├── main.py              # Entry point
│   ├── app.py               # Main Kivy application
│   ├── login_screen.py      # PIN authentication
│   ├── main_screen.py       # Dashboard view
│   ├── alerts_screen.py     # Alerts history
│   ├── settings_screen.py   # Configuration interface
│   ├── listeners.py         # Network listeners
│   └── config/              # Configuration files
└── SEND/                    # Sender component
    ├── SEND.py              # Raspberry Pi script
    └── requirements.txt     # Sender-specific dependencies
```

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License
This project is licensed under the MIT License - see the LICENSE.txt file for details.
