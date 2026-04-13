import sys
import os
import warnings

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# 在所有测试之前过滤 FAISS Swig 警告
warnings.filterwarnings("ignore", category=DeprecationWarning, module="importlib._bootstrap")
warnings.filterwarnings("ignore", message="builtin type.*has no __module__ attribute")
