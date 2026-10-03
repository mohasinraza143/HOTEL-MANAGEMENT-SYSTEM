@echo off
set GIT_EXE="C:\Users\mohas\AppData\Local\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd\git.exe"
echo ========================================================
echo   Aurora Haven Hotel - Push to GitHub for Render
echo ========================================================
echo.
set /p REPO_URL="Enter your GitHub Repository URL: "

echo.
echo Connecting repository to %REPO_URL%...
%GIT_EXE% remote remove origin >nul 2>&1
%GIT_EXE% remote add origin %REPO_URL%
%GIT_EXE% branch -M main

echo Pushing code to GitHub main branch...
%GIT_EXE% push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo   SUCCESS! Your code has been pushed to GitHub.
    echo   Next step: Go to dashboard.render.com to deploy!
    echo ========================================================
) else (
    echo An error occurred during push. Please check your credentials/URL.
)
pause
