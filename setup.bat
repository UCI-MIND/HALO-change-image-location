@echo off

echo *** Creating virtual environment...
python -m venv .venv
echo:

echo *** Activating virtual environment...
call .\.venv\Scripts\activate.bat
REM LINUX/MAC EQUIVALENT:
REM     source .venv/bin/activate
REM Confirm that the virtual environment is activated with
REM     which python
echo:

echo *** Installing packages...
python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt
echo:

echo *** Confirming Python version and installed packages:
python --version
python -m pip --version
python -m pip list -v
echo:

echo *** Setup complete, deactivating virtual environment...
call .\.venv\Scripts\deactivate.bat
REM LINUX/MAC EQUIVALENT:
REM     deactivate
echo:

echo *** Press enter to exit.
set /p input=
