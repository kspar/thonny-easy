from thonnycontrib.easy.ui import EDITOR_CONTENT_NAME


def generate_exercise_list_html(base_url, exercises):
    ex_list = [f'<li><a href="{base_url}{e["id"]}">{e["effective_title"]}</a></li>' for e in exercises]
    html = f"<ul>{''.join(ex_list)}</ul>"
    return html


def generate_course_list_html(courses):
    format_c = [f'<li><a href="/student/courses/{c["id"]}/exercises/">{c["title"]}</a></li>' for c in courses]
    html = f"<ul>{''.join(format_c)}</ul>"
    return html


def generate_submit_html(course_id, exercise_id) -> str:
    submit_html = f"""
         <form action="/student/courses/{course_id}/exercises/{exercise_id}/submissions">
             <input type="hidden" name="{EDITOR_CONTENT_NAME}" />
             <input type="submit" value="Esita aktiivse redaktori sisu" />
         </form>       
     """
    return submit_html


def generate_login_html(from_url) -> str:
    if from_url is None:
        from_url = "/"

    return f"""
        <h1>LAHENDUS</h1>
        <form action="/auth">
             <input type="hidden" name="from" value="{from_url}"/>
             <input type="submit" value="Ava veebilehitseja autentimiseks" />
        </form>                    
    """


def generate_error_html(error_msg) -> str:
    return f"""
        <h1>Viga!</h1>
        <div>{error_msg}</div>"""


def generate_latest_submissions_html(provider, course_id, exercise_id) -> str:
    def has_submissions() -> bool:
        return len(provider.easy.student.get_all_submissions(course_id, exercise_id).submissions) > 0

    if not has_submissions():
        return "<h1>Esitamine</h1>"

    latest = provider.easy.student.get_latest_exercise_submission_details(course_id, exercise_id)

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
                    <code>{latest.feedback_auto}</code>
                </div> 

                <div>{teacher_feedback}</div> 

                <h2>Viimane esitus</h2>
                <div>
                    <code>{latest.solution}</code>
                </div> 
        """
