# Image.py shim for Pillow -> old "import Image" style
try:
    from PIL.Image import *
    from PIL import Image as _mod
    __all__ = [n for n in dir(_mod) if not n.startswith('_')]
except ImportError:
    pass
