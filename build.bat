REM  This is the default batch file for use when building the Windows versions of BrewFlasher
REM  The default command is as follows: 
REM
REM  pyinstaller --log-level=DEBUG ^
REM              --noconfirm ^
REM              build-on-win.spec
REM
REM  This command uses the default python installation to build the app. We want to build two versions:
REM  a 32 bit version and a 64 bit version. To accomplish this, I'm going to call two separate installations
REM  of Python. I'm assuming Python 3.7 (since that's what I have) installed for the local user (as 
REM  opposed to systemwide). 



REM  First, we'll create the 64 bit version
REM  Delete any previous versions
del "dist\BrewFlasher-1.0.exe" 
del "dist\BrewFlasher-1.0 x64.exe"
REM  Make sure packages for the 32 bit version are up-to-date
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python37\Scripts\pip.exe" install --upgrade -r requirements.txt
REM  And then, run pyinstaller
"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python37\Scripts\pyinstaller.exe" --log-level=DEBUG --noconfirm build-on-win.spec
REM Rename the file to x64
move "dist\BrewFlasher-1.0.exe" "dist\BrewFlasher-1.0 x64.exe"


REM  Next, we'll create the 32 bit version.
REM  Delete any previous versions
del "dist\BrewFlasher-1.0.exe" 
del "dist\BrewFlasher-1.0 x32.exe"
REM  Make sure packages for the 32 bit version are up-to-date
"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python37-32\Scripts\pip.exe" install --upgrade -r requirements.txt
REM  And then, we'll actually run pyinstaller
"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python37-32\Scripts\pyinstaller.exe" --log-level=DEBUG --noconfirm build-on-win.spec
REM Rename the file to x32
move "dist\BrewFlasher-1.0.exe" "dist\BrewFlasher-1.0 x32.exe"

