/**
 * ESP Security Sensor (ESP_SEND)
 * Compatible with BAKALARKA-SEC-SYS-MAIN security system
 * 
 * For ESP8266 and ESP32 devices
 */

#include <ESP8266WiFi.h>        // For ESP8266 - Comment out if using ESP32
// #include <WiFi.h>            // For ESP32 - Uncomment if using ESP32
#include <ESP8266HTTPClient.h>  // For ESP8266 - Comment out if using ESP32
// #include <HTTPClient.h>      // For ESP32 - Uncomment if using ESP32
#include <WiFiUdp.h>
#include <ArduinoJson.h>
#include <EEPROM.h>

// WiFi credentials - Change these to match your network
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// Device configuration
struct Config {
  char device_id[37];       // UUID string (36 chars + null terminator)
  char device_name[32];     // Human-readable device name
  char receiver_ip[16];     // IP address string (max 15 chars + null terminator)
  uint16_t tcp_port;        // Port for sending images
  uint16_t udp_port;        // Port for sensor updates
  uint16_t discovery_port;  // Port for discovery service
  uint8_t motion_pin;       // GPIO pin for motion sensor
  uint8_t door_pin;         // GPIO pin for door sensor
  uint8_t window_pin;       // GPIO pin for window sensor
  uint8_t led_pin;          // GPIO pin for status LED
  int capture_interval;     // Min seconds between sensor triggers
};

// Default configuration
Config CONFIG = {
  "",                       // device_id - will be generated
  "ESP-Security-Sensor",    // device_name
  "127.0.0.1",              // receiver_ip - will be updated via discovery
  8080,                     // tcp_port
  8081,                     // udp_port
  8082,                     // discovery_port
  5,                        // motion_pin (D1 on ESP8266)
  4,                        // door_pin (D2 on ESP8266)
  0,                        // window_pin (D3 on ESP8266)
  2,                        // led_pin (D4 on ESP8266, built-in LED)
  5                         // capture_interval seconds
};

// State variables
WiFiUDP udp;
unsigned long lastMotionTime = 0;
bool motionActive = false;
bool doorLastState = false;
bool windowLastState = false;
unsigned long lastDiscoveryTime = 0;
const int discoveryInterval = 30000; // 30 seconds between discovery broadcasts
String mac_address = "";

void setup() {
  // Initialize serial connection
  Serial.begin(115200);
  Serial.println("\n\nESP Security Sensor Starting...");

  // Initialize EEPROM for storing device ID and configuration
  EEPROM.begin(512);

  // Initialize pins
  pinMode(CONFIG.motion_pin, INPUT);
  pinMode(CONFIG.door_pin, INPUT_PULLUP); // Use pull-up for contact sensors
  pinMode(CONFIG.window_pin, INPUT_PULLUP);
  pinMode(CONFIG.led_pin, OUTPUT);
  digitalWrite(CONFIG.led_pin, LOW);

  // Load or generate device ID
  loadOrGenerateDeviceId();

  // Connect to WiFi
  setupWifi();

  // Start UDP for discovery and sensor updates
  udp.begin(CONFIG.discovery_port);
  
  // Flash LED to indicate successful startup
  for (int i = 0; i < 3; i++) {
    digitalWrite(CONFIG.led_pin, HIGH);
    delay(100);
    digitalWrite(CONFIG.led_pin, LOW);
    delay(100);
  }
  
  // Find the receiver initially
  discoverReceiver();

  Serial.println("ESP Security Sensor Ready");
}

void loop() {
  // Handle WiFi reconnection if needed
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    setupWifi();
  }

  // Check motion sensor
  checkMotionSensor();
  
  // Check door sensor
  checkDoorSensor();
  
  // Check window sensor
  checkWindowSensor();
  
  // Run discovery service periodically
  runDiscoveryService();
  
  // Process incoming UDP messages
  checkForUDPMessages();

  delay(100); // Small delay to prevent excessive loop execution
}

