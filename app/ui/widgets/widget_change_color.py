import flet as ft

COLORS = [
    {"color": ft.colors.INDIGO, "name": "Indigo"},
    {"color": ft.colors.BLUE, "name": "Blue (default)"},
    {"color": ft.colors.TEAL, "name": "Teal"},
    {"color": ft.colors.GREEN, "name": "Green"},
    {"color": ft.colors.YELLOW, "name": "Yellow"},
    {"color": ft.colors.ORANGE, "name": "Orange"},
    {"color": ft.colors.DEEP_ORANGE, "name": "Deep orange"},
    {"color": ft.colors.PINK, "name": "Pink"},
    {"color": ft.colors.RED, "name": "Red"},
    {"color": ft.colors.PURPLE, "name": "Purple"},
    {"color": ft.colors.DEEP_PURPLE, "name": "Deep Purple"},
    {"color": ft.colors.CYAN, "name": "Cyan"},
    {"color": ft.colors.LIGHT_GREEN, "name": "Light Green"},
    {"color": ft.colors.LIME, "name": "Lime"},
    {"color": ft.colors.BROWN, "name": "Brown"},
    {"color": ft.colors.GREY, "name": "Grey"},
    {"color": ft.colors.BLUE_GREY, "name": "Blue Grey"}
]

class ColorMenuItem(ft.PopupMenuItem):
    def __init__(self, color, name):
        super().__init__()

        self.icon_widget = ft.Icon(name=ft.icons.COLOR_LENS_OUTLINED, color=color)
        self.text_widget = ft.Text(name)

        self.content = ft.Row()
        self.content.controls = [
            self.icon_widget,
            self.text_widget
        ]

        self.on_click = self.change_color
        self.data = color

    def change_color(self, e):
        self.page.theme = self.page.dark_theme = ft.Theme(color_scheme_seed=self.data)
        self.page.update()

class ColorMenuButton(ft.PopupMenuButton):
    def __init__(self):
        super().__init__()
        self.tooltip = "Change colors"
        self.icon = ft.icons.COLOR_LENS_OUTLINED
        self.items = [ColorMenuItem(color=data['color'], name=data['name']) for data in COLORS]
