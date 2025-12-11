"""import compatible pyside lib for each version of nuke"""

import nuke
from qt_compat import QtCore, QtGui, QtWidgets

# Exportar todo como hacía el import original
globals().update({name: getattr(QtCore, name) for name in dir(QtCore) if not name.startswith("_")})
globals().update({name: getattr(QtGui, name) for name in dir(QtGui) if not name.startswith("_")})
globals().update({name: getattr(QtWidgets, name) for name in dir(QtWidgets) if not name.startswith("_")})

# Compatibilidad con Signal si se usaba
Signal = getattr(QtCore, "Signal", getattr(QtCore, "pyqtSignal", None))