void loadOrGenerateDeviceId() {
  // Check if we have a saved device ID
  if (EEPROM.read(0) == 'I' && EEPROM.read(1) == 'D') {
    // Read device ID from EEPROM
    for (int i = 0; i < 36; i++) {
      CONFIG.device_id[i] = char(EEPROM.read(i + 2));
    }
    CONFIG.device_id[36] = '\0';
    Serial.print("Loaded device ID: ");
    Serial.println(CONFIG.device_id);
    
    // Set device name based on MAC address
    mac_address = WiFi.macAddress();
    String defaultName = "ESP-" + mac_address.substring(9);
    defaultName.replace(":", "");
    strncpy(CONFIG.device_name, defaultName.c_str(), sizeof(CONFIG.device_name) - 1);
    CONFIG.device_name[sizeof(CONFIG.device_name) - 1] = '\0';
  } else {
    // Generate new UUID
    generateDeviceId();
  }
}

void generateDeviceId() {
  // Create a simple UUID-like string using MAC address and timestamp
  mac_address = WiFi.macAddress();
  String timestamp = String(millis());
  
  String uuid = "";
  uuid += mac_address.substring(0, 2);
  uuid += mac_address.substring(3, 5);
  uuid += mac_address.substring(6, 8);
  uuid += mac_address.substring(9, 11);
  uuid += "-";
  uuid += mac_address.substring(12, 14);
  uuid += mac_address.substring(15, 17);
  uuid += "-";
  uuid += timestamp.substring(0, 4);
  uuid += "-";
  uuid += String(random(1000, 9999));
  uuid += "-";
  uuid += String(random(100000000, 999999999));
  
  // Store in CONFIG
  strncpy(CONFIG.device_id, uuid.c_str(), sizeof(CONFIG.device_id) - 1);
  CONFIG.device_id[sizeof(CONFIG.device_id) - 1] = '\0';
  
  // Set device name based on MAC
  String defaultName = "ESP-" + mac_address.substring(9);
  defaultName.replace(":", "");
  strncpy(CONFIG.device_name, defaultName.c_str(), sizeof(CONFIG.device_name) - 1);
  CONFIG.device_name[sizeof(CONFIG.device_name) - 1] = '\0';
  
  // Save device ID in EEPROM
  EEPROM.write(0, 'I');
  EEPROM.write(1, 'D');
  for (int i = 0; i < 36 && i < uuid.length(); i++) {
    EEPROM.write(i + 2, uuid[i]);
  }
  EEPROM.commit();
  
  Serial.print("Generated new device ID: ");
  Serial.println(CONFIG.device_id);
}

void setupWifi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  // Wait for connection with timeout
  int timeout = 0;
  while (WiFi.status() != WL_CONNECTED && timeout < 20) {
    digitalWrite(CONFIG.led_pin, !digitalRead(CONFIG.led_pin)); // Blink LED while connecting
    delay(500);
    Serial.print(".");
    timeout++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(CONFIG.led_pin, HIGH); // LED on when connected
    delay(500);
    digitalWrite(CONFIG.led_pin, LOW);
  } else {
    Serial.println("");
    Serial.println("WiFi connection failed!");
    // Fast blink to indicate failure
    for (int i = 0; i < 10; i++) {
      digitalWrite(CONFIG.led_pin, !digitalRead(CONFIG.led_pin));
      delay(100);
    }
    digitalWrite(CONFIG.led_pin, LOW);
  }
}

void checkMotionSensor() {
  // Read the motion sensor
  int motionState = digitalRead(CONFIG.motion_pin);
  
  // Check if motion is detected and cooldown period has passed
  if (motionState == HIGH && !motionActive && 
      (millis() - lastMotionTime > CONFIG.capture_interval * 1000)) {
    
    Serial.println("Motion detected!");
    motionActive = true;
    lastMotionTime = millis();
    
    // Send sensor update
    sendSensorUpdate("motion", "DETECTED");
    
    // Flash the LED
    digitalWrite(CONFIG.led_pin, HIGH);
    delay(100);
    digitalWrite(CONFIG.led_pin, LOW);
  }
  else if (motionState == LOW && motionActive) {
    motionActive = false;
  }
}

