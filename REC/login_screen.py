# Inicializácia balíka
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from config.settings import validate_pin

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Nadpis
        layout.add_widget(Label(
            text="Security System Login",
            font_size=24,
            size_hint_y=0.2
        ))
        
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
        layout.add_widget(self.pin_display)
        
        # Klávesnica
        keypad_layout = GridLayout(cols=3, spacing=[10, 10], size_hint_y=0.5)
        
        # Vytvorenie tlačidiel s číslami
        for i in range(1, 10):  # Vytvorí tlačidlá 1 až 9
            btn = Button(text=str(i), font_size=24)
            btn.bind(on_release=self.on_button_press)
            keypad_layout.add_widget(btn)
            
        # Pridanie tlačidiel vymazať, 0 a enter
        btn_clear = Button(text="Clear", font_size=20)
        btn_clear.bind(on_release=self.on_clear)
        keypad_layout.add_widget(btn_clear)
        
        btn_0 = Button(text="0", font_size=24)
        btn_0.bind(on_release=self.on_button_press)
        keypad_layout.add_widget(btn_0)
        
        btn_enter = Button(text="Enter", font_size=20)
        btn_enter.bind(on_release=self.on_enter_pressed)
        keypad_layout.add_widget(btn_enter)
        
        layout.add_widget(keypad_layout)
        
        # Stavová správa
        self.status_label = Label(
            text="Enter PIN to access system",
            font_size=18,
            size_hint_y=0.2
        )
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)
    
    # Oprava: Toto by malo byť správne pomenované, aby sa predišlo konfliktu s udalosťou Kivy on_enter
    def on_enter_pressed(self, instance):
        """Spracuje stlačenie tlačidla Enter"""
        if validate_pin(self.pin_input):
            print("DEBUG: PIN úspešne overený, prístup povolený")
            self.status_label.text = "Access granted"
            self.manager.current = 'main'
        else:
            print(f"DEBUG: Zadaný neplatný PIN: {self.pin_input}")
            self.status_label.text = "Invalid PIN, please try again"
            self.pin_input = ""
            self.pin_display.text = ""
        
    def on_button_press(self, instance):
        self.pin_input += instance.text
        self.pin_display.text = "*" * len(self.pin_input)
        
    def on_clear(self, instance):
        self.pin_input = ""
        self.pin_display.text = ""
    
    # Toto je metóda udalosti Kivy, ktorá potrebuje správnu signatúru
    def on_enter(self):
        """Volá sa pri vstupe na obrazovku"""
        print("DEBUG: Vstup na prihlasovaciu obrazovku")
        # Pri návrate na túto obrazovku vynuluj vstup PIN
        self.pin_input = ""
        self.pin_display.text = ""
        self.status_label.text = "Enter PIN to access system"