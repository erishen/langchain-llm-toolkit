import os
import sys
import warnings

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "true"
os.environ["LITELLM_MODE"] = "PRODUCTION"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="builtin type.*has no __module__ attribute")
