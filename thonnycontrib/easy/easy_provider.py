import logging
import re
from typing import Tuple, List

from easy import ErrorResponseException
from easy import Ez, AuthRequiredException

from .ui import ExerciseProvider, FormData, EDITOR_CONTENT_NAME

HOME_LINK = ("/", "Home")


class EasyExerciseProvider(ExerciseProvider):
    def __init__(self, exercises_view):
        self.exercises_view = exercises_view
        self.easy = Ez("dev.ems.lahendus.ut.ee", 'dev.idp.lahendus.ut.ee', "dev.lahendus.ut.ee")
        logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s : %(message)s', level=logging.DEBUG)

    def get_html_and_breadcrumbs(self, url: str, form_data: FormData) -> Tuple[str, List[Tuple[str, str]]]:
        try:
            if bool(re.match(r"^/student/courses/[0-9]+/exercises/$", url)):
                course_id = url.replace("/student/courses/", "").replace("/exercises/", "")
                return self._get_ex_list(course_id)

            elif bool(re.match(r"^/student/courses/[0-9]+/exercises/[0-9]+$", url)):
                course_id = url.replace("/student/courses/", "").split("/exercises/")[0]
                ex_id = url.split("/exercises/")[1]
                return self._get_ex_description(course_id, ex_id)

            elif bool(re.match(r"^/student/courses$", url)) or url == "/":
                return self._get_course_list()

            elif bool(re.match(r"^/student/courses/[0-9]+/exercises/[0-9]+/submissions$", url)):
                course_id = url.replace("/student/courses/", "").split("/exercises/")[0]
                ex_id = url.split("/exercises/")[1].replace("/submissions", "")
                return self._submit_solution(course_id, ex_id, form_data)

            else:
                return self._get_course_list()

        except ErrorResponseException:
            return f"Päring Lahendusega ebaõnnestus!", []

        except AuthRequiredException:
            return f"Autentimine ebaõnnestus! Palun proovige uuesti!", []

        except KeyError:
            return "Lahenduse serveri vastuse lugemine ebaõnnestus! Kas kasutusel on kõige viimane Thonny versioon?", []

    def _auth(self):
        if self.easy.is_auth_required():
            logging.info('Authentication required')
            self.easy.start_auth_in_browser()
            logging.info('Authentication started')
            while self.easy.is_auth_in_progress(10):
                logging.info('Authentication still not done...')
                self.easy.start_auth_in_browser()

            logging.info('Authenticated!')

    def _get_course_list(self) -> Tuple[str, List[Tuple[str, str]]]:
        self._auth()
        courses = self.easy.student.get_courses().courses
        return self._generate_course_list_html(courses), [HOME_LINK, self._breadcrumb_courses()]

    def _get_ex_list(self, course_id: str) -> Tuple[str, List[Tuple[str, str]]]:
        self._auth()

        exercises = self.easy.student.get_course_exercises(course_id).exercises
        breadcrumb_ex_list = self._breadcrumb_exercises(course_id)
        html = self._generate_exercise_list_html(breadcrumb_ex_list[0], exercises)

        return html, [HOME_LINK, self._breadcrumb_courses(), breadcrumb_ex_list]

    def _get_ex_description(self, course_id: str, exercise_id: str) -> Tuple[str, List[Tuple[str, str]]]:
        self._auth()

        details = self.easy.student.get_exercise_details(course_id, exercise_id)
        last_submission_html = self._generate_latest_submissions_html(course_id, exercise_id)
        submit_html = self._generate_submit_html(course_id, exercise_id)

        breadcrumb_this = (f"/student/courses/{course_id}/exercises/{exercise_id}", details.effective_title)
        breadcrumbs = [HOME_LINK, self._breadcrumb_courses(), self._breadcrumb_exercises(course_id), breadcrumb_this]

        return f"<h1>{details.effective_title}</h1>{details.text_html}{last_submission_html}{submit_html}", breadcrumbs

    def _submit_solution(self, course_id: str, exercise_id: str, form_data) -> Tuple[str, List[Tuple[str, str]]]:
        self.easy.student.post_submission(course_id, exercise_id, form_data.get(EDITOR_CONTENT_NAME))
        return self._get_ex_description(course_id, exercise_id)

    def _get_course_name(self, course_id: str) -> str:
        return [c for c in self.easy.student.get_courses().courses if c["id"] == course_id][0]["title"]

    def _has_submissions(self, course_id: str, exercise_id: str) -> bool:
        return len(self.easy.student.get_all_submissions(course_id, exercise_id).submissions) > 0

    def _breadcrumb_exercises(self, course_id: str) -> Tuple[str, str]:
        return f"/student/courses/{course_id}/exercises/", self._get_course_name(course_id)

    def _breadcrumb_courses(self) -> Tuple[str, str]:
        return f"/student/courses/", "Kursused"

    def _generate_exercise_list_html(self, base_url, exercises):
        ex_list = [f'<li><a href="{base_url}{e["id"]}">{e["effective_title"]}</a></li>' for e in exercises]
        html = f"<ul>{''.join(ex_list)}</ul>"
        return html

    def _generate_course_list_html(self, courses):
        format_c = [f'<li><a href="/student/courses/{c["id"]}/exercises/">{c["title"]}</a></li>' for c in courses]
        html = f"<ul>{''.join(format_c)}</ul>"
        return html

    def _generate_submit_html(self, course_id, exercise_id) -> str:
        submit_html = f"""
             <form action="/student/courses/{course_id}/exercises/{exercise_id}/submissions">
                 <input type="hidden" name="{EDITOR_CONTENT_NAME}" />
                 <input type="submit" value="Esita aktiivse redaktori sisu" />
             </form>       
         """
        return submit_html

    def _generate_latest_submissions_html(self, course_id, exercise_id) -> str:
        if not self._has_submissions(course_id, exercise_id):
            return ""

        latest = self.easy.student.get_latest_exercise_submission_details(course_id, exercise_id)

        if latest.grade_teacher is None:
            teacher_feedback = ""
        else:
            teacher_feedback = f"""
            <h2>Õpetaja hinnang</h2>       

            <div>{latest.feedback_teacher} </div> 

            <div>Hinne: {latest.grade_teacher}/100</div> 
            """

        return f"""
                <h1>Esitamine</h1>
            
                <h2>Automaatne hinnang</h2>

                <div>Automaatne hinne: {latest.grade_auto}/100</div> 
                
                <div>
                    <code>
                    {latest.feedback_auto}
                    </code>
                </div> 

                <div>{teacher_feedback}</div> 

                <h2>Viimane esitus</h2>
                <div>
                    <code>
                    {latest.solution}
                    </code>
                </div> 
        """
