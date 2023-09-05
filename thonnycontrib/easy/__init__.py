from thonny import get_workbench, THONNY_USER_DIR

from thonnycontrib.easy.ui import ExercisesView


class EasyExercisesView(ExercisesView):
    def __init__(self, master):
        from thonnycontrib.easy.easy_provider import EasyExerciseProvider
        super(EasyExercisesView, self).__init__(master, EasyExerciseProvider)


class DemoExercisesView(ExercisesView):
    def __init__(self, master):
        from thonnycontrib.easy.demo_exercise_provider import DemoExerciseProvider
        super(DemoExercisesView, self).__init__(master, DemoExerciseProvider)


def load_plugin():
    import logging
    import platform
    import datetime
    import configparser
    import os

    path = os.path.join(THONNY_USER_DIR, "lahendus")
    os.makedirs(path, exist_ok=True)
    log_file = os.path.join(path, datetime.datetime.now().strftime("%Y-%m-%d") + ".lahendus.log")

    # config
    config = configparser.ConfigParser()
    config.set('DEFAULT', 'lang', "et")
    config_location = os.path.join(path, 'lahendus.ini')

    if not os.path.exists(config_location):
        with open(config_location, 'w') as configfile:
            config.write(configfile)

    file_handler = logging.FileHandler(log_file, encoding="UTF-8", mode="a")
    file_handler.setFormatter(logging.Formatter("%(asctime)s;%(levelname)s;%(message)s"))

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.info(f"Starting plug-in on '{platform.platform()}'")

    # get_workbench().add_view(DemoExercisesView, "DemoEx", "ne")
    get_workbench().add_view(EasyExercisesView, "Lahendus", "ne")
