import json
import logging
import os
from datetime import datetime
from html import escape
from typing import Dict

import chevron
from easy import ErrorResponseException

from thonnycontrib.easy.ui import EDITOR_CONTENT_NAME

logger = logging.getLogger(__name__)


def render(template_name: str, data: Dict) -> str:
    res_path = os.path.join(os.path.dirname(__file__), "templates", template_name)

    with open(res_path, mode="r", encoding="UTF-8") as f:
        return chevron.render(f, data)


def generate_update_html(versions, lang="et"):
    return render("update_et.mustache" if lang == "et" else "update_en.mustache", versions)


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
                   "button": "Ava sisse logimiseks veebilehitseja" if lang == "et" else "Open a web browser to log in"})


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
            msg = "    " + test['exception_message'].replace("\n", "\n    ")
            exception = f"  {locale_dict['EXCEPTION']}:\n\n{msg}\n"

        if test['created_files'] is None or len(test['created_files']) == 0:
            created_files = ""
        else:
            files = [(x['name'], x['content']) for x in test['created_files']]
            files = ["    ---" + name + "---\n" + content for (name, content) in files]
            files = [content.replace("\n", "\n    ") for content in files]
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
                  "POINTS_TITLE": "Valid grade",
                  "SUBMITTING_TITLE": "Submit",
                  "SUBMIT_ACTIVE": "Submit the contents of the active editor",
                  "TEACHER_COMMENT": "Teacher feedback",
                  "AUTOMATIC_TESTS": "Automated tests",
                  "LAST_SUBMISSION": "Latest submission",
                  "SEE_IN_LAHENDUS": "See the task in Lahendus",
                  "GAVE_INPUTS": "Inputs provided to the program",
                  "OUTPUT_WAS": "The program's full output",
                  "EXCEPTION": "There was an exception during the program's execution",
                  "CREATED_FILES": "Before running the program, the following files were created",
                  "INLINE_COMMENTS": "Comments on the code",
                  "SUGGESTION": "Suggested code",
                  "LINE": "Line",
                  "LINES": "Lines"
                  }

    strings_et = {"CLOSED_DENIED_INFO": "See ülesanne on suletud ja ei luba enam uusi esitusi",
                  "SUBMITTING_TITLE": "Esitamine",
                  "POINTS_TITLE": "Kehtiv hinne",
                  "SUBMIT_ACTIVE": "Esita aktiivse redaktori sisu",
                  "TEACHER_COMMENT": "Tagasiside",
                  "AUTOMATIC_TESTS": "Automaatsed testid",
                  "LAST_SUBMISSION": "Viimane esitus",
                  "SEE_IN_LAHENDUS": "Vaata ülesannet Lahenduses",
                  "GAVE_INPUTS": "Andsin programmile sisendid",
                  "OUTPUT_WAS": "Programmi täielik väljund oli",
                  "EXCEPTION": "Programmi käivitamisel tekkis viga",
                  "CREATED_FILES": "Enne programmi käivitamist lõin failid",
                  "INLINE_COMMENTS": "Kommentaarid koodile",
                  "SUGGESTION": "Soovitatud kood",
                  "LINE": "Rida",
                  "LINES": "Read"
                  }

    strings = strings_et if lang == "et" else strings_en

    details = provider.easy.student.get_exercise_details(course_id, exercise_id)

    def _format_date(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').strftime('%d.%m.%Y %H:%M')
        except (ValueError, TypeError):
            return date_str  # In case of a formatting error, leave it as is

    def _format_teacher_name(entity):
        teacher = entity.get("teacher") or {}
        return escape((teacher.get("given_name") or "") + " " + (teacher.get("family_name") or ""))

    def _format_teacher_activity(ta, lang="et"):
        if ta is None:
            ta = {}

        teacher = _format_teacher_name(ta)

        # v4.0 has feedback_html flat on the activity; older servers nest it under "feedback".
        # `or ""` because the field is nullable server-side - None would render as "None".
        feedback_html = ta.get("feedback_html") or (ta.get("feedback") or {}).get("feedback_html") or ""
        grade = ta.get("grade", "")
        created_at = _format_date(ta.get("created_at", ""))
        submission_number = ta.get("submission_number", "")

        if grade == "" or grade is None:
            grade_text = ""
        else:
            grade_text = f" · Hinne: <b>{grade} / 100</b> " if lang == "et" else f" · Grade: <b>{grade} / 100</b> "
        submission_text = f"Esitus # {submission_number}" if lang == "et" else f"Submission # {submission_number}"

        html_output = f"<br/>    - {teacher} · {created_at} · {submission_text}{grade_text}<br/>"
        if feedback_html:
            html_output += f"{feedback_html}"

        return html_output

    def _format_inline_comment(comment):
        teacher = _format_teacher_name(comment)
        created_at = _format_date(comment.get("created_at", ""))

        line_start, line_end = comment.get("line_start"), comment.get("line_end")
        if line_end is None or line_end == line_start:
            lines_text = f"{strings['LINE']} {line_start}"
        else:
            lines_text = f"{strings['LINES']} {line_start}-{line_end}"

        html_output = f"<br/>    - {teacher} · {created_at} · {lines_text}<br/>"
        code = comment.get("code")
        if code:
            html_output += f"<pre><code>{escape(code)}</code></pre>"
        if comment.get("text_html"):
            html_output += comment["text_html"]
        # No `type` field: a non-null suggested_code is what makes a comment a suggestion
        suggested_code = comment.get("suggested_code")
        if suggested_code:
            html_output += f"<div>{strings['SUGGESTION']}:</div><pre><code>{escape(suggested_code)}</code></pre>"

        return html_output

    def has_submissions() -> bool:
        return len(provider.easy.student.get_all_submissions(course_id, exercise_id).submissions) > 0

    if not has_submissions():
        return render("exercise.mustache", {"effective_title": details.effective_title,
                                            "text_html": details.text_html,
                                            "is_open": details.is_open,
                                            "not_open": not details.is_open,
                                            "points": None,
                                            "feedback_type": None,
                                            "feedback_auto": None,
                                            "solution": None,
                                            "EDITOR_CONTENT_NAME": EDITOR_CONTENT_NAME,
                                            "course_id": course_id,
                                            "exercise_id": exercise_id,
                                            "latest_feedback_teacher": None,
                                            "inline_comments": None,
                                            "provider_url": provider.site_host} | strings)
    else:
        # Wait or AT assessment finish
        provider.easy.student.await_latest_exercise_submission_details(course_id, exercise_id)
        latest = provider.easy.student.get_all_submissions(course_id, exercise_id).submissions[0]
        grade_resp = latest.get("grade", {})

        # Python evals grade 0 to False later in the template. Convert to str
        points = None if grade_resp is None else str(grade_resp.get("grade", None))

        if points == "None":
            points = None


        is_autograde = False if grade_resp is None else grade_resp.get("is_autograde", False)
        feedback_type = "" if is_autograde else "🙎"
        feedback_auto = None

        try:
            auto_assessment = latest.get("auto_assessment", {})

            js = json.loads(auto_assessment.get("feedback", '{}'))
            if "result_type" in js:
                result_type = js["result_type"]

                if result_type == "OK_V3":
                    if js["pre_evaluate_error"] is None:
                        test_results = [_process_test(test, strings) for test in js["tests"]]
                        feedback_auto = '\n'.join(test_results)
                    else:
                        feedback_auto = js["pre_evaluate_error"]

                elif result_type == "OK_LEGACY":
                    feedback_auto = js["feedback"]

                elif result_type == "ERROR_V3":
                    feedback_auto = js["error"]
            else:
                feedback_auto = auto_assessment.get("feedback", "")

        except json.decoder.JSONDecodeError:
            feedback_auto = auto_assessment.get("feedback", "")
        except Exception as e:
            logger.error(latest)
            logger.exception(e, stacklevel=True, exc_info=True)

        activities = provider.easy.student.get_all_exercise_teacher_activities(course_id, exercise_id).teacher_activities
        activities = sorted(activities, key=lambda x: x.get('created_at', ""), reverse=True)

        # Or you can directly sort the list in place:
        teacher_activites = [_format_teacher_activity(ta, lang) for ta in activities] if activities is not None else []
        teacher_activites = "\n\n".join(teacher_activites)

        # Inline comments span all submissions; show only the ones on the submission that is on screen
        inline_comments = ""
        try:
            all_comments = provider.easy.student.get_inline_comments(course_id, exercise_id).inline_comments or []
            comments = [c for c in all_comments if c.get("submission_number") == latest.get("number")]
            comments.sort(key=lambda c: (c.get("line_start") or 0, c.get("created_at") or ""))
            inline_comments = "\n\n".join(_format_inline_comment(c) for c in comments)
        except ErrorResponseException:
            # Pre-v4.0 servers do not have the inline-comments endpoint; render the page without it
            logger.info("Inline comments are not available on this server")

        return render("exercise.mustache", {"effective_title": details.effective_title,
                                            "text_html": details.text_html,
                                            "is_open": details.is_open,
                                            "not_open": not details.is_open,
                                            "points": points,
                                            "feedback_type": feedback_type,
                                            "feedback_auto": feedback_auto,
                                            "solution": latest.get("solution", ""),
                                            "EDITOR_CONTENT_NAME": EDITOR_CONTENT_NAME,
                                            "course_id": course_id,
                                            "exercise_id": exercise_id,
                                            "latest_feedback_teacher": teacher_activites,
                                            "inline_comments": inline_comments,
                                            "provider_url": provider.site_host} | strings)
