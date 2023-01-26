import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib

class ErrorReporter:
    def __init__(self, window=None):
        self.window = window

    def show_error(self, message, details=None):
        # create a fresh dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CANCEL,
            text=message,
        )
        if details:
            dialog.format_secondary_text(details)

        # show dialog
        dialog.run()
        dialog.destroy()



