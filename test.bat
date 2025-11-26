@echo off
set "parent=teszter\test_cases"

for /D %%F in ("%parent%\*") do (
    call run.bat "%%F"
)

cd teszter
dusza_teszter.exe
pause