import threading
from diffusers import StableDiffusionPipeline
from threading import Thread


class DiffusionSettings:
    def __init__(self, model=None, device='cpu', low_mem=True, width=256, height=256, steps=50, nimages=1):
        self.model = model
        self.device = device
        self.low_mem = low_mem
        self.width = width
        self.height = height
        self.steps = steps
        self.nimages = nimages


class DiffusionJob:
    running_thread = None
    ui_states = []

    def __init__(self, prompt, settings, image_view, error_reporter):
        self.prompt = prompt
        self.settings = settings
        self.image_view = image_view
        self.error_reporter = error_reporter

    @classmethod
    def register_ui(cls, ui):
        cls.ui_states.append(ui)

    @classmethod
    def is_running(cls):
        return cls.running_thread != None

    @classmethod
    def report_state(cls, state):
        for ui in cls.ui_states:
            ui.show_diffusion_running(state)

    def run(self):
        # communicate running job to ui
        DiffusionJob.report_state(True)

        pipeline = None
        try:
            # create pipeline
            pipeline = StableDiffusionPipeline.from_pretrained(self.settings.model, low_cpu_mem_usage=self.settings.low_mem) \
                    .to(self.settings.device)

            # generate self.settings.nimages images from pipeline
            for i in range(0, self.settings.nimages):
                image = pipeline(self.prompt, num_inference_steps=self.settings.steps, width=self.settings.width, height=self.settings.height).images[0]
                self.image_view.add_image(image)
        except ValueError as e:
            self.error_reporter.show_error('Invalid parameters', str(e))
        except Exception as e:
            self.error_reporter.show_error('Unexpected error', str(e))
        finally:
            del(pipeline)

        if DiffusionJob.running_thread == threading.current_thread():
            self.running_thread = None
            DiffusionJob.report_state(False)

    def run_async(self):
        if DiffusionJob.is_running():
            self.error_reporter.show_error('Another job is already running')
            return
        else:
            DiffusionJob.running_thread = Thread(target=self.run)
            DiffusionJob.running_thread.start()


