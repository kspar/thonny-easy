import os
from typing import Dict

import chevron
from easy import SubmissionResp

from thonnycontrib.easy.ui import EDITOR_CONTENT_NAME


def render(template_name: str, data: Dict) -> str:
    res_path = os.path.join(os.path.dirname(__file__), "templates", template_name)

    with open(res_path, mode="r", encoding="UTF-8") as f:
        return chevron.render(f, data)


def generate_update_html(versions):
    return render("update.mustache", versions)


def generate_exercise_list_html(base_url, exercises):
    ex_list = [f'<li><a href="{base_url}{e["id"]}">{e["effective_title"]}</a></li>' for e in exercises]
    if len(ex_list) == 0:
        return "<div>Siia kursusele ei ole veel ülesandeid lisatud.</div>"
    else:
        return f"<ul>{''.join(ex_list)}</ul>"


def generate_course_list_html(courses):
    course_lst = [f'<li><a href="/student/courses/{c["id"]}/exercises/">{c["title"] if c.get("alias", None) is None else c["alias"]}</a></li>' for c in courses]
    if len(course_lst) == 0:
        return "<div>Sind ei ole veel ühelegi kursusele lisatud.</div>"
    else:
        return f"<ul>{''.join(course_lst)}</ul>"


def generate_role_not_allowed_html():
    return "<div>Sul puudub õpilase roll, mis on vajalik plugina kasutamiseks.</div>"


def generate_login_html(from_url) -> str:
    return render("authenticate.mustache", {"from_url": "/" if from_url is None else from_url})


def generate_error_html(error_msg) -> str:
    return f"<h1>Viga!</h1><div>{error_msg}</div>"


def generate_error_auth() -> str:
    return f"""<h1>Autentimine ebaõnnestus!</h1><a href="/auth">Alusta autentimist uuesti</a>"""


def _convert_to_str(value):
    if value is None:
        return value
    else:
        return str(value)


def generate_exercise_html(provider, course_id, exercise_id) -> str:
    def has_submissions() -> bool:
        return len(provider.easy.student.get_all_submissions(course_id, exercise_id).submissions) > 0

    if has_submissions():
        latest = provider.easy.student.get_latest_exercise_submission_details(course_id, exercise_id)
    else:
        latest = SubmissionResp()

    details = provider.easy.student.get_exercise_details(course_id, exercise_id)
    return render("exercise.mustache", {"effective_title": details.effective_title,
                                        "text_html": details.text_html,
                                        "grade_auto": _convert_to_str(latest.grade_auto),
                                        "feedback_auto": latest.feedback_auto,
                                        "solution": latest.solution,
                                        "EDITOR_CONTENT_NAME": EDITOR_CONTENT_NAME,
                                        "course_id": course_id,
                                        "exercise_id": exercise_id,
                                        "latest_feedback_teacher": latest.feedback_teacher,
                                        "latest_grade_teacher": _convert_to_str(latest.grade_teacher),
                                        "provider_url": provider.easy.util.idp_client_name})
