"""
Modul pomocníka témy pre aplikáciu bezpečnostného systému.
Poskytuje konzistentný štýl naprieč všetkými obrazovkami.
"""
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.lang import Builder
from kivy.core.window import Window

# Explicitné nastavenie farby okna
Window.clearcolor = (1, 1, 1, 1)

# Farby svetlej témy
COLORS = {
    'background': (1, 1, 1, 1),  # Biela
    'text': (0, 0, 0, 1),  # Čierna
    'primary': (0, 0.6, 1, 1),  # Modrá
    'secondary': (0.95, 0.95, 0.95, 1),  # Veľmi svetlá sivá
    'success': (0, 0.8, 0, 1),  # Zelená
    'warning': (1, 0.8, 0, 1),  # Žltá
    'error': (1, 0, 0, 1),  # Červená
    'button': (1, 1, 1, 1),  # Biela pre tlačidlá
    'button_text': (0, 0, 0, 1),  # Čierny text pre tlačidlá
    'button_border': (0.8, 0.8, 0.8, 1),  # Svetlý sivý okraj
    'popup_background': (1, 1, 1, 1),  # Biela pre pozadie vyskakovacích okien
    'popup_title': (0, 0, 0, 1),  # Čierna pre titulky vyskakovacích okien
}

# Veľkosti písma
FONT_SIZES = {
    'small': 18,
    'medium': 22,
    'large': 28,
    'xlarge': 32,
    'title': 36,
}

# Aplikácia globálnych štýlov Kivy
Builder.load_string('''
<Button>:
    background_color: 1, 1, 1, 1
    background_normal: ''
    color: 0, 0, 0, 1
    bold: True
    font_size: '22sp'
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.8, 0.8, 0.8, 1
        Line:
            width: 1.5
            rectangle: self.x, self.y, self.width, self.height

<Label>:
    color: 0, 0, 0, 1
    bold: True
    font_size: '18sp'

<TextInput>:
    background_color: 1, 1, 1, 1
    foreground_color: 0, 0, 0, 1
    bold: True
    font_size: '18sp'
    padding: [10, 10, 10, 5]
    
<Spinner>:
    background_color: 1, 1, 1, 1
    background_normal: ''
    color: 0, 0, 0, 1
    bold: True
    font_size: '18sp'
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.8, 0.8, 0.8, 1
        Line:
            width: 1.5
            rectangle: self.x, self.y, self.width, self.height

<Popup>:
    background: ''
    background_color: 1, 1, 1, 1
    title_color: 0, 0, 0, 1
    title_size: '22sp'
    title_align: 'center'
    title_font: 'Roboto'
    separator_color: 0.8, 0.8, 0.8, 1
    border: (0, 0, 0, 0)
''')

def ensure_minimum_font_size(widget, min_size):
    """Zabezpečenie minimálnej veľkosti písma pre widget"""
    if hasattr(widget, 'font_size'):
        if isinstance(widget.font_size, (int, float)) and widget.font_size < min_size:
            widget.font_size = min_size

def set_rectangle_border(instance, background_color, border_color, line_width=1.5):
    """Nastavenie obdĺžnikového pozadia a okraja pre widget"""
    if hasattr(instance, 'canvas') and instance.canvas.before:
        instance.canvas.before.clear()
    
    with instance.canvas.before:
        # Pozadie
        Color(*background_color)
        Rectangle(pos=instance.pos, size=instance.size)
        
        # Okraj
        Color(*border_color)
        Line(rectangle=(instance.pos[0], instance.pos[1], instance.size[0], instance.size[1]), width=line_width)
    
    # Aktualizácia pri zmene veľkosti alebo pozície
    instance.bind(pos=lambda instance, value: update_rect(instance, background_color, border_color, line_width),
                  size=lambda instance, value: update_rect(instance, background_color, border_color, line_width))

def update_rect(instance, background_color, border_color, line_width=1.5):
    """Aktualizácia pozadia a okraja pri zmene veľkosti/pozície"""
    if hasattr(instance, 'canvas') and instance.canvas.before:
        instance.canvas.before.clear()
    
    with instance.canvas.before:
        # Pozadie
        Color(*background_color)
        Rectangle(pos=instance.pos, size=instance.size)
        
        # Okraj
        Color(*border_color)
        Line(rectangle=(instance.pos[0], instance.pos[1], instance.size[0], instance.size[1]), width=line_width)

def apply_button_style(button):
    """Aplikácia štýlu na tlačidlo"""
    button.background_color = (1, 1, 1, 1)
    button.background_normal = ''
    button.color = COLORS['text']
    button.bold = True
    
    ensure_minimum_font_size(button, FONT_SIZES['medium'])
    set_rectangle_border(button, COLORS['button'], COLORS['button_border'])

def apply_popup_style(popup):
    """Aplikácia štýlu na vyskakovacie okno a jeho obsah"""
    # Nastavenie vlastností vyskakovacieho okna
    popup.background = ''
    popup.background_color = COLORS['popup_background']
    popup.title_color = COLORS['popup_title']
    popup.title_size = str(FONT_SIZES['large']) + 'sp'
    popup.title_align = 'center'
    popup.title_font = 'Roboto'
    popup.separator_color = COLORS['button_border']
    
    # Štýlovanie obsahu vyskakovacieho okna, ak existuje
    if hasattr(popup, 'content') and popup.content is not None:
        style_screen(popup.content)

def apply_theme(widget):
    """Aplikácia témy na widget na základe jeho typu"""
    if isinstance(widget, Button):
        apply_button_style(widget)
    
    elif isinstance(widget, Label):
        widget.color = COLORS['text']
        widget.bold = True
        ensure_minimum_font_size(widget, FONT_SIZES['small'])
    
    elif isinstance(widget, TextInput):
        widget.background_color = COLORS['background']
        widget.foreground_color = COLORS['text']
        widget.bold = True
        ensure_minimum_font_size(widget, FONT_SIZES['small'])
    
    elif isinstance(widget, Spinner):
        apply_button_style(widget)  # Aplikácia rovnakého štýlu ako pre tlačidlá
        
    elif isinstance(widget, Popup):
        apply_popup_style(widget)

def style_screen(screen):
    """Aplikácia štýlovania na všetky widgety na obrazovke, rekurzívne spracovanie potomkov"""
    # Aplikácia témy na samotnú obrazovku
    apply_theme(screen)
    
    # Spracovanie všetkých priamych potomkov
    if hasattr(screen, 'children'):
        for child in screen.children:
            style_screen(child)
            
    # Špeciálne spracovanie widgetov s vlastnými potomkami, ktorí nie sú vo vlastnosti 'children'
    # Toto rieši prípady, keď Kivy používa vlastnosti ako 'content', atď.
    for prop_name in ['content', 'container', 'scroll_view', 'layout']:
        if hasattr(screen, prop_name) and getattr(screen, prop_name) is not None:
            child = getattr(screen, prop_name)
            style_screen(child)

# Funkcia na prepísanie vytvorenia vyskakovacieho okna, aby sa zabezpečilo aplikovanie témy
original_popup_open = Popup.open
def themed_popup_open(self, *args, **kwargs):
    """Prepísanie Popup.open na aplikáciu témy pred zobrazením"""
    apply_popup_style(self)
    original_popup_open(self, *args, **kwargs)

# Aplikácia našej tematickej metódy open na všetky vyskakovacie okná
Popup.open = themed_popup_open