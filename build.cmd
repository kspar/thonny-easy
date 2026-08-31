@echo off
setlocal

rem Builds the sdist and wheel into dist\.
rem
rem Uses the py launcher rather than "python": on Windows, "python" often
rem resolves to the Microsoft Store alias stub, which reports that Python was
rem not found instead of running anything.

set "PY=py -3"
where py >nul 2>&1 || set "PY=python"

%PY% -m build --version >nul 2>&1 || %PY% -m pip install --upgrade build || goto :failed

rem Build from a staged copy rather than in place. egg_info fails with
rem "Access is denied" whenever a file-syncing client, indexer or antivirus is
rem holding the tree, which the build itself cannot do anything about. Staging
rem also guarantees that files deleted since the last build cannot reach the
rem wheel, because build\ and *.egg-info are never copied across.

set "STAGE=%TEMP%\thonny-lahendus-build"
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%" || goto :failed

robocopy . "%STAGE%" /E /NFL /NDL /NJH /NJS /NP /XD build dist .git .idea __pycache__ /XF *.pyc >nul
if errorlevel 8 goto :failed
for /d %%D in ("%STAGE%\*.egg-info") do rmdir /s /q "%%D"

pushd "%STAGE%" || goto :failed
%PY% -m build --sdist --wheel
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" goto :failed

if not exist dist mkdir dist
copy /y "%STAGE%\dist\*" dist\ >nul || goto :failed
rmdir /s /q "%STAGE%"

echo.
echo Built into dist\:
dir /b dist
exit /b 0

:failed
echo.
echo Build failed.
exit /b 1
