"""
Tooltip utility for GUI widgets
"""
import tkinter as tk


class ToolTip:
    """
    Create a tooltip for a given widget with improved styling
    """

    def __init__(self, widget, text, delay=500):
        """
        Initialize tooltip

        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text to display
            delay: Delay in milliseconds before showing tooltip
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.after_id = None

        # Bind events
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<Button>", self.on_leave)

    def on_enter(self, event=None):
        """Mouse entered widget"""
        self.schedule_tooltip()

    def on_leave(self, event=None):
        """Mouse left widget"""
        self.cancel_tooltip()
        self.hide_tooltip()

    def schedule_tooltip(self):
        """Schedule tooltip to show after delay"""
        self.cancel_tooltip()
        self.after_id = self.widget.after(self.delay, self.show_tooltip)

    def cancel_tooltip(self):
        """Cancel scheduled tooltip"""
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def show_tooltip(self):
        """Display the tooltip"""
        if self.tooltip_window or not self.text:
            return

        # Get widget position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        # Create tooltip window
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        # Create label with styled background
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            foreground="#000000",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9, "normal"),
            padx=8,
            pady=5
        )
        label.pack()

    def hide_tooltip(self):
        """Hide the tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def create_tooltip(widget, text, delay=500):
    """
    Helper function to quickly create a tooltip

    Args:
        widget: Widget to attach tooltip to
        text: Tooltip text
        delay: Delay before showing (ms)

    Returns:
        ToolTip instance
    """
    return ToolTip(widget, text, delay)
