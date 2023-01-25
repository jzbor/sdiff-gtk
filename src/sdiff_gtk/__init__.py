import array
import gi
import os.path
import torch
from PIL import Image
from diffusers import StableDiffusionPipeline
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
# from threading import Thread, Event
from multiprocessing import Process


MODEL='runwayml/stable-diffusion-v1-5'


class SaveableImage(Gtk.EventBox):
    def __init__(self, image, parent):
        super().__init__()
        self.image = image
        self.parent = parent

        pixbuf = img_to_pixbuf(image)
        self.image_widget = Gtk.Image(pixbuf=pixbuf);
        self.image_widget.set_visible(True);
        self.add(self.image_widget)

        self.connect('button-press-event', self.show_menu)

    def show_menu(self, source, event):
        if source == self:
            menu = Gtk.Menu()
            save_item = Gtk.MenuItem(label='Save image')
            save_item.connect('button-press-event', self.save)
            menu.append(save_item)

            menu.show_all()
            menu.popup_at_pointer(event)

    def save(self, widget, event):
        file_chooser = Gtk.FileChooserDialog(title='Please choose a destination',
                                             action=Gtk.FileChooserAction.SAVE,
                                             transient_for=self.parent)
        png_filter = Gtk.FileFilter()
        png_filter.set_name('PNG Image')
        png_filter.add_mime_type('image/png')
        file_chooser.add_filter(png_filter)
        file_chooser.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                 Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        file_chooser.set_current_name('sdiff.png')
        file_chooser.set_current_folder(self.parent.save_path)

        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = file_chooser.get_filename()
            self.parent.save_path = file_chooser.get_current_folder()
            self.save_as(filename)
        file_chooser.destroy()

    def save_as(self, filename):
        if not (filename.endswith('.png') or filename.endswith('.PNG')):
            filename += '.png'
        print('Saving image to', filename)
        self.image.save(filename)


