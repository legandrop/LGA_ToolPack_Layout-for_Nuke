# Using ordered dictionary or nuke12 makes a jumbled mess of the buttons.
from collections import OrderedDict
colors = OrderedDict()

# The script it's expecting 3 HSV colors per element.
colors["red"] =        {"hsv": [[0.03, 0.45, 0.33], [0.03, 0.30, 0.44], [0.03, 0.54, 0.61]], "tooltip": "Quickly apply between 3 shades of red to the Backdrop",       "newline": False, "title": False}
colors["orange"] =     {"hsv": [[0.11, 0.45, 0.33], [0.11, 0.30, 0.44], [0.11, 0.54, 0.61]], "tooltip": "Quickly apply between 3 shades of orange to the Backdrop",    "newline": False, "title": False}
colors["yellow"] =     {"hsv": [[0.16, 0.45, 0.33], [0.16, 0.30, 0.44], [0.16, 0.54, 0.61]], "tooltip": "Quickly apply between 3 shades of yellow to the Backdrop",    "newline": False, "title": False}
colors["green"] =      {"hsv": [[0.32, 0.45, 0.33], [0.32, 0.30, 0.44], [0.32, 0.54, 0.61]], "tooltip": "Quickly apply between 3 shades of green to the Backdrop",     "newline": False, "title": False}
colors["cyan"] =       {"hsv": [[0.49, 0.45, 0.33], [0.49, 0.30, 0.44], [0.49, 0.54, 0.61]], "tooltip": "Quickly apply between 3 shades of cyan to the Backdrop",      "newline": False, "title": False}
colors["blue"] =       {"hsv": [[0.55, 0.45, 0.33], [0.55, 0.30, 0.44], [0.55, 0.54, 0.61]], "tooltip": "Quickly apply between 3 shades of blue to the Backdrop",      "newline": False, "title": False}
colors["dark_blue"] =  {"hsv": [[0.72, 0.45, 0.33], [0.66, 0.30, 0.44], [0.66, 0.54, 0.61]], "tooltip": "Quickly apply between 3 shades of dark_blue to the Backdrop", "newline": False, "title": False}
colors["magenta"] =    {"hsv": [[0.79, 0.45, 0.33], [0.79, 0.30, 0.44], [0.79, 0.54, 0.61]], "tooltip": "Quickly apply between 3 shades of magenta to the Backdrop",   "newline": False, "title": False}
colors["pink"] =       {"hsv": [[0.88, 0.45, 0.33], [0.88, 0.30, 0.44], [0.88, 0.54, 0.61]], "tooltip": "Quickly apply between 3 shades of pink to the Backdrop",      "newline": False, "title": False}

# These colors will have the name showing and use the same color for all 3 HSV values.
colors["input"] =      {"hsv": [[0.00, 0.00, 0.60], [0.00, 0.00, 0.60], [0.00, 0.00, 0.60]], "tooltip": "Quickly apply a Backdrop for Cam",                            "newline": True,  "title": True}
colors["AOVs"] =       {"hsv": [[0.00, 0.00, 0.40], [0.00, 0.00, 0.40], [0.00, 0.00, 0.40]], "tooltip": "Quickly apply a Backdrop for Elements",                       "newline": False, "title": True}
colors["Mattee"] =       {"hsv": [[0.32, 0.08, 0.50], [0.32, 0.08, 0.50], [0.32, 0.08, 0.50]], "tooltip": "Quickly apply a Backdrop for Key",                            "newline": False, "title": True}
colors["crypt"] =      {"hsv": [[0.32, 0.53, 0.40], [0.32, 0.53, 0.40], [0.32, 0.53, 0.40]], "tooltip": "Quickly apply a Backdrop for Cleanup",                        "newline": False, "title": True}
colors["refe"] =       {"hsv": [[0.59, 0.55, 0.34], [0.59, 0.55, 0.34], [0.59, 0.55, 0.34]], "tooltip": "Quickly apply a Backdrop for Ref",                            "newline": False, "title": False}
colors["otro"] =       {"hsv": [[0.58, 0.05, 0.60], [0.58, 0.05, 0.60], [0.58, 0.05, 0.60]], "tooltip": "Quickly apply a Backdrop for CG",                             "newline": False, "title": False}
colors["otro"] =       {"hsv": [[0.66, 0.00, 0.67], [0.66, 1.00, 0.67], [0.66, 1.00, 0.67]], "tooltip": "Quickly apply a Backdrop for Matte",                          "newline": False, "title": False}
colors["otro"] =       {"hsv": [[0.63, 0.41, 0.47], [0.63, 0.41, 0.47], [0.63, 0.41, 0.47]], "tooltip": "Quickly apply a Backdrop for Pub",                            "newline": False, "title": False}