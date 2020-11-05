import logging
import re
from typing import Tuple, List

from easy import Ez, AuthRequiredException

from .templates import *
from .templates import generate_course_list_html
from .ui import ExerciseProvider, FormData, EDITOR_CONTENT_NAME

HOME_LINK = ("/", "Lahendus")


class EasyExerciseProvider(ExerciseProvider):
    def __init__(self, exercises_view):
        self.exercises_view = exercises_view
        self.easy = Ez("ems.lahendus.ut.ee", 'idp.lahendus.ut.ee', "lahendus.ut.ee")
        logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s : %(message)s', level=logging.DEBUG)

    def get_html_and_breadcrumbs(self, url: str, form_data: FormData) -> Tuple[str, List[Tuple[str, str]]]:
        try:
            if bool(re.match(r"^/student/courses/[0-9]+/exercises/$", url)):
                return self.show_exercise_list(url)

            elif bool(re.match(r"^/student/courses/[0-9]+/exercises/[0-9]+$", url)):
                return self.show_exercise_description(url)

            elif bool(re.match(r"^/student/courses$", url)) or url == "/":
                return self.show_course_list()

            elif bool(re.match(r"^/student/courses/[0-9]+/exercises/[0-9]+/submissions$", url)):
                return self.handle_submit_solution(form_data, url)

            elif url == "/auth":
                return self.handle_auth(form_data)

            else:
                return self.show_course_list()

        except AuthRequiredException:
            return generate_login_html(url), [HOME_LINK]

        except Exception as e:
            return generate_error_html(e), [HOME_LINK]

    def handle_auth(self, form_data):
        form_url = form_data.get("from")
        next_url = "/" if form_url is None else form_url
        if self.easy.is_auth_required():
            logging.info('Authentication required')
            self.easy.start_auth_in_browser()
            logging.info('Authentication started')
            while self.easy.is_auth_in_progress(10):
                logging.info('Authentication still not done...')

            if self.easy.is_auth_required():
                logging.info('Authentication failed!')
            else:
                logging.info('Authenticated!')

        return self.get_html_and_breadcrumbs(next_url, form_data)

    def handle_submit_solution(self, form_data, url):
        course_id = url.replace("/student/courses/", "").split("/exercises/")[0]
        ex_id = url.split("/exercises/")[1].replace("/submissions", "")
        return self._submit_solution(course_id, ex_id, form_data)

    def show_course_list(self):
        courses = self.easy.student.get_courses().courses
        result = generate_course_list_html(courses), [HOME_LINK, self._breadcrumb_courses()]
        return result

    def show_exercise_description(self, url):
        course_id = url.replace("/student/courses/", "").split("/exercises/")[0]
        ex_id = url.split("/exercises/")[1]
        return self._get_ex_description(course_id, ex_id)

    def show_exercise_list(self, url):
        course_id = url.replace("/student/courses/", "").replace("/exercises/", "")
        return self._get_ex_list(course_id)

    def _get_course_list(self) -> Tuple[str, List[Tuple[str, str]]]:
        courses = self.easy.student.get_courses().courses
        return generate_course_list_html(courses), [HOME_LINK, self._breadcrumb_courses()]

    def _get_ex_list(self, course_id: str) -> Tuple[str, List[Tuple[str, str]]]:
        exercises = self.easy.student.get_course_exercises(course_id).exercises
        breadcrumb_ex_list = self._breadcrumb_exercises(course_id)
        html = generate_exercise_list_html(breadcrumb_ex_list[0], exercises)

        return html, [HOME_LINK, self._breadcrumb_courses(), breadcrumb_ex_list]

    def _get_ex_description(self, course_id: str, exercise_id: str) -> Tuple[str, List[Tuple[str, str]]]:
        details = self.easy.student.get_exercise_details(course_id, exercise_id)
        last_submission_html = generate_latest_submissions_html(self, course_id, exercise_id)
        submit_html = generate_submit_html(course_id, exercise_id)

        breadcrumb_this = (f"/student/courses/{course_id}/exercises/{exercise_id}", details.effective_title)
        breadcrumbs = [HOME_LINK, self._breadcrumb_courses(), self._breadcrumb_exercises(course_id), breadcrumb_this]

        return f"<h1>{details.effective_title}</h1>{details.text_html}{last_submission_html}{submit_html}", breadcrumbs

    def _submit_solution(self, course_id: str, exercise_id: str, form_data) -> Tuple[str, List[Tuple[str, str]]]:
        self.easy.student.post_submission(course_id, exercise_id, form_data.get(EDITOR_CONTENT_NAME))
        return self._get_ex_description(course_id, exercise_id)

    def _breadcrumb_exercises(self, course_id: str) -> Tuple[str, str]:
        def get_course_name() -> str:
            return [c for c in self.easy.student.get_courses().courses if c["id"] == course_id][0]["title"]

        return f"/student/courses/{course_id}/exercises/", get_course_name()

    @staticmethod
    def _breadcrumb_courses() -> Tuple[str, str]:
        return f"/student/courses/", "Kursused"
