"""
Context APIs
=============
"""

__all__ = [
    "WorkDirContext"
]


import os


class WorkDirContext(object):
    """
    Temporarily modify the work directory
    """

    def __init__(self, workdir):
        super(WorkDirContext, self).__init__()
        self.workdir = workdir

    def __enter__(self):
        self.pre_workdir = os.getcwd()
        os.chdir(self.workdir)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.pre_workdir)
