import logging
import re
import time
from typing import Tuple, List, Union, Callable

import pkg_resources
import requests
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

logger = logging.getLogger(__name__)


def _get_easy():
    auth_browser_success_msg = "Autentimine õnnestus! Võid nüüd selle lehe sulgeda."
    auth_browser_fail_msg = "Midagi läks ootamatult valesti. Palun proovi uuesti."

    if PRODUCTION:
        return Ez("ems.lahendus.ut.ee",
                  'idp.lahendus.ut.ee',
                  "lahendus.ut.ee",
                  auth_browser_success_msg=auth_browser_success_msg,
                  auth_browser_fail_msg=auth_browser_fail_msg)
    else:
        return Ez("dev.ems.lahendus.ut.ee",
                  'dev.idp.lahendus.ut.ee',
                  "dev.lahendus.ut.ee",
                  auth_browser_success_msg=auth_browser_success_msg,
                  auth_browser_fail_msg=auth_browser_fail_msg)


# noinspection DuplicatedCode
class EasyExerciseProvider(ExerciseProvider):
    def __init__(self, exercises_view):
        self.exercises_view = exercises_view
        self.easy = _get_easy()
        self.last_update_check = None

    def get_html_and_breadcrumbs(self, url: str, form_data: FormData) -> Tuple[str, List[Tuple[str, str]]]:
        logger.info(f"User query: '{url}'. Form data: '{form_data}'.")
        try:
            if self._update_required():
                logger.info(f"Plug-in update required from user: {self._get_versions()}")
                return generate_update_html(self._get_versions()), HOME

            if url == AUTH_PATH:
                if self.easy.is_auth_required():
                    self._authenticate()

                    if self.easy.is_auth_required():
                        logger.info('Authentication failed!')
                        return generate_error_auth(), HOME
                    else:
                        logger.info('Authenticated! Checking in...')
                        self.easy.check_in()

                url = ROOT_PATH if form_data.get("from") is None else form_data.get("from")

            if EXERCISE_LIST_RE.fullmatch(url):
                self.log_match("EXERCISE_LIST", url, form_data)
                return self._show_exercise_list(EXERCISE_LIST_RE.fullmatch(url))

            elif EXERCISE_DESCRIPTION_RE.fullmatch(url):
                self.log_match("EXERCISE_DESCRIPTION", url, form_data)
                return self._show_exercise_description(EXERCISE_DESCRIPTION_RE.fullmatch(url))

            elif COURSE_LIST_RE.fullmatch(url) or url == ROOT_PATH:
                self.log_match("COURSE_LIST", url, form_data)
                return self._show_course_list()

            elif SUBMIT_SOLUTION_RE.fullmatch(url):
                self.log_match("SUBMIT_SOLUTION", url, form_data)
                return self._handle_submit_solution(form_data, SUBMIT_SOLUTION_RE.fullmatch(url))

            elif url == LOGOUT_PATH:
                self.log_match("LOGOUT_PATH", url, form_data)
                self._logout()
                return "<p>Nägemist!</p>", HOME
            else:
                self.log_match("COURSE_LIST", url, form_data)
                return self._show_course_list()

        except AuthRequiredException:
            self.log_match("AuthRequiredException", url, form_data)

            # Allow only one instance of the auth server in all cases.
            if self.easy.is_auth_in_progress(0):
                logger.info("Auth server is already running. Closing auth server down.")
                self.easy.shutdown()
                logger.info("Returning auth error page.")
                return generate_error_auth(), HOME

            logger.info("Auth required, returning auth page.")
            return generate_login_html(url), HOME

        except Exception as e:
            self.log_match("Exception", url, form_data)
            logger.warning(f"Unexpected error: '{e}'")
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

    @staticmethod
    def _get_versions():
        logger.info("Getting the installed plugin-in version info via pkg_resources...")
        installed_version = pkg_resources.require("thonny-lahendus")[0].version

        logger.info("Getting the latest plugin-in version info via pypi...")
        resp: requests.Response = requests.get("https://pypi.org/pypi/thonny-lahendus/json")
        latest_version = resp.json()["info"]["version"]

        versions = {"current": installed_version, "latest": latest_version}
        logger.info(f"Plug-in version info: {versions}")
        return versions

    def _update_required(self):
        def minutes_passed(oldepoch, minutes: int):
            if oldepoch is None:
                return True
            return time.time() - oldepoch >= 60 * minutes

        check_every = 10
        check_required = minutes_passed(self.last_update_check, check_every)

        if not check_required:
            logger.info(f"Skipping plug-in update check as {check_every} minutes are not passed from the last check.")
            return False

        logger.info("Checking for plug-in update...")
        versions = self._get_versions()
        major_installed, minor_installed, patch_installed = tuple(map(int, versions["current"].split(".")))
        major_latest, minor_latest, patch_latest = tuple(map(int, versions["latest"].split(".")))

        update_required = major_installed < major_latest
        if not update_required:
            logger.info(f"Version '{major_installed}' < '{major_latest}' is {update_required}, no update required.")
        else:
            logger.info(f"Version '{major_installed}' < '{major_latest}' is {update_required}, update required.")

        self.last_update_check = time.time()

        return update_required

    @staticmethod
    def log_match(matched_action: str, url: str, form_data: FormData):
        logger.info(f"User query: '{url}'. Form data: '{form_data}'. ---> {matched_action}")
