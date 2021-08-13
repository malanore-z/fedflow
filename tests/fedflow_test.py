try:
    import fedflow
except:
    import os
    import sys
    root_dir = os.path.dirname(os.path.dirname(__file__))
    fedflow_dir = os.path.join(root_dir, "src")
    sys.path.insert(0, fedflow_dir)