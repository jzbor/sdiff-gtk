# sdiff-gtk
...is a GTK+ application for generating images with [Stable Diffusion](https://github.com/Stability-AI/stablediffusion).
It uses [diffusers](https://github.com/huggingface/diffusers) to do the actual inference and downloads the model from [huggingface](https://huggingface.co/) when first used.
Initial downloading might take a while, but the model will be cached for later use.

Sadly the current way of handling the model cache prevents you from using the application offline, even though the models are cached.
You can take a look at [this issue](https://github.com/huggingface/diffusers/issues/1717) on the diffusers repo.

## Running the application
I haven't gotten around to properly packaging the application yet, so for now your best option is to run it with poetry like so:
```
poetry install
poetry run python src/sdiff_gtk/__init__.py
```

Note that you might have to install `gobject-introspection` package on your system, as it is required to build the python package `gobject`.

### Arch Linux-based platforms
You can install this program from the AUR.
It is available as `sdiff-gtk`.
