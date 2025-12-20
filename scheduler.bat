@echo off
cd /d "C:\Users\joswa\OneDrive\Desktop\Punch_Automation"
call venv\Scripts\activate
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
python punch_normal.py
python punch_site.py
exit