"""
Theme helper module for the security system application.
Provides consistent styling across all screens.
"""

# Light theme colors
COLORS = {
    'background': (1, 1, 1, 1),  # White
    'text': (0, 0, 0, 1),  # Black
    'primary': (0, 0.6, 1, 1),  # Blue
    'secondary': (0.9, 0.9, 0.9, 1),  # Light Gray
    'success': (0, 0.8, 0, 1),  # Green
    'warning': (1, 0.8, 0, 1),  # Yellow
    'error': (1, 0, 0, 1),  # Red
    'button': (0.9, 0.9, 0.9, 1),  # Light Gray for buttons
    'button_text': (0, 0, 0, 1),  # Black text for buttons
}

# Font sizes
FONT_SIZES = {
    'small': 18,
    'medium': 22,
    'large': 28,
    'xlarge': 32,
    'title': 36,
}

def apply_theme(widget):
    """Applies theme to a widget based on its type"""
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.textinput import TextInput
    
    if isinstance(widget, Label):
        widget.color = COLORS['text']
        if hasattr(widget, 'font_size') and widget.font_size < FONT_SIZES['small']:
            widget.font_size = FONT_SIZES['small']
    
    elif isinstance(widget, Button):
        widget.background_color = COLORS['button']
        widget.color = COLORS['button_text']
        if hasattr(widget, 'font_size') and widget.font_size < FONT_SIZES['medium']:
            widget.font_size = FONT_SIZES['medium']
    
    elif isinstance(widget, TextInput):
        widget.background_color = COLORS['background']
        widget.foreground_color = COLORS['text']
        if hasattr(widget, 'font_size') and widget.font_size < FONT_SIZES['small']:
            widget.font_size = FONT_SIZES['small']

def style_screen(screen):
    """Recursively styles all widgets in a screen"""
    apply_theme(screen)
    
    if hasattr(screen, 'children'):
        for child in screen.children:
            style_screen(child)