# -*- mode: python -*-

block_cipher = None

a = Analysis(['nodemcu-pyflasher.py'],
             binaries=None,
             datas=[("images", "images")],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='BrewFlasher',
          debug=False,
          strip=False,
          upx=True,
          target_arch='arm64',
          entitlements_file='Entitlements.plist',
          codesign_identity='Developer ID Application: John Beeler (RAS94LVJ7S)',
          console=False , icon='images/icon-256.icns')
app = BUNDLE(exe,
             name='BrewFlasher-1.2.app',
             icon='./images/icon-256.icns',
             bundle_identifier='com.brewflasher.macos',
             info_plist={
               'NSPrincipalClass': 'NSApplication',
               'NSAppleScriptEnabled': False,
               'LSRequiresIPhoneOS': False,
               'LSApplicationCategoryType': 'public.app-category.utilities',
               'CFBundleVersion': '1.2.0',
               'CFBundleShortVersionString': '1.2',
               'CFBundleSignature': 'BFLS',
               'LSMinimumSystemVersion': '10.0.0'
               },
            )
