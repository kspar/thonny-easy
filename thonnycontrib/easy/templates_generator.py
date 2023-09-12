import json
import os
from typing import Dict

import chevron
from easy import SubmissionResp

from thonnycontrib.easy.ui import EDITOR_CONTENT_NAME


def render(template_name: str, data: Dict) -> str:
    res_path = os.path.join(os.path.dirname(__file__), "templates", template_name)

    with open(res_path, mode="r", encoding="UTF-8") as f:
        return chevron.render(f, data)


def generate_update_html(versions, lang="et"):
    return render("update_et.mustache"  if lang == "et" else "update_en.mustache", versions)

def generate_exercise_list_html(base_url, exercises, lang="et"):
    ex_list = [f'<li><a href="{base_url}{e["id"]}">{e["effective_title"]}</a></li>' for e in exercises]
    if len(ex_list) == 0:
        if lang == "et":
            return "<div>Siia kursusele ei ole veel ülesandeid lisatud.</div>"
        else:
            return "<div>No assignments have been added to this course yet.</div>"
    else:
        return f"<ul>{''.join(ex_list)}</ul>"


def generate_course_list_html(courses, lang="et"):
    course_lst = [
        f'<li><a href="/student/courses/{c["id"]}/exercises/">{c["title"] if c.get("alias", None) is None else c["alias"]}</a></li>'
        for c in courses]
    if len(course_lst) == 0:
        if lang == "et":
            return "<div>Sind ei ole veel ühelegi kursusele lisatud.</div>"
        else:
            return "<div>You have not been added to any courses yet.</div>"
    else:
        return f"<ul>{''.join(course_lst)}</ul>"


def generate_role_not_allowed_html(lang="et"):
    if lang == "et":
        return "<div>Sul puudub õpilase roll, mis on vajalik plugina kasutamiseks.</div>"
    else:
        return "<div>You lack the student role required for using the plugin.</div>"


def generate_login_html(from_url, lang="et") -> str:
    return render("authenticate.mustache",
                  {"from_url": "/" if from_url is None else from_url,
                   "button": "Ava sisse logimiseks veebilehitseja" if lang == "et" else "Open a web browser to log in" })


def generate_error_html(error_msg, lang="et") -> str:
    if lang == "et":
        return f"<h1>Viga!</h1><div>{error_msg}</div>"
    else:
        return f"<h1>Error!</h1><div>{error_msg}</div>"


def generate_error_auth(lang="et") -> str:
    if lang == "et":
        return f"""<h1>Autentimine ebaõnnestus!</h1><a href="/auth">Alusta autentimist uuesti</a>"""
    else:
        return f"""<h1>Authentication Failed!</h1><a href='/auth'>Start authentication again</a>"""


def _convert_to_str(value):
    if value is None:
        return value
    else:
        return str(value)


def _status(status):
    return status.replace('FAIL', '❌').replace('PASS', '✔')


def _process_test(test, locale_dict):
    try:
        title, status = test['title'], _status(test['status'])
        user_inputs, actual_output = test['user_inputs'], test['actual_output']

        checks = [f"{(_status(check['status']))}: {check['feedback']}" for check in test["checks"]]
        checks = "\n  ".join(checks)

        if len(user_inputs) == 0:
            user_inputs = ""
        else:
            user_inputs = "\n    ".join(user_inputs)
            user_inputs = f"  {locale_dict['GAVE_INPUTS']}: \n    {user_inputs}\n"

        if actual_output is None or len(actual_output) == 0:
            actual_output = ""
        else:
            formatted = "\n    ".join(actual_output.split("\n"))
            actual_output = f"  {locale_dict['OUTPUT_WAS']}:\n    {formatted}\n"

        if test['exception_message'] is None:
            exception = ''
        else:
            msg = "    " + test['exception_message'].replace("\n","\n    ")
            exception = f"  {locale_dict['EXCEPTION']}:\n\n{msg}\n"


        if test['created_files'] is None or len(test['created_files']) == 0:
            created_files = ""
        else:
            files = [(x['name'], x['content']) for x in test['created_files']]
            files = ["    ---" + name + "---\n" + content for (name, content) in files]
            files = [content.replace("\n","\n    ") for content in files]
            files = "  \n\n".join(files)
            created_files = f"  {locale_dict['CREATED_FILES']}:\n\n{files}\n\n"

        result = (
            f"{status}: {title}\n"
            f"  {checks}\n"
            f"{exception}"
            f"{user_inputs}"
            f"{created_files}"
            f"{actual_output}"
        )
    except KeyError:
        result = str(test)

    return result


