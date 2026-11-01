import os
import tempfile


def use_temp_home():
    d = tempfile.mkdtemp(prefix="mealhome_")
    os.environ["MEALHELPER_HOME"] = d
    return d
