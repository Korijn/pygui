from importlib.metadata import version

from .collagraph import Collagraph  # noqa: F401
from .component import Component  # noqa: F401
from .renderers import *  # noqa: F403
from .sfc import importer  # noqa: F401
from .types import EventLoopType  # noqa: F401

__version__ = version("collagraph")
