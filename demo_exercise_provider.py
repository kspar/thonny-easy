import re
from typing import Tuple, List

from easy import Ez, ExerciseDetailsResp, StudentAllSubmissionsResp

from thonny import get_workbench
from thonny.exercises import ExerciseProvider, FormData, EDITOR_CONTENT_NAME


class DemoExerciseProvider(ExerciseProvider):
    def __init__(self, exercises_view):
        self.exercises_view = exercises_view
        self.easy = Ez("dev.ems.lahendus.ut.ee", 'dev.idp.lahendus.ut.ee', "dev.lahendus.ut.ee")

    def get_html_and_breadcrumbs(self, url: str, form_data: FormData) -> Tuple[str, List[Tuple[str, str]]]:
        # TODO: expect id's to be numbers?
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

    def _auth(self):
        if self.easy.is_auth_required():
            print('auth is required')
            self.easy.start_auth_in_browser()
            print('auth started')
            while self.easy.is_auth_in_progress(10):
                print('Still not done')
                self.easy.start_auth_in_browser()

            print('Done!')
            print(self.easy.is_auth_required())

    def _get_course_list(self) -> Tuple[str, List[Tuple[str, str]]]:
        self._auth()
        # TODO: why data classes do not work (only sometimes?)?
        courses = self.easy.student.get_courses().courses
        format_c = [f'<li><a href="/student/courses/{c["id"]}/exercises/">{c["title"]}</a></li>' for c in courses]
        return f"<ul>{''.join(format_c)}</ul>", [("/student/courses", "Courses")]

    def _get_ex_list(self, course_id: str) -> Tuple[str, List[Tuple[str, str]]]:
        self._auth()
        exercises = self.easy.student.get_course_exercises(course_id).exercises
        course_name = [c["title"] for c in self.easy.student.get_courses().courses if c["id"] == course_id][0]
        format_e = [f'<li><a href="/student/courses/{course_id}/exercises/{e["id"]}">{e["effective_title"]}</a></li>'
                    for e in exercises]
        return f"<ul>{''.join(format_e)}</ul>", [(f"/student/courses/{course_id}/exercises/", course_name)]

    def _get_ex_text(self, course_id: str, exercise_id: str) -> Tuple[str, List[Tuple[str, str]]]:
        self._auth()
        details: ExerciseDetailsResp = self.easy.student.get_exercise_details(course_id, exercise_id)
        html = details.text_html
        title = details.effective_title

        submit_html = f""" 
            <form action="/student/courses/{course_id}/exercises/{exercise_id}/submissions">
                <input type="hidden" name="{EDITOR_CONTENT_NAME}" />
                <input type="submit" value="Esita aktiivse redaktori sisu" />
            </form>"""

        return html + submit_html, [(f"/student/courses/{course_id}/exercises/{exercise_id}", title)]

    def _get_submit_text(self, course_id: str, exercise_id: str, form_data) -> Tuple[str, List[Tuple[str, str]]]:
        source: str = form_data.get(EDITOR_CONTENT_NAME)
        resp_code: int = self.easy.student.post_submission(course_id, exercise_id, source)
        prev: StudentAllSubmissionsResp = self.easy.student.get_all_submissions(course_id, exercise_id)
        return f"""
        <h1>Esitus</h1>
        <code>
            {source}
        </code>
        <h2>Tulemus</h2>
        <h4>{resp_code}</h4>

        Priima töö!
        
        <h2>Eelmised esitused ({prev.count})</h2>
        <ul>
            {''.join([f"<li>{s['submission_time']}</li>" for s in prev.submissions])}            
        </ul>
        """, []


def load_plugin():
    get_workbench().add_exercise_provider("demo", "Lahendus", DemoExerciseProvider)
