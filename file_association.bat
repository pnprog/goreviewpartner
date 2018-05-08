@echo off

NET SESSION
IF %ERRORLEVEL% NEQ 0 GOTO ELEVATE
GOTO ADMINTASKS

:ELEVATE
CD /d %~dp0
MSHTA "javascript: var shell = new ActiveXObject('shell.application'); shell.ShellExecute('%~nx0', '', '', 'runas', 1);close();"
EXIT

:ADMINTASKS


::see https://superuser.com/questions/406985/programatically-associate-file-extensions-with-application-on-windows

set grp_path=%~dp0%
cd %~dp0%


set filename=main.py
if exist "%filename%" goto fromsources

set filename=GoReviewPartner.exe
if exist "%filename%" goto frompy2exe

pause
exit

:fromsources
echo GRP is running from the source



for /f "delims=" %%i in ('Assoc .py') do set filetype=%%i
set filetype=%filetype:~4% 
echo filetype for .py files: %filetype%


for /f "delims=" %%i in ('Ftype %filetype%') do set pythonexe=%%i
set pythonexe=%pythonexe:~12,-7%
echo path to python interpreter: %pythonexe%

set python_path="%grp_path%dual_view.py"
echo path to GRP python file: %python_path%

echo associating ".rsgf" extension with file type "rsgffile"
assoc .rsgf=rsgffile

echo setting the link between a rsgffile FileType and an GRP python file
ftype rsgffile=%pythonexe% %python_path% %%1

set ico_path="%grp_path%grp.ico"
echo path to GRP icon: %ico_path%

echo creating rsgffile entry in registry
REG ADD HKEY_CLASSES_ROOT\rsgffile /f

echo creating rsgffile\DefaultIcon key in registry
REG ADD HKEY_CLASSES_ROOT\rsgffile\DefaultIcon /ve /T REG_EXPAND_SZ /f /d %ico_path%

pause
exit

:frompy2exe

echo GRP is running from the py2exe version
echo not implemented yet
pause
exit

rem GRP is running from the py2exe version
rem let's associate *.rsgf file to GoReviewPartner.exe
::Assoc .rsgf=rsgffile
::Echo %~dpnx0 > %FOLDER%
::Set EXE=GoReviewPartner.exe
::Set FULLPATH=%FOLDER%%EXE%
::Ftype rsgffile=%FULLPATH% %1



