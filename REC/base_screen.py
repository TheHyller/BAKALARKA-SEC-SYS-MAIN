"""
Modul poskytuje základnú triedu obrazovky pre aplikáciu.
Zabezpečuje konzistentný layout a štýlovanie pre všetky obrazovky.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from theme_helper import COLORS, FONT_SIZES

class BaseScreen(Screen):
    """Základná trieda pre všetky obrazovky aplikácie poskytujúca štandardné rozloženie a funkcie"""
    
    def __init__(self, **kwargs):
        """Inicializácia základnej obrazovky s štandardným rozložením"""
        super(BaseScreen, self).__init__(**kwargs)
        
        # Vytvorenie hlavného rozloženia
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.add_widget(self.layout)
        
        # Príprava na pridanie hlavičky
        self.header = None
        self.content_area = None
        self.footer = None
    
    def set_title(self, title_text, font_size=FONT_SIZES['large']):
        """Nastavenie titulku obrazovky"""
        # Ak už hlavička existuje, vyčisti ju
        if self.header:
            self.header.clear_widgets()
        else:
            self.header = BoxLayout(orientation='horizontal', size_hint_y=0.1)
            self.layout.add_widget(self.header)
        
        # Pridanie titulku
        title = Label(text=title_text, font_size=font_size, halign='center', valign='middle')
        title.bind(size=lambda s, w: setattr(s, 'text_size', w))
        self.header.add_widget(title)
    
    def add_back_button(self, target_screen='main'):
        """Pridanie tlačidla Späť do hlavičky"""
        if not self.header:
            self.set_title("")  # Vytvorenie prázdnej hlavičky, ak neexistuje
        
        # Pridanie tlačidla Späť do ľavej časti hlavičky
        back_button = Button(text="Späť", size_hint=(0.2, 1))
        back_button.bind(on_release=lambda x: self.go_to_screen(target_screen))
        
        # Pridanie tlačidla na začiatok hlavičky
        self.header.add_widget(back_button, index=len(self.header.children))
    
    def create_content_area(self):
        """Vytvorenie oblasti obsahu s predvoleným boxlayout"""
        self.content_area = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.8)
        self.layout.add_widget(self.content_area)
        return self.content_area
    
    def create_footer(self):
        """Vytvorenie oblasti päty s predvoleným boxlayout"""
        self.footer = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.1)
        self.layout.add_widget(self.footer)
        return self.footer
    
    def go_to_screen(self, screen_name):
        """Prechod na inú obrazovku"""
        if self.manager:
            self.manager.current = screen_name
    
    def add_content_widget(self, widget):
        """Pridanie widgetu do oblasti obsahu"""
        if not self.content_area:
            self.create_content_area()
        self.content_area.add_widget(widget)
    
    def add_footer_widget(self, widget):
        """Pridanie widgetu do oblasti päty"""
        if not self.footer:
            self.create_footer()
        self.footer.add_widget(widget)