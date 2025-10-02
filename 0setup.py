from distutils.core import setup
import py2exe

setup(
zipfile = None,
windows=[{u'script': u'morinus.py','bundle_files': 1,'compressed': True, 'optimize': 2,u'icon_resources': [(1, u'Res/Morinus.ico')] }]
)

#setup(console=[u"morinus.py"],
#      options={
#          'py2exe': {
#              'bundle_files': 1,
#              'compressed': True,
#              'optimize': 2,
#              'includes': ['module1',
#              'icon_resources': [(1, 'Res\\Morinus.ico')]
#          }
#      }
#)