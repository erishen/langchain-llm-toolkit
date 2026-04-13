import warnings

# 在所有测试之前过滤 FAISS Swig 警告
warnings.filterwarnings("ignore", category=DeprecationWarning, module="importlib._bootstrap")
warnings.filterwarnings("ignore", message="builtin type.*has no __module__ attribute")