class ApplicationWindow(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.generating = False
        self.save_path = '.'

        self.main_box = Gtk.Box()
        self.main_box.set_orientation(Gtk.Orientation.VERTICAL)

        self.create_settings_frame()
        self.main_box.pack_start(self.settings_frame, False, True, 5)

        self.prompt_frame = Gtk.Frame()
        self.prompt_frame.set_label('Prompt')
        self.prompt_frame.set_margin_end(5)
        self.prompt_frame.set_margin_start(5)
        self.prompt_field = Gtk.Entry()
        self.prompt_frame.add(self.prompt_field)
        self.main_box.pack_start(self.prompt_frame, False, True, 5)

        self.button_box = Gtk.Box()
        self.start_button = Gtk.Button(label='Start')
        self.start_button.connect('clicked', self.start_diffusion)
        self.button_box.pack_start(self.start_button, True, True, 5)
        self.stop_button = Gtk.Button(label='Stop')
        self.stop_button.connect('clicked', self.stop_generation)
        self.button_box.pack_start(self.stop_button, True, True, 5)
        self.status_spinner = Gtk.Spinner()
        self.button_box.pack_start(self.status_spinner, False, False, 5)
        self.main_box.pack_start(self.button_box, False, True, 5)

        self.image_window = Gtk.ScrolledWindow()
        self.image_box = Gtk.FlowBox()
        self.image_window.add(self.image_box);
        self.main_box.pack_start(self.image_window, True, True, 5)
        self.save_all_button = Gtk.Button(label='Save all images')
        self.save_all_button.connect('clicked', self.save_all)
        self.main_box.pack_start(self.save_all_button, False, True, 5)
        self.clear_button = Gtk.Button(label='Clear images')
        self.clear_button.connect('clicked', self.clear_images)
        self.main_box.pack_start(self.clear_button, False, True, 5)

        self.add(self.main_box);
        self.set_default_size(800, 850)
        self.show_all()
        self.status_spinner.set_visible(False)
        self.connect('destroy', Gtk.main_quit)

    def clear_images(self, _source):
        image_widgets = self.image_box.get_children()
        for widget in image_widgets:
            self.image_box.remove(widget)
            del(widget)

    def create_settings_frame(self):
        self.settings_frame = Gtk.Frame()
        self.settings_frame.set_label('Settings')
        self.settings_frame.set_margin_end(5)
        self.settings_frame.set_margin_start(5)
        self.settings_box = Gtk.Box()
        self.settings_box.set_orientation(Gtk.Orientation.VERTICAL)
        self.settings_frame.add(self.settings_box)

        self.machine_settings_box = Gtk.Box()
        self.device_selector = Gtk.ComboBoxText()
        if torch.cuda.is_available():
            self.device_selector.append_text('CUDA')
        self.device_selector.append_text('CPU')
        self.device_selector.set_active(0)
        self.machine_settings_box.pack_start(self.device_selector, True, True, 5)
        self.low_memory_button = Gtk.CheckButton(label='Low Memory Mode')
        self.low_memory_button.set_active(True)
        self.machine_settings_box.pack_start(self.low_memory_button, False, False, 5)
        self.settings_box.pack_start(self.machine_settings_box, False, False, 5)

        self.image_settings_box = Gtk.Box()
        self.width_label = Gtk.Label(label='Width: ')
        self.width_spin_button = Gtk.SpinButton()
        self.width_spin_button.set_range(0, 2048)
        self.width_spin_button.set_increments(8, 64)
        self.width_spin_button.set_value(256)
        self.image_settings_box.pack_start(self.width_label, False, False, 5)
        self.image_settings_box.pack_start(self.width_spin_button, False, False, 5)
        self.height_label = Gtk.Label(label='Height: ')
        self.height_spin_button = Gtk.SpinButton()
        self.height_spin_button.set_range(0, 2048)
        self.height_spin_button.set_increments(8, 64)
        self.height_spin_button.set_value(256)
        self.image_settings_box.pack_start(self.height_label, False, False, 5)
        self.image_settings_box.pack_start(self.height_spin_button, False, False, 5)
        self.steps_label = Gtk.Label(label='Steps: ')
        self.steps_spin_button = Gtk.SpinButton()
        self.steps_spin_button.set_range(1, 1000)
        self.steps_spin_button.set_increments(1, 10)
        self.steps_spin_button.set_value(50)
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

    def start_diffusion(self, _source):
        if self.generating:
            return
        else:
            self.generating = True

        prompt = self.prompt_field.get_buffer().get_text()
        steps = self.steps_spin_button.get_value_as_int()
        nimages = self.nimages_spin_button.get_value_as_int()
        width = self.width_spin_button.get_value_as_int()
        height = self.height_spin_button.get_value_as_int()
        device = self.device_selector.get_active_text().lower()
        low_mem = self.low_memory_button.get_active()

        self.show_running(True)

        self.thread = Process(target=self.generate_images, args=(prompt, steps, nimages, width, height, device, low_mem))
        self.thread.start()

    def stop_generation(self, _source):
        if (self.thread and self.generating):
            self.thread.terminate()
            self.generating = False
            print('Killed worker')
            self.show_running(False)

    def save_all(self, _source):
        file_chooser = Gtk.FileChooserDialog(title='Please choose a destination',
                                             action=Gtk.FileChooserAction.SELECT_FOLDER,
                                             transient_for=self)
        file_chooser.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                 Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        file_chooser.set_current_folder(self.save_path)

        response = file_chooser.run()
        print(response == Gtk.ResponseType.OK, file_chooser.get_filename())
        if response == Gtk.ResponseType.OK:
            self.save_path = file_chooser.get_filename()
            image_widgets = self.image_box.get_children()
            for i, image_widget in enumerate(image_widgets):
                print('save')
                path = os.path.join(self.save_path, f"sdiff-gtk-{i}.png")
                image_widget.get_child().save_as(path)
        file_chooser.destroy()


    def show_running(self, state):
        if state:
            self.status_spinner.start()
            self.status_spinner.set_visible(True)
            self.start_button.set_sensitive(False)
        else:
            self.status_spinner.stop()
            self.status_spinner.set_visible(False)
            self.start_button.set_sensitive(True)

    def add_image(self, pixbuf):
        image_widget = Gtk.Image(pixbuf=pixbuf)
        image_widget.connect('clicked', self.show_image_menu)

    def generate_images(self, prompt, steps, nimages, width, height, device = 'cpu', low_mem = False):
        print('Prompt:', prompt)
        pipeline = None
        try:
            pipeline = StableDiffusionPipeline.from_pretrained(MODEL, low_cpu_mem_usage=low_mem) \
                        .to(device)
            for i in range(0, nimages):
                    image = pipeline(prompt, num_inference_steps=steps, width=width, height=height).images[0]
                    image_widget = SaveableImage(image, self);
                    image_widget.set_visible(True)
                    # self.image_box.pack_start(image_widget, True, True, 5)
                    self.image_box.add(image_widget)
        except ValueError as e:
            self.show_error('Invalid parameters', str(e))
        except Exception as e:
            self.show_error('Unexpected error', str(e))

        del(pipeline)
        self.generating = False
        self.show_running(False)

    def show_error(self, message, details):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CANCEL,
            text=message,
        )
        if details:
            dialog.format_secondary_text(details)
        dialog.run()
        dialog.destroy()



def img_to_pixbuf(img):
    data = GLib.Bytes(img.tobytes())
    width, height = img.size
    return GdkPixbuf.Pixbuf.new_from_bytes(data, GdkPixbuf.Colorspace.RGB,
                                           False, 8, width, height, width * 3)

if __name__ == '__main__':
    # gradient calculation is not required for inference and might slow things down
    # so we can disable it
    torch.no_grad()

    ApplicationWindow()
    Gtk.main()
