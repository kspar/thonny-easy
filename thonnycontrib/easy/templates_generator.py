import os
from typing import Dict

import chevron
from easy import SubmissionResp

from thonnycontrib.easy.ui import EDITOR_CONTENT_NAME


def render(template_name: str, data: Dict) -> str:
    res_path = os.path.join(os.path.dirname(__file__), "templates", template_name)

    with open(res_path, mode="r", encoding="UTF-8") as f:
        return chevron.render(f, data)


def generate_exercise_list_html(base_url, exercises):
    ex_list = [f'<li><a href="{base_url}{e["id"]}">{e["effective_title"]}</a></li>' for e in exercises]
    html = f"<ul>{''.join(ex_list)}</ul>"
    return html


def generate_course_list_html(courses):
    format_c = [f'<li><a href="/student/courses/{c["id"]}/exercises/">{c["title"]}</a></li>' for c in courses]
    html = f"<ul>{''.join(format_c)}</ul>"
    return html


def generate_login_html(from_url) -> str:
    return render("authenticate.mustache", {"from_url": "/" if from_url is None else from_url})


def generate_error_html(error_msg) -> str:
    return f"<h1>Viga!</h1><div>{error_msg}</div>"


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
                                        "grade_auto": latest.grade_auto,
                                        "feedback_auto": latest.feedback_auto,
                                        "solution": latest.solution,
                                        "EDITOR_CONTENT_NAME": EDITOR_CONTENT_NAME,
                                        "course_id": course_id,
                                        "exercise_id": exercise_id,
                                        "latest_feedback_teacher": latest.feedback_teacher,
                                        "latest_grade_teacher": latest.grade_teacher,
                                        "provider_url": provider.easy.util.idp_client_name})
