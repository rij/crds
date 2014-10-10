# The "crds" __version__ defined here should also reflect the behavior of 
# crds.client
__version__ = "1.2.0"   # see also setup.py

# ============================================================================

__all__ = [ 
           "get_default_context", 
           "getreferences", 
           "getrecommendations",
           "get_cached_mapping",
           
           "CrdsError", 
           "CrdsNetworkError", 
           "CrdsLookupError", 
           "CrdsDownloadError",
           
           "CrdsUnknownInstrumentError",
           "CrdsUnknownRefypeError",
           ]

# ============================================================================

from . import config   # module
from crds.client import CrdsError, CrdsLookupError, CrdsNetworkError, CrdsDownloadError
from crds.client import get_default_context

from .heavy_client import getreferences, getrecommendations

from .rmap import get_cached_mapping, locate_mapping, locate_file
from .rmap import CrdsUnknownInstrumentError, CrdsUnknownReftypeError

# ============================================================================

def handle_version():
    """Handles --version printing for scripts."""
    import sys, crds
    if '--version' in sys.argv :
        print crds.__version__
        sys.exit(0)
