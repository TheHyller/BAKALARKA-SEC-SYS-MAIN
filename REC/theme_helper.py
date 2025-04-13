"""
Theme helper module for the security system application.
Provides consistent styling across all screens.
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

# Set window color explicitly
Window.clearcolor = (1, 1, 1, 1)

# Light theme colors
COLORS = {
    'background': (1, 1, 1, 1),  # White
    'text': (0, 0, 0, 1),  # Black
    'primary': (0, 0.6, 1, 1),  # Blue
    'secondary': (0.95, 0.95, 0.95, 1),  # Very Light Gray
    'success': (0, 0.8, 0, 1),  # Green
    'warning': (1, 0.8, 0, 1),  # Yellow
    'error': (1, 0, 0, 1),  # Red
    'button': (1, 1, 1, 1),  # White for buttons
    'button_text': (0, 0, 0, 1),  # Black text for buttons
    'button_border': (0.8, 0.8, 0.8, 1),  # Light grey border
    'popup_background': (1, 1, 1, 1),  # White for popup backgrounds
    'popup_title': (0, 0, 0, 1),  # Black for popup titles
}

# Font sizes
FONT_SIZES = {
    'small': 18,
    'medium': 22,
    'large': 28,
    'xlarge': 32,
    'title': 36,
}

# Apply global Kivy styles
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

def apply_button_style(button):
    """Apply white background style to a button, overriding any existing styles"""
    # Ensure we have a clean canvas to work with
    if hasattr(button, 'canvas') and button.canvas.before:
        button.canvas.before.clear()
    
    # Set the button properties directly
    button.background_color = (1, 1, 1, 1)
    button.background_normal = ''
    button.color = COLORS['text']
    button.bold = True
    
    # Make sure font size is big enough
    if hasattr(button, 'font_size'):
        # Convert numeric values to dp if needed
        if isinstance(button.font_size, (int, float)):
            if button.font_size < FONT_SIZES['medium']:
                button.font_size = FONT_SIZES['medium']
        # If it's a string, we'll respect it
    
    # Draw our custom styling
    with button.canvas.before:
        # Background
        Color(*COLORS['button'])
        Rectangle(pos=button.pos, size=button.size)
        
        # Border
        Color(*COLORS['button_border'])
        Line(rectangle=(button.pos[0], button.pos[1], button.size[0], button.size[1]), width=1.5)
    
    # Update the rectangle when the button changes size
    button.bind(pos=update_button_rect, size=update_button_rect)

def apply_popup_style(popup):
    """Apply white background style to a popup and its content"""
    # Set popup properties
    popup.background = ''
    popup.background_color = COLORS['popup_background']
    popup.title_color = COLORS['popup_title']
    popup.title_size = str(FONT_SIZES['large']) + 'sp'
    popup.title_align = 'center'
    popup.title_font = 'Roboto'
    popup.separator_color = COLORS['button_border']
    
    # Style the popup content if it exists
    if hasattr(popup, 'content') and popup.content is not None:
        style_screen(popup.content)

def update_button_rect(instance, value):
    """Update button background and border when size/position changes"""
    # Clear existing canvas to prevent overdraw
    if hasattr(instance, 'canvas') and instance.canvas.before:
        instance.canvas.before.clear()
    
    # Redraw with new position and size
    with instance.canvas.before:
        # Background
        Color(*COLORS['button'])
        Rectangle(pos=instance.pos, size=instance.size)
        
        # Border
        Color(*COLORS['button_border'])
        Line(rectangle=(instance.pos[0], instance.pos[1], instance.size[0], instance.size[1]), width=1.5)

def apply_theme(widget):
    """Apply theming to a widget based on its type"""
    if isinstance(widget, Button):
        apply_button_style(widget)
    
    elif isinstance(widget, Label):
        widget.color = COLORS['text']
        widget.bold = True
        
        # Ensure minimum font size
        if hasattr(widget, 'font_size'):
            if isinstance(widget.font_size, (int, float)) and widget.font_size < FONT_SIZES['small']:
                widget.font_size = FONT_SIZES['small']
    
    elif isinstance(widget, TextInput):
        widget.background_color = COLORS['background']
        widget.foreground_color = COLORS['text']
        widget.bold = True
        
        # Ensure minimum font size
        if hasattr(widget, 'font_size'):
            if isinstance(widget.font_size, (int, float)) and widget.font_size < FONT_SIZES['small']:
                widget.font_size = FONT_SIZES['small']
    
    elif isinstance(widget, Spinner):
        apply_button_style(widget)  # Apply same styling as buttons
        
    elif isinstance(widget, Popup):
        apply_popup_style(widget)

def style_screen(screen):
    """Apply styling to all widgets in a screen, recursively processing child widgets"""
    # Apply theme to the screen itself
    apply_theme(screen)
    
    # Process all immediate children
    if hasattr(screen, 'children'):
        for child in screen.children:
            style_screen(child)
            
    # Special handling for widgets with their own children not in the 'children' property
    # This handles cases where Kivy uses properties like 'content', etc.
    for prop_name in ['content', 'container', 'scroll_view', 'layout']:
        if hasattr(screen, prop_name) and getattr(screen, prop_name) is not None:
            child = getattr(screen, prop_name)
            style_screen(child)

# Function to override popup creation to ensure theming is applied
original_popup_open = Popup.open
def themed_popup_open(self, *args, **kwargs):
    """Override of Popup.open to apply theming before showing"""
    apply_popup_style(self)
    original_popup_open(self, *args, **kwargs)

# Apply our themed open method to all popups
Popup.open = themed_popup_open