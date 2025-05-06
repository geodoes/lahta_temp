@echo off
echo Server is Starting...
pause

ipconfig
pause

echo Activating virtual environment...
call env\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Running server...
python run.py

pause