void checkDoorSensor() {
  // Read the door sensor (LOW when open with pullup)
  bool doorState = !digitalRead(CONFIG.door_pin);
  
  // Check if door state changed
  if (doorState != doorLastState) {
    doorLastState = doorState;
    
    if (doorState) {
      Serial.println("Door opened!");
      sendSensorUpdate("door", "OPEN");
    } else {
      Serial.println("Door closed!");
      sendSensorUpdate("door", "CLOSED");
    }
    
    // Flash the LED
    digitalWrite(CONFIG.led_pin, HIGH);
    delay(100);
    digitalWrite(CONFIG.led_pin, LOW);
  }
}

void checkWindowSensor() {
  // Read the window sensor (LOW when open with pullup)
  bool windowState = !digitalRead(CONFIG.window_pin);
  
  // Check if window state changed
  if (windowState != windowLastState) {
    windowLastState = windowState;
    
    if (windowState) {
      Serial.println("Window opened!");
      sendSensorUpdate("window", "OPEN");
    } else {
      Serial.println("Window closed!");
      sendSensorUpdate("window", "CLOSED");
    }
    
    // Flash the LED
    digitalWrite(CONFIG.led_pin, HIGH);
    delay(100);
    digitalWrite(CONFIG.led_pin, LOW);
  }
}

void sendSensorUpdate(const char* sensorType, const char* status) {
  // Format message according to the protocol: SENSOR:{DEVICE_ID}:{DEVICE_NAME}:{TYPE}:{STATUS}
  String message = "SENSOR:";
  message += CONFIG.device_id;
  message += ":";
  message += CONFIG.device_name;
  message += ":";
  message += sensorType;
  message += ":";
  message += status;
  
  // Send message via UDP
  udp.beginPacket(CONFIG.receiver_ip, CONFIG.udp_port);
  udp.write(message.c_str());
  udp.endPacket();
  
  Serial.print("Sent update: ");
  Serial.println(message);
}

void discoverReceiver() {
  Serial.println("Discovering receiver...");
  
  // Send discovery message via broadcast
  IPAddress broadcastIP(255, 255, 255, 255);
  String discoveryMessage = "DISCOVER:SENDER";
  
  int maxAttempts = 5;
  bool discovered = false;
  
  for (int attempt = 1; attempt <= maxAttempts && !discovered; attempt++) {
    Serial.print("Discovery attempt ");
    Serial.print(attempt);
    Serial.println("...");
    
    // Send discovery message
    udp.beginPacket(broadcastIP, CONFIG.discovery_port);
    udp.write(discoveryMessage.c_str());
    udp.endPacket();
    
    // Wait for response with timeout
    unsigned long startTime = millis();
    while (millis() - startTime < 2000 && !discovered) {
      int packetSize = udp.parsePacket();
      if (packetSize) {
        char incomingPacket[255];
        int len = udp.read(incomingPacket, 255);
        if (len > 0) {
          incomingPacket[len] = '\0';
          String receivedData = String(incomingPacket);
          
          Serial.print("Received: ");
          Serial.println(receivedData);
          
          // Check if this is a response from the receiver
          if (receivedData.startsWith("SECURITY_SYSTEM:ONLINE:")) {
            String ip = receivedData.substring(receivedData.indexOf(":", 18) + 1);
            ip = ip.substring(0, ip.indexOf(":"));
            
            Serial.print("Found receiver at: ");
            Serial.println(ip);
            
            strncpy(CONFIG.receiver_ip, ip.c_str(), sizeof(CONFIG.receiver_ip) - 1);
            CONFIG.receiver_ip[sizeof(CONFIG.receiver_ip) - 1] = '\0';
            
            discovered = true;
            
            // Flash LED to indicate successful discovery
            for (int i = 0; i < 5; i++) {
              digitalWrite(CONFIG.led_pin, HIGH);
              delay(50);
              digitalWrite(CONFIG.led_pin, LOW);
              delay(50);
            }
          }
        }
      }
      delay(10);
    }
    
    // Wait before next attempt
    if (!discovered && attempt < maxAttempts) {
      delay(1000);
    }
  }
  
  if (!discovered) {
    Serial.println("Failed to discover receiver. Using default IP.");
  }
}

