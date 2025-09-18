# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['morinus.py'],
             pathex=['C:\\morinus-src\\morinus-code'],
             binaries=[('SWEP\\src\\Windows\\32bit\\sweastrology.pyd', '.')],
             datas=[('Res', 'Res'), ('Hors', 'Hors'), ('Opts', 'Opts'), ('Data', 'Data'), ('SWEP\\Ephem', 'SWEP\\Ephem'), ('Morinus.ico', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Morinus',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='Morinus.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Morinus')
