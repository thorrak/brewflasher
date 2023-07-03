. .\venv64\Scripts\activate.ps1
cd .\pyinstaller\bootloader
python.exe ./waf distclean all
cd ..
python.exe setup.py install
cd ..
