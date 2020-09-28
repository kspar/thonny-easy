import logging
import re
from typing import Tuple, List

from easy.exceptions import ErrorResponseException
from easy.ez import Ez, AuthRequiredException

from thonny import get_workbench
from thonny.exercises import ExerciseProvider, FormData, EDITOR_CONTENT_NAME


class DemoExerciseProvider(ExerciseProvider):
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
                return self._get_ex_text(course_id, ex_id)

            elif bool(re.match(r"^/student/courses$", url)) or url == "/":
                return self._get_course_list()

            elif bool(re.match(r"^/student/courses/[0-9]+/exercises/[0-9]+/submissions$", url)):
                course_id = url.replace("/student/courses/", "").split("/exercises/")[0]
                ex_id = url.split("/exercises/")[1].replace("/submissions", "")
                return self._get_submit_text(course_id, ex_id, form_data)

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
        format_c = [f'<li><a href="/student/courses/{c["id"]}/exercises/">{c["title"]}</a></li>' for c in courses]
        return f"<ul>{''.join(format_c)}</ul>", [("/", "")]

    def _get_ex_list(self, course_id: str) -> Tuple[str, List[Tuple[str, str]]]:
        self._auth()
        exercises = self.easy.student.get_course_exercises(course_id).exercises
        format_e = [f'<li><a href="/student/courses/{course_id}/exercises/{e["id"]}">{e["effective_title"]}</a></li>'
                    for e in exercises]
        return f"<ul>{''.join(format_e)}</ul>", [(f"/student/courses/", "Kursused")]

    def _get_ex_text(self, course_id: str, exercise_id: str) -> Tuple[str, List[Tuple[str, str]]]:
        self._auth()
        details = self.easy.student.get_exercise_details(course_id, exercise_id)
        html = details.text_html
        all_submissions = self.easy.student.get_all_submissions(course_id, exercise_id)

        has_submissions = len(all_submissions.submissions) > 0
        last_submission_times = ''.join([f"<li>{s['submission_time']}</li>" for s in all_submissions.submissions])
        previous_html = f"""
    
            {f"<h1>Viimane esitus</h1>" if has_submissions else "Esitusi ei ole"}            
            {f"<code>{all_submissions.submissions[0]['solution']}</code>" if has_submissions else ""}

            {f"<h2>Eelmised esitused ({all_submissions.count})</h2>" if has_submissions else ""}
            {f"<ul>{last_submission_times}</ul>" if has_submissions else ""}
        """

        submit_html = f"""
            <form action="/student/courses/{course_id}/exercises/{exercise_id}/submissions">
                <input type="hidden" name="{EDITOR_CONTENT_NAME}" />
                <input type="submit" value="Esita aktiivse redaktori sisu" />
            </form>       
        """

        return html + previous_html + submit_html, [(f"/student/courses/{course_id}/exercises/", "Ülesanded")]

    def _get_submit_text(self, course_id: str, exercise_id: str, form_data) -> Tuple[str, List[Tuple[str, str]]]:
        source = form_data.get(EDITOR_CONTENT_NAME)
        self.easy.student.post_submission(course_id, exercise_id, source)
        all_submissions = self.easy.student.get_all_submissions(course_id, exercise_id)

        return f"""
            <h1>Esitus</h1>
            <code>
                {source}
            </code>
            <h2>Tulemus</h2>
    
            Priima töö!
            
            <h2>Eelmised esitused ({all_submissions.count})</h2>
            <ul>
                {''.join([f"<li>{s['submission_time']}</li>" for s in all_submissions.submissions])}            
            </ul>
            """, [(f"/student/courses/{course_id}/exercises/{exercise_id}", "Ülesande kirjeldus")]


def load_plugin():
    get_workbench().add_exercise_provider("demo", "Lahendus", DemoExerciseProvider)
