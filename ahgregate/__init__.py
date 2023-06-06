from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ahgregate")
except PackageNotFoundError:
    # package is not installed
    print('ahgregate is not installed')
    pass

from . scripts import *