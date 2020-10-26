from thonny import get_workbench

from thonnycontrib.easy.demo_exercise_provider import DemoExerciseProvider
from thonnycontrib.easy.easy_provider import EasyExerciseProvider
from thonnycontrib.easy.ui import ExercisesView


class EasyExercisesView(ExercisesView):
    def __init__(self, master):
        super(EasyExercisesView, self).__init__(master, EasyExerciseProvider)


class DemoExercisesView(ExercisesView):
    def __init__(self, master):
        super(DemoExercisesView, self).__init__(master, DemoExerciseProvider)


def load_plugin():
    # get_workbench().add_view(DemoExercisesView, "DemoEx", "ne")
    get_workbench().add_view(EasyExercisesView, "Easy", "ne")
