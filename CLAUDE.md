# CLAUDE.md

## What this is

**thonny-lahendus** — a Thonny plugin that puts the Easy/Lahendus learning platform (lahendus.ut.ee, University of Tartu) inside the editor: students browse courses and exercises, submit the active editor's contents, and read their grade and teacher feedback without leaving Thonny. Published on PyPI as `thonny-lahendus`; the package directory is `thonnycontrib/easy`.

The GitHub remote has moved to `kspar/thonny-easy` (pushes to the old `easy-thonny` URL still work by redirect).

Sibling checkouts:

- `../easy-py` — the SDK this plugin talks to (`easy-py` on PyPI). All auth and HTTP lives there, not here. Has its own CLAUDE.md, including the auth-flow invariants.
- `../easy` — the platform itself. Response shapes are in `core/src/main/kotlin/core/ems/service/*.kt`, most usefully `assessments.kt`.

Issues are YouTrack `EZ-*`; the web UI is a JS SPA, so read them through the API:

```bash
curl -s "https://easy.myjetbrains.com/youtrack/api/issues/EZ-1805?fields=summary,description,comments(text)"
```

## How a page gets rendered

`ExercisesView` (`ui.py`) is a Tk widget hosting a small HTML renderer (`htmltext.py`). It owns a thread pool and calls into an `ExerciseProvider`; `EasyExerciseProvider` (`easy_provider.py`) is the real implementation.

`get_html_and_breadcrumbs(url, form_data)` is the entry point for everything. It is a URL router over an internal, made-up URL space (`/student/courses/7/exercises/8`, `/auth`, `/logout`, `/lang`), matched with the regexes at the top of the file. It returns `(html, breadcrumbs)`; the HTML is built in `templates_generator.py` from Mustache templates in `templates/` via `chevron`.

Things that follow from that design:

- **Every render passes through `_update_required()` first**, so anything that can raise there takes down every page, not just one. It is now wrapped in try/except and backs off for 10 minutes on failure. Keep it that way.
- **`AuthRequiredException` is caught by the router**, which returns the login page. That is the normal not-logged-in path, not an error.
- Provider methods run on the thread pool, so blocking calls there do not freeze the UI, but they do stall the page — give every network call a timeout.
- Localisation is two dicts (`strings_et` / `strings_en`) merged into the template context with `|`. The chosen language lives in `lahendus.ini` under Thonny's user dir. Estonian is the default and the fallback.

## Talking to the API

The plugin holds an `Ez` instance (`self.easy`) built in `_get_easy()`. It calls `Ez.student.*`, and **`util.handle_response` in the SDK only instantiates the top-level dataclass** — so `activities`, `submissions`, `inline_comments` and friends arrive as plain dicts. Read them with `.get()` and assume any field can be missing or `None`; a server-side shape change will not raise here, it will silently render nothing. That is exactly how EZ-1804 hid: the response was flattened in core v4.0, the old nested read returned `""`, and a truthiness guard skipped the feedback with no error anywhere.

Because production and dev can run different core versions, **read tolerantly across both shapes** where they differ, and treat a missing endpoint as "no data" rather than an error:

- teacher feedback: `ta.get("feedback_html") or (ta.get("feedback") or {}).get("feedback_html") or ""`
- inline comments: the endpoint is v4.0-only, so `ErrorResponseException` means "older server", and the section is simply omitted.

Two more shape facts worth remembering: inline comments span **all** submissions, so filter to the one on screen with `submission_number`; and there is no `type` field on them — a non-null `suggested_code` is what makes a comment a suggestion.

Anything the server sends as `*_html` is trusted, rendered HTML and goes into the template unescaped (`{{{ }}}`). Anything else that reaches HTML — code, names, user text — must go through `html.escape` first.

Exercise descriptions carry **root-relative** image `src` values (`/v2/resource/<key>/<file>`), which `urlopen` cannot fetch. `EasyExerciseProvider.get_image` resolves them with `urljoin(self.easy.util.api_url, url)`. Do not prefix `api_url` by hand: it already ends in `/v2`, so string concatenation yields `/v2/v2/...` and a 404 that looks exactly like the bug you are fixing. `urljoin` replaces the whole path and leaves absolute URLs alone.

## Environments

