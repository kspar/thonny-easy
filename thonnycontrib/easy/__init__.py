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
    import os.path
    formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s")
    log_file = os.path.join(THONNY_USER_DIR, "lahendus.log")
    file_handler = logging.FileHandler(log_file, encoding="UTF-8", mode="a")
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # get_workbench().add_view(DemoExercisesView, "DemoEx", "ne")
    get_workbench().add_view(EasyExercisesView, "Lahendus", "ne")
