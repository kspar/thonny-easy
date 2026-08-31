@echo off
setlocal

rem Builds the sdist and wheel into dist\.
rem
rem Uses the py launcher rather than "python": on Windows, "python" often
rem resolves to the Microsoft Store alias stub, which reports that Python was
rem not found instead of running anything.

set "PY=py -3"
where py >nul 2>&1 || set "PY=python"

rem Files deleted since the last build survive in build\ and get packed into the
rem next wheel, so start from a clean tree.
if exist build rmdir /s /q build

%PY% -m build --version >nul 2>&1 || %PY% -m pip install --upgrade build || goto :failed

%PY% -m build --sdist --wheel || goto :failed

echo.
echo Built into dist\:
dir /b dist
exit /b 0

:failed
echo.
echo Build failed.
echo If egg_info stopped with a permission or file-lock error, copy the project
echo to a plain local directory, build there, and move the artifacts back.
exit /b 1