void runDiscoveryService() {
  // Only run discovery broadcast periodically
  if (millis() - lastDiscoveryTime > discoveryInterval) {
    lastDiscoveryTime = millis();
    
    // Broadcast presence
    String message = "SECURITY_DEVICE:ONLINE:";
    message += CONFIG.device_id;
    message += ":";
    message += CONFIG.device_name;
    
    IPAddress broadcastIP(255, 255, 255, 255);
    udp.beginPacket(broadcastIP, CONFIG.discovery_port);
    udp.write(message.c_str());
    udp.endPacket();
    
    Serial.println("Broadcast device presence");
  }
}

void checkForUDPMessages() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    char incomingPacket[255];
    int len = udp.read(incomingPacket, 255);
    if (len > 0) {
      incomingPacket[len] = '\0';
      String receivedData = String(incomingPacket);
      
      Serial.print("UDP Message: ");
      Serial.println(receivedData);
      
      // Process discovery requests
      if (receivedData.startsWith("DISCOVER:")) {
        // Send a direct response with device info
        String response = "SECURITY_DEVICE:ONLINE:";
        response += CONFIG.device_id;
        response += ":";
        response += CONFIG.device_name;
        
        udp.beginPacket(udp.remoteIP(), udp.remotePort());
        udp.write(response.c_str());
        udp.endPacket();
        
        Serial.print("Responded to discovery request from ");
        Serial.println(udp.remoteIP());
      }
      
      // Process GPIO config updates
      if (receivedData.startsWith("CONFIG:GPIO:")) {
        handleGPIOConfigUpdate(receivedData);
      }
    }
  }
}

void handleGPIOConfigUpdate(String data) {
  // Parse CONFIG:GPIO:DEVICE_ID:motion_pin:door_pin:window_pin:led_pin
  int parts[7]; // To store the positions of each colon
  int partCount = 0;
  
  // Find all colons
  for (int i = 0; i < data.length() && partCount < 7; i++) {
    if (data.charAt(i) == ':') {
      parts[partCount++] = i;
    }
  }
  
  // Check if we have enough parts
  if (partCount >= 6) {
    String deviceId = data.substring(parts[1] + 1, parts[2]);
    
    // Process only if for this device or broadcast ("all")
    if (deviceId == "all" || deviceId == CONFIG.device_id) {
      Serial.println("Processing GPIO config update");
      
      // Parse pin values
      int motion_pin = data.substring(parts[2] + 1, parts[3]).toInt();
      int door_pin = data.substring(parts[3] + 1, parts[4]).toInt();
      int window_pin = data.substring(parts[4] + 1, parts[5]).toInt();
      int led_pin = data.substring(parts[5] + 1).toInt();
      
      Serial.print("New pin configuration: Motion=");
      Serial.print(motion_pin);
      Serial.print(", Door=");
      Serial.print(door_pin);
      Serial.print(", Window=");
      Serial.print(window_pin);
      Serial.print(", LED=");
      Serial.println(led_pin);
      
      // Store configuration
      CONFIG.motion_pin = motion_pin;
      CONFIG.door_pin = door_pin;
      CONFIG.window_pin = window_pin; 
      CONFIG.led_pin = led_pin;
      
      // Update pin modes
      // First, cleanup if we're changing pins
      pinMode(CONFIG.motion_pin, INPUT);
      pinMode(CONFIG.door_pin, INPUT_PULLUP);
      pinMode(CONFIG.window_pin, INPUT_PULLUP);
      pinMode(CONFIG.led_pin, OUTPUT);
      
      // Acknowledge configuration update
      String ack = "GPIO_CONFIG_UPDATED:";
      ack += CONFIG.device_id;
      
      udp.beginPacket(CONFIG.receiver_ip, CONFIG.udp_port);
      udp.write(ack.c_str());
      udp.endPacket();
      
      Serial.println("GPIO configuration updated and acknowledged");
    }
  }
}