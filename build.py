from py2exe.build_exe import py2exe
from distutils.core import setup

setup(
  name        = 'renderb0x',
  author      = 'sk1LLb0X',
  version     = '0.1',
  windows     = ['main.pyw'],
  options     = {'py2exe': {'bundle_files': 3, 'compressed': False, 'includes':['sip'], 'dll_excludes':['MSVCP90.dll']}},
  zipfile     = None,
  data_files  = [('sounds', ['sounds/done.wav'], 'ffmpeg_x64.exe', 'ffmpeg_x86.exe')]
)