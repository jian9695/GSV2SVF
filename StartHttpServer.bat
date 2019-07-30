set SVFHOME=%~dp0
set PYTHONHOME=%SVFHOME%Miniconda3
set PYTHONPATH=%PYTHONHOME%Lib
set PythonDir=%PYTHONHOME%
cd  %SVFHOME%Cache
%PYTHONHOME%\python.exe -m http.server 8000 --bind 127.0.0.1