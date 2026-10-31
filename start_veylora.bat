@echo off
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
set "FLOWLENS_DATA_DIR=%~dp0data\processed"
call "%~dp0.venv\Scripts\activate.bat"
streamlit run app.py
pause
