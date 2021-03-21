@echo off
setlocal
:PROMPT
SET /P AREYOUSURE=Are you sure you want to delete src (Y/[N])?
IF /I "%AREYOUSURE%" NEQ "Y" GOTO END
ECHO "Deleting substitution cache files..."
DEL /F/Q build\*.tar.gz
ECHO "Deleting source files..."
DEL /F/Q/S build\src > NUL
ECHO "Deleting source folders..."
RMDIR /Q/S build\src
DEL /F/Q/S build\patches > NUL
RMDIR /Q/S build\patches 
DEL /F/Q/S build\temp_patches> NUL
RMDIR /Q/S build\temp_patches
DEL /F/Q/S build\unpatched> NUL
RMDIR /Q/S build\unpatched>

:END
endlocal