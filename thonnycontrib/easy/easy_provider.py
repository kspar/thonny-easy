import logging
import re
from typing import Tuple, List, Union, Callable

from easy import Ez, AuthRequiredException

from .templates_generator import *
from .ui import ExerciseProvider, FormData, EDITOR_CONTENT_NAME

AUTH_TIMEOUT_SECONDS = 300
ROOT_PATH = "/"
HOME = [(ROOT_PATH, "Lahendus")]
LOGOUT_PATH = "/logout"
AUTH_PATH = "/auth"

EXERCISE_LIST_RE = re.compile(r"^/student/courses/([0-9]+)/exercises/$")
EXERCISE_DESCRIPTION_RE = re.compile(r"^/student/courses/([0-9]+)/exercises/([0-9]+)$")
COURSE_LIST_RE = re.compile(r"^/student/courses$")
SUBMIT_SOLUTION_RE = re.compile(r"^/student/courses/([0-9]+)/exercises/([0-9]+)/submissions$")

PRODUCTION = True


def _get_easy():
    if PRODUCTION:
        return Ez("ems.lahendus.ut.ee", 'idp.lahendus.ut.ee', "lahendus.ut.ee")
    else:
        return Ez("dev.ems.lahendus.ut.ee", 'dev.idp.lahendus.ut.ee', "dev.lahendus.ut.ee")


# noinspection DuplicatedCode
class EasyExerciseProvider(ExerciseProvider):
    def __init__(self, exercises_view):
        self.exercises_view = exercises_view
        self.easy = _get_easy()
        logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s : %(message)s', level=logging.DEBUG)

    def get_html_and_breadcrumbs(self, url: str, form_data: FormData) -> Tuple[str, List[Tuple[str, str]]]:
        try:
            if url == AUTH_PATH:
                if self.easy.is_auth_required():
                    self._authenticate()

                    if self.easy.is_auth_required():
                        return generate_error_auth(), HOME
                    else:
                        logging.info('Authenticated! Checking in...')
                        self.easy.check_in()

                url = ROOT_PATH if form_data.get("from") is None else form_data.get("from")

            if EXERCISE_LIST_RE.fullmatch(url):
                return self._show_exercise_list(EXERCISE_LIST_RE.fullmatch(url))

            elif EXERCISE_DESCRIPTION_RE.fullmatch(url):
                return self._show_exercise_description(EXERCISE_DESCRIPTION_RE.fullmatch(url))

            elif COURSE_LIST_RE.fullmatch(url) or url == ROOT_PATH:
                return self._show_course_list()

            elif SUBMIT_SOLUTION_RE.fullmatch(url):
                return self._handle_submit_solution(form_data, SUBMIT_SOLUTION_RE.fullmatch(url))

            elif url == LOGOUT_PATH:
                self._logout()
                return "<p>Nägemist!</p>", HOME
            else:
                return self._show_course_list()

        except AuthRequiredException:
            # Allow only one instance of the auth server in all cases.
            if self.easy.is_auth_in_progress(0):
                self.easy.shutdown()
                return generate_error_auth(), HOME

            return generate_login_html(url), HOME

        except Exception as e:
            return generate_error_html(e), [self._breadcrumb_courses()]

    def _logout(self):
        self.easy.logout_in_browser()
        self.easy.shutdown()
        self.easy = _get_easy()

    def _authenticate(self):
        self.easy.start_auth_in_browser()
        self.easy.is_auth_in_progress(AUTH_TIMEOUT_SECONDS)

    def _handle_submit_solution(self, form_data, match):
        course_id, ex_id = match.group(1), match.group(2)
        return self._submit_solution(course_id, ex_id, form_data)

    def _show_course_list(self):
        courses = self.easy.student.get_courses().courses
        return generate_course_list_html(courses), [self._breadcrumb_courses()]

    def _show_exercise_description(self, match):
        course_id, ex_id = match.group(1), match.group(2)
        return self._get_ex_description(course_id, ex_id)

    def _show_exercise_list(self, match):
        course_id = match.group(1)
        return self._get_ex_list(course_id)

    def _get_course_list(self):
        return generate_course_list_html(self.easy.student.get_courses().courses), [self._breadcrumb_courses()]

    def _get_ex_list(self, course_id: str):
        exercises = self.easy.student.get_course_exercises(course_id).exercises
        breadcrumb_ex_list = self._breadcrumb_exercises(course_id)
        html = generate_exercise_list_html(breadcrumb_ex_list[0], exercises)
        return html, [self._breadcrumb_courses(), breadcrumb_ex_list]

    def _get_ex_description(self, course_id: str, exercise_id: str):
        details = self.easy.student.get_exercise_details(course_id, exercise_id)
        breadcrumb_this = (f"/student/courses/{course_id}/exercises/{exercise_id}", details.effective_title)
        breadcrumbs = [self._breadcrumb_courses(), self._breadcrumb_exercises(course_id), breadcrumb_this]
        return generate_exercise_html(self, course_id, exercise_id), breadcrumbs

    def _submit_solution(self, course_id: str, exercise_id: str, form_data):
        self.easy.student.post_submission(course_id, exercise_id, form_data.get(EDITOR_CONTENT_NAME))
        return self._get_ex_description(course_id, exercise_id)

    def _breadcrumb_exercises(self, course_id: str) -> Tuple[str, str]:
        return f"/student/courses/{course_id}/exercises/", self.easy.common.get_course_basic_info(course_id).title

    @staticmethod
    def _breadcrumb_courses() -> Tuple[str, str]:
        return f"/student/courses/", "Kursused"

    def get_menu_items(self) -> List[Tuple[str, Union[str, Callable, None]]]:
        return [("Logi sisse", AUTH_PATH) if self.easy.is_auth_required() else ("Logi välja", LOGOUT_PATH)]
