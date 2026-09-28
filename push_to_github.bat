@echo off
title Push Vendor Agreement System to GitHub
echo ========================================================
echo Pushing code to https://github.com/nauratan91-collab/vendor-agreement-system.git ...
echo ========================================================
"C:\Users\ITkey\AppData\Local\Programs\Git\cmd\git.exe" push -u origin main
echo ========================================================
if %ERRORLEVEL% EQU 0 (
    echo Successfully uploaded to GitHub!
) else (
    echo Error pushing to GitHub. Please make sure the repo exists at:
    echo https://github.com/nauratan91-collab/vendor-agreement-system
)
echo ========================================================
pause
