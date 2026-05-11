from tkinter import Label, Toplevel
from typing import Any

from config import UI_CONFIG


class InfoTooltip:
    """Tooltip widget that displays information on hover."""

    def __init__(self, widget: Any, text: str) -> None:
        """Initializes the tooltip for a widget."""
        self.widget: Any = widget
        self.text: str = text
        self.tooltip: Toplevel | None = None
        widget.bind('<Enter>', self._on_enter)
        widget.bind('<Leave>', self._on_leave)

    def _on_enter(self, event: Any = None) -> None:
        """Displays the tooltip when the mouse enters the widget."""
        x, y, _, _ = self.widget.bbox('insert')
        offset_x, offset_y = UI_CONFIG['TOOLTIP_OFFSET']
        x += self.widget.winfo_rootx() + offset_x
        y += self.widget.winfo_rooty() + offset_y
        
        self.tooltip = Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f'+{x}+{y}')
        
        label = Label(
            self.tooltip,
            text=self.text,
            background=UI_CONFIG['TOOLTIP_BG'],
            relief='solid',
            borderwidth=1,
            padx=5,
            pady=2
        )
        label.pack()

    def _on_leave(self, event: Any = None) -> None:
        """Removes the tooltip when the mouse leaves the widget."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

