import torch
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from diffusionjob import DiffusionSettings, DiffusionJob
from error import ErrorReporter
from widgets import ImageView


class DiffusionBox(Gtk.Box):
    def __init__(self, models, prompt_widget, settings=DiffusionSettings(), window=None):
        super().__init__()
        self.window = window
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.models = models

        # add settings panel
        self.create_settings_frame()
        self.pack_start(self.settings_frame, False, True, 5)

        # add user prompt panel
        self.prompt_widget = prompt_widget
        self.pack_start(prompt_widget, False, True, 5)

        # add start button and spinner
        self.button_box = Gtk.Box()
        self.start_button = Gtk.Button(label='Start')
        self.start_button.connect('clicked', self.start_diffusion)
        self.button_box.pack_start(self.start_button, True, True, 5)
        self.status_spinner = Gtk.Spinner()
        self.button_box.pack_start(self.status_spinner, False, False, 5)
        self.pack_start(self.button_box, False, True, 5)

        # add image view
        self.image_view = ImageView(window=window)
        self.pack_start(self.image_view, True, True, 5)

        DiffusionJob.register_ui(self)
        self.show_all()
        self.status_spinner.set_visible(False)

    def create_settings_frame(self, settings=DiffusionSettings()):
        # frame and box to place all settings in
        self.settings_frame = Gtk.Frame()
        self.settings_frame.set_label('Settings')
        self.settings_frame.set_margin_end(5)
        self.settings_frame.set_margin_start(5)
        self.settings_box = Gtk.Box()
        self.settings_box.set_orientation(Gtk.Orientation.VERTICAL)
        self.settings_frame.add(self.settings_box)

        # selector for model
        self.model_box = Gtk.Box()
        self.model_selector = Gtk.ComboBoxText()
        for model in self.models:
            self.model_selector.append_text(model)
        self.model_selector.set_active(0)
        self.model_box.pack_start(self.model_selector, True, True, 5)
        self.settings_box.pack_start(self.model_box, False, False, 5)

        # configuration options for machine and acceleration platform
        self.machine_settings_box = Gtk.Box()
        self.device_selector = Gtk.ComboBoxText()
        if torch.cuda.is_available():
            self.device_selector.append_text('CUDA')
        self.device_selector.append_text('CPU')
        self.device_selector.set_active(0)
        self.machine_settings_box.pack_start(self.device_selector, True, True, 5)
        self.low_memory_button = Gtk.CheckButton(label='Low Memory Mode')
        self.low_memory_button.set_active(settings.low_mem)
        self.machine_settings_box.pack_start(self.low_memory_button, False, False, 5)
        self.settings_box.pack_start(self.machine_settings_box, False, False, 5)

        # details on how (steps), how big (width, height) and how many images to generate
        self.image_settings_box = Gtk.Box()
        self.width_label = Gtk.Label(label='Width: ')
        self.width_spin_button = Gtk.SpinButton()
        self.width_spin_button.set_range(0, 2048)
        self.width_spin_button.set_increments(8, 64)
        self.width_spin_button.set_value(settings.width)
        self.image_settings_box.pack_start(self.width_label, False, False, 5)
        self.image_settings_box.pack_start(self.width_spin_button, False, False, 5)
        self.height_label = Gtk.Label(label='Height: ')
        self.height_spin_button = Gtk.SpinButton()
        self.height_spin_button.set_range(0, 2048)
        self.height_spin_button.set_increments(8, 64)
        self.height_spin_button.set_value(settings.height)
        self.image_settings_box.pack_start(self.height_label, False, False, 5)
        self.image_settings_box.pack_start(self.height_spin_button, False, False, 5)
        self.steps_label = Gtk.Label(label='Steps: ')
        self.steps_spin_button = Gtk.SpinButton()
        self.steps_spin_button.set_range(1, 1000)
        self.steps_spin_button.set_increments(1, 10)
        self.steps_spin_button.set_value(settings.steps)
        self.image_settings_box.pack_start(self.steps_label, False, False, 5)
        self.image_settings_box.pack_start(self.steps_spin_button, False, False, 5)
        self.nimages_label = Gtk.Label(label='Number of images: ')
        self.nimages_spin_button = Gtk.SpinButton()
        self.nimages_spin_button.set_range(1, 50)
        self.nimages_spin_button.set_increments(1, 5)
        self.nimages_spin_button.set_value(1)
        self.image_settings_box.pack_start(self.nimages_label, False, False, 5)
        self.image_settings_box.pack_start(self.nimages_spin_button, False, False, 5)
        self.settings_box.pack_start(self.image_settings_box, False, False, 5)

    def show_diffusion_running(self, state):
        if state:
            self.status_spinner.start()
            self.status_spinner.set_visible(True)
            self.start_button.set_sensitive(False)
        else:
            self.status_spinner.stop()
            self.status_spinner.set_visible(False)
            self.start_button.set_sensitive(True)

    def start_diffusion(self, _source):
        prompt = self.prompt_widget.get_prompt()
        settings = DiffusionSettings(
            model = self.model_selector.get_active_text(),
            device = self.device_selector.get_active_text().lower(),
            low_mem = self.low_memory_button.get_active(),
            width = self.width_spin_button.get_value_as_int(),
            height = self.height_spin_button.get_value_as_int(),
            steps = self.steps_spin_button.get_value_as_int(),
            nimages = self.nimages_spin_button.get_value_as_int(),
        )
        error_reporter = ErrorReporter(window=self.window)

        job = DiffusionJob(self.models, prompt, settings, self.image_view, error_reporter)
        job.run_async()