def generate_exercise_html(provider, course_id, exercise_id, lang="et") -> str:
    strings_en = {"CLOSED_DENIED_INFO": "This exercise is closed and does not allow any new submissions",
                  "POINTS_TITLE": "Points",
                  "SUBMITTING_TITLE": "Submit",
                  "SUBMIT_ACTIVE": "Submit the contents of the active editor",
                  "TEACHER_COMMENT": "Teacher feedback",
                  "AUTOMATIC_TESTS": "Automated tests",
                  "LAST_SUBMISSION": "Latest submission",
                  "SEE_IN_LAHENDUS": "See the task in Lahendus",
                  "GAVE_INPUTS": "Inputs provided to the program",
                  "OUTPUT_WAS": "The program's full output",
                  "EXCEPTION": "There was an exception during the program's execution",
                  "CREATED_FILES" : "Before running the program, the following files were created"
                  }

    strings_et = {"CLOSED_DENIED_INFO": "See ülesanne on suletud ja ei luba enam uusi esitusi",
                  "SUBMITTING_TITLE": "Esitamine",
                  "POINTS_TITLE": "Punktid",
                  "SUBMIT_ACTIVE": "Esita aktiivse redaktori sisu",
                  "TEACHER_COMMENT": "Õpetaja kommentaar",
                  "AUTOMATIC_TESTS": "Automaatsed testid",
                  "LAST_SUBMISSION": "Viimane esitus",
                  "SEE_IN_LAHENDUS": "Vaata ülesannet Lahenduses",
                  "GAVE_INPUTS": "Andsin programmile sisendid",
                  "OUTPUT_WAS": "Programmi täielik väljund oli",
                  "EXCEPTION": "Programmi käivitamisel tekkis viga",
                  "CREATED_FILES":"Enne programmi käivitamist lõin failid"
                  }

    strings = strings_et if lang == "et" else strings_en

    def has_submissions() -> bool:
        return len(provider.easy.student.get_all_submissions(course_id, exercise_id).submissions) > 0

    if has_submissions():
        latest = provider.easy.student.get_latest_exercise_submission_details(course_id, exercise_id)
    else:
        latest = SubmissionResp()

    try:
        js = json.loads(latest.feedback_auto)
        if "result_type" in js:
            result_type = js["result_type"]

            if result_type == "OK_V3":
                if js["pre_evaluate_error"] is None:
                    test_results = [_process_test(test, strings) for test in js["tests"]]
                    feedback_auto = '\n'.join(test_results)
                    grade_auto = _convert_to_str(js["points"])
                else:
                    feedback_auto = js["pre_evaluate_error"]
                    grade_auto = _convert_to_str(js["points"])

            elif result_type == "OK_LEGACY":
                feedback_auto = js["feedback"]
                grade_auto = _convert_to_str(js["points"])

            elif result_type == "ERROR_V3":
                feedback_auto = js["error"]
                grade_auto = "-"
        else:
            feedback_auto = latest.feedback_auto
            grade_auto = _convert_to_str(latest.grade_auto)
    except (ValueError, KeyError, TypeError):
        feedback_auto = latest.feedback_auto
        grade_auto = _convert_to_str(latest.grade_auto)

    if _convert_to_str(latest.grade_teacher) is None:
        points, feedback_type = (grade_auto, "")
    else:
        points, feedback_type = (_convert_to_str(latest.grade_teacher), "🙎")

    details = provider.easy.student.get_exercise_details(course_id, exercise_id)
    return render("exercise.mustache", {"effective_title": details.effective_title,
                                        "text_html": details.text_html,
                                        "is_open": details.is_open,
                                        "not_open": not details.is_open,
                                        "points": points,
                                        "feedback_type": feedback_type,
                                        "feedback_auto": feedback_auto,
                                        "solution": latest.solution,
                                        "EDITOR_CONTENT_NAME": EDITOR_CONTENT_NAME,
                                        "course_id": course_id,
                                        "exercise_id": exercise_id,
                                        "latest_feedback_teacher": latest.feedback_teacher,
                                        "latest_grade_teacher": _convert_to_str(latest.grade_teacher),
                                        "provider_url": provider.easy.util.idp_client_name} | strings)