`PRODUCTION` (top of `easy_provider.py`) switches hosts; `SITE_HOST` is the website used for links and the post-logout redirect. Keep it separate from the OIDC client id — on dev they differ, since dev's client id is `lahendus.ut.ee` while the site is `dev.lahendus.ut.ee` (`https://dev.lahendus.ut.ee/config.json` is the authority).

Dev runs the newer core, so it is the place to test v4.0 behaviour — but **dev login is currently blocked**: its IdP client has no loopback redirect URIs registered, so the browser flow fails before it starts. Prod accepts them. Until that is fixed IdP-side, dev is only usable for work that does not need a fresh login.

## Versioning — read before releasing

The update check is the plugin's own tripwire and it constrains what you may publish:

- **Exactly three numeric components.** Installed 9.2.0 clients parse the published version with `major, minor, patch = version.split(".")`, so `10.0` or `10.0.0.post1` raises there — and since that runs before every render, it turns every page into an error page for those users. This constraint holds for as long as 9.2.0 installs exist, regardless of how tolerant the current parser is.
- **Only a major bump prompts anyone.** `_update_required` compares the major component alone, so a fix shipped as 10.0.1 or 10.1.0 reaches nobody who has not already upgraded.
- The installed version is read with `importlib.metadata`. **Never `pkg_resources`** — it ships with setuptools, which is absent from Thonny's bundled Python, and importing it crashed the whole view on startup.

## Thonny hosting

Thonny bundles its own interpreter and installs plugins into its own user directory, not into a system Python — on Windows that is `%APPDATA%\Thonny\plugins\Python<XYZ>\site-packages`. Thonny 5 bundles Python 3.14. That environment is missing things you may assume are present, setuptools included. When touching imports, dependencies, or anything version-related, verify against it by making a venv from the interpreter inside the Thonny installation.

Installing the plugin there must also *upgrade* whatever the previous release pinned, which a fresh-venv test does not exercise — an already-satisfied floor leaves an old, possibly broken dependency in place.

## Testing

There is no test suite. The renderer is straightforward to exercise anyway: `generate_exercise_html(provider, course_id, exercise_id, lang)` only needs an object exposing `site_host` and `easy.student.*`, so a hand-rolled fake provider returning canned dicts covers feedback shapes, comment filtering and sorting, escaping, and missing-endpoint handling without a network or a GUI. Worth turning into a committed test if this area is touched again.

For anything auth- or UI-shaped, run the real thing: `PRODUCTION = False`, `pip install -e` both repos into a Thonny environment, and open the view.

## Build and release

```bash
build.cmd
publish.cmd 10.0.1
```

Both scripts invoke Python through the `py` launcher rather than `python`, because on Windows `python` frequently resolves to the Microsoft Store alias stub, which reports that Python was not found instead of running. They also install `build` / `twine` on demand, since neither is present by default.

- `build.cmd` builds from a staged copy under `%TEMP%`, not in place. Building in the working tree fails with `Access is denied` on `egg_info` whenever a file-syncing client, indexer or antivirus is holding it — which the build cannot do anything about. Staging also means files deleted since the last build cannot reach the wheel, since `build/` and `*.egg-info` are never copied across.
- **`publish.cmd` takes the version** and uploads only that release. `dist/` keeps every earlier build, and PyPI refuses a file that already exists, so an unscoped `twine upload dist/*` fails on the old files before reaching the new ones. It runs `twine check` before uploading.
- **Publish `easy-py` first** — the plugin's metadata requires the matching SDK version.
- Releases are tagged `vX.Y.Z`, matching the published version.

`requirements.txt` is only a dev convenience: it is a single `-e .`, so `pip install -r requirements.txt` gives an editable install and the dependencies come from `setup.py`. It deliberately holds no version list of its own — the duplicate it used to carry drifted out of sync with `setup.py` twice.

`.gitignore` here covers only `__pycache__` and `.idea`, so `build/`, `dist/` and `*.egg-info` show as untracked — take care not to sweep them into a commit.

## Background

The 10.x line (2026-08) fixed a startup crash on Thonny 5 (`pkg_resources`), restored teacher feedback after the v4.0 response was flattened, made exercise images render for the first time, and added inline comments. The companion SDK release is easy-py 0.8.0, which rewrote login; see `../easy-py/PLAN-EZ-1803-1806.md` for the full account.
