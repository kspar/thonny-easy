import logging
import re
from typing import Tuple, List, Union, Callable

from easy import Ez, AuthRequiredException

from .templates_generator import *
from .ui import ExerciseProvider, FormData, EDITOR_CONTENT_NAME

AUTH_ALLOWED_RETRIES = 6
AUTH_TIMEOUT_SECONDS = 10
ROOT_PATH = "/"
HOME = [(ROOT_PATH, "Lahendus")]
LOGOUT_PATH = "/logout"
AUTH_PATH = "/auth"

EXERCISE_LIST_RE = re.compile(r"^/student/courses/[0-9]+/exercises/$")
EXERCISE_DESCRIPTION_RE = re.compile(r"^/student/courses/[0-9]+/exercises/[0-9]+$")
COURSE_LIST_RE = re.compile(r"^/student/courses$")
SUBMIT_SOLUTION_RE = re.compile(r"^/student/courses/[0-9]+/exercises/[0-9]+/submissions$")

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
                    self.easy.start_auth_in_browser()

                    retries = 0
                    while self.easy.is_auth_in_progress(AUTH_TIMEOUT_SECONDS):
                        retries += 1
                        logging.info(f'Authentication still not done... Attempt {retries}/{AUTH_ALLOWED_RETRIES}.')
                        if retries == AUTH_ALLOWED_RETRIES:
                            self.easy.shutdown()

                    if self.easy.is_auth_required():
                        return generate_error_auth(), HOME
                    else:
                        logging.info('Authenticated! Checking in...')
                        self.easy.check_in()

                form_url = form_data.get("from")
                url = ROOT_PATH if form_url is None else form_url

            if EXERCISE_LIST_RE.match(url):
                return self.show_exercise_list(url)

            elif EXERCISE_DESCRIPTION_RE.match(url):
                return self.show_exercise_description(url)

            elif COURSE_LIST_RE.match(url) or url == ROOT_PATH:
                return self.show_course_list()

            elif SUBMIT_SOLUTION_RE.match(url):
                return self.handle_submit_solution(form_data, url)

            elif url == LOGOUT_PATH:
                self.easy.logout_in_browser()
                self.easy.shutdown()
                self.easy = _get_easy()
                return "<p>Nägemist!</p>", HOME
            else:
                return self.show_course_list()

        except AuthRequiredException:
            # Allow only one instance of the auth server in all cases.
            if self.easy.is_auth_in_progress(0):
                self.easy.shutdown()
                return generate_error_auth(), HOME

            return generate_login_html(url), HOME

        except Exception as e:
            return generate_error_html(e), [self._breadcrumb_courses()]

    def handle_submit_solution(self, form_data, url):
        course_id = url.replace("/student/courses/", "").split("/exercises/")[0]
        ex_id = url.split("/exercises/")[1].replace("/submissions", "")
        return self._submit_solution(course_id, ex_id, form_data)

    def show_course_list(self):
        courses = self.easy.student.get_courses().courses
        result = generate_course_list_html(courses), [self._breadcrumb_courses()]
        return result

    def show_exercise_description(self, url):
        course_id = url.replace("/student/courses/", "").split("/exercises/")[0]
        ex_id = url.split("/exercises/")[1]
        return self._get_ex_description(course_id, ex_id)

    def show_exercise_list(self, url):
        course_id = url.replace("/student/courses/", "").replace("/exercises/", "")
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
        def get_course_name() -> str:
            return [c for c in self.easy.student.get_courses().courses if c["id"] == course_id][0]["title"]

        return f"/student/courses/{course_id}/exercises/", get_course_name()

    @staticmethod
    def _breadcrumb_courses() -> Tuple[str, str]:
        return f"/student/courses/", "Kursused"

    def get_menu_items(self) -> List[Tuple[str, Union[str, Callable, None]]]:
        return [("Logi sisse", AUTH_PATH) if self.easy.is_auth_required() else ("Logi välja", LOGOUT_PATH)]
