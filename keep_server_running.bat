@echo off
echo Starting Finance Tracker Server...
echo.

echo Checking network information for mobile access...
ipconfig | findstr "IPv4"
echo.
echo Make note of your computer's IPv4 Address above to access from mobile devices
echo Mobile Access URL: http://YOUR_IP_ADDRESS:8000
echo.
echo ====================================================================
echo Server is starting... The terminal will show access URLs
echo ====================================================================
echo.

:start
python manage.py runserver 0.0.0.0:8000
echo Server stopped, restarting in 5 seconds...
timeout /t 5
goto start
