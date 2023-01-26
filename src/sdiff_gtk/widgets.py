import gi
import os.path
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib

class ImageView(Gtk.Box):
    def __init__(self, window=None):
        super().__init__()
        self.window = window
        self.set_orientation(Gtk.Orientation.VERTICAL)

        # add scrolled window for images
        self.scrolled_window = Gtk.ScrolledWindow()
        self.image_box = Gtk.FlowBox()
        self.scrolled_window.add(self.image_box)
        self.pack_start(self.scrolled_window, True, True, 5)

        # add buttons to save all or clear all images
        self.save_all_button = Gtk.Button(label='Save all images')
        self.save_all_button.connect('clicked', self.save_all)
        self.pack_start(self.save_all_button, False, True, 5)
        self.clear_button = Gtk.Button(label='Clear images')
        self.clear_button.connect('clicked', self.clear_images)
        self.pack_start(self.clear_button, False, True, 5)

    def add_image(self, image):
        image_widget = SaveableImage(image, window=self.window)
        image_widget.set_visible(True)
        self.image_box.add(image_widget)

    def clear_images(self, _source):
        image_widgets = self.image_box.get_children()
        for widget in image_widgets:
            self.image_box.remove(widget)
            del(widget)

    def save_all(self, _source):
        # configure file chooser for destination directory
        file_chooser = Gtk.FileChooserDialog(title='Please choose a destination',
                                             action=Gtk.FileChooserAction.SELECT_FOLDER,
                                             transient_for=self.window)
        file_chooser.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                 Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        file_chooser.set_current_folder(SaveableImage.save_path)

        # show file chooser
        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            # update save_path for repeated use
            SaveableImage.save_path = file_chooser.get_filename()

            # loop over images and save them under respective name
            image_widgets = self.image_box.get_children()
            for i, image_widget in enumerate(image_widgets):
                path = os.path.join(SaveableImage.save_path, f"sdiff-gtk-{i}.png")
                image_widget.get_child().save_as(path)
        file_chooser.destroy()


class SaveableImage(Gtk.EventBox):
    save_path = '.'

    def __init__(self, image, window=None):
        super().__init__()
        self.image = image
        self.window = window

        # create Gtk Image widget from raw image
        pixbuf = img_to_pixbuf(image)
        self.image_widget = Gtk.Image(pixbuf=pixbuf)
        self.image_widget.set_visible(True)
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
        # configure file chooser to select output file
        file_chooser = Gtk.FileChooserDialog(title='Please choose a destination',
                                             action=Gtk.FileChooserAction.SAVE,
                                             transient_for=self.window)
        png_filter = Gtk.FileFilter()
        png_filter.set_name('PNG Image')
        png_filter.add_mime_type('image/png')
        file_chooser.add_filter(png_filter)
        file_chooser.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                 Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        file_chooser.set_current_name('sdiff.png')
        file_chooser.set_current_folder(SaveableImage.save_path)

        # run file chooser and save file on success
        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = file_chooser.get_filename()
            SaveableImage.save_path = file_chooser.get_current_folder()
            self.save_as(filename)
        file_chooser.destroy()

    def save_as(self, filename):
        # save file under given name and append file ending if necessary
        if not (filename.endswith('.png') or filename.endswith('.PNG')):
            filename += '.png'
        print('Saving image to', filename)
        self.image.save(filename)


class TextPromptFrame(Gtk.Frame):
    def __init__(self):
        super().__init__()
        # configure frame
        self.set_label('Prompt')
        self.set_margin_end(5)
        self.set_margin_start(5)

        # create actual input field
        self.prompt_field = Gtk.Entry()
        self.add(self.prompt_field)

    def get_prompt(self):
        return self.prompt_field.get_buffer().get_text()


def img_to_pixbuf(img):
    data = GLib.Bytes(img.tobytes())
    width, height = img.size
    return GdkPixbuf.Pixbuf.new_from_bytes(data, GdkPixbuf.Colorspace.RGB,
                                           False, 8, width, height, width * 3)

