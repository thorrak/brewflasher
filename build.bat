REM  This is the default batch file for use when building the Windows versions of BrewFlasher
REM  The default command is as follows: 
REM
REM  pyinstaller --log-level=DEBUG ^
REM              --noconfirm ^
REM              build-on-win.spec
REM
REM  This command uses the default python installation to build the app. While we used to build an x32
REM  and x64 version, beginning with BrewFlasher 1.2 I'm only going to support x64 going forward.
REM  I'm assuming Python 3.9 (since that's what I have) installed for the local user (as opposed to systemwide).



REM  First, we'll create the 64 bit version
REM  Delete any previous versions
del "dist\BrewFlasher-1.3.exe"
del "dist\BrewFlasher-1.3 x64.exe"
REM  Make sure packages for the 64 bit version are up-to-date
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\Scripts\pip.exe" install --upgrade -r requirements.txt
REM  And then, run pyinstaller
"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\Scripts\pyinstaller.exe" --log-level=DEBUG --noconfirm build-on-win.spec
REM Rename the file to x64
move "dist\BrewFlasher-1.0.exe" "dist\BrewFlasher-1.0 x64.exe"


REM  Next, we'll create the 32 bit version.
REM  Delete any previous versions
REM del "dist\BrewFlasher-1.3.exe"
REM del "dist\BrewFlasher-1.3 x32.exe"
REM  Make sure packages for the 32 bit version are up-to-date
REM "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python37-32\Scripts\pip.exe" install --upgrade -r requirements.txt
REM  And then, we'll actually run pyinstaller
REM "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python37-32\Scripts\pyinstaller.exe" --log-level=DEBUG --noconfirm build-on-win.spec
REM Rename the file to x32
REM move "dist\BrewFlasher-1.0.exe" "dist\BrewFlasher-1.0 x32.exe"

