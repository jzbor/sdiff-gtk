import array
import gi
import os.path
import torch
from PIL import Image
from diffusers import StableDiffusionPipeline
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from threading import Thread

from widgets import TextPromptFrame
from diffusionbox import DiffusionBox


MODEL='runwayml/stable-diffusion-v1-5'

T2T_MODELS = [
    'runwayml/stable-diffusion-v1-5',
    'stabilityai/stable-diffusion-2-base',
]


class ApplicationWindow(Gtk.Window):
    def __init__(self):
        super().__init__()

        prompt_frame = TextPromptFrame()
        self.diffusion_box = DiffusionBox(T2T_MODELS, prompt_frame)
        self.add(self.diffusion_box)

        self.set_default_size(800, 850)
        self.set_visible(True)
        self.connect('destroy', Gtk.main_quit)
        self.set_title('Stable Diffusion GTK');

if __name__ == '__main__':
    # gradient calculation is not required for inference and might slow things down
    # so we can disable it
    torch.no_grad()

    ApplicationWindow()
    Gtk.main()
