import nuke
from PySide2 import QtWidgets, QtCore, QtGui
import time
from PySide2.QtGui import QCursor, QMouseEvent
from PySide2.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PySide2.QtCore import Qt, QEvent, QPoint, QTimer, QPropertyAnimation, QEasingCurve, Property

# Estado del zoom
_zoom_state = {
    'zoom_level': None,
    'is_zoomed_out': False,
    'timestamp': None
}

# Tiempo máximo entre clics (en segundos)
MAX_TIME_BETWEEN_CLICKS = 9

# Variables globales para mantener referencias
floating_message = None

def find_dag_widget():
    """Encuentra el widget del DAG"""
    for widget in QApplication.allWidgets():
        if widget.objectName() == "DAG.1":
            return widget
    return None

class FloatingMessage(QWidget):
    def __init__(self, text, parent=None):
        super(FloatingMessage, self).__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label con el texto
        self.label = QLabel(text)
        self.label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: #282828;
                padding: 5px 10px;
                border-radius: 4px;
                font-family: Verdana;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.label)
        
        # Ajustar tamaño
        self.adjustSize()
        
        # Encontrar el DAG y posicionar el mensaje
        dag_widget = find_dag_widget()
        if dag_widget:
            # Obtener geometría del DAG
            dag_geo = dag_widget.geometry()
            dag_global_pos = dag_widget.mapToGlobal(QPoint(0, 0))
            
            # Posicionar en la parte superior del DAG, centrado horizontalmente
            x = dag_global_pos.x() + (dag_geo.width() // 2) - (self.width() // 2)
            y = dag_global_pos.y() + 10  # Un pequeño margen desde el borde superior
            self.move(x, y)
        
        # Propiedad para la opacidad
        self._opacity = 1.0
        
        # Crear la animación
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(1000)  # 1 segundo
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.InQuad)
        self.animation.finished.connect(self.deleteLater)
        
        # Iniciar la animación inmediatamente
        self.animation.start()
    
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, value):
        self._opacity = value
        self.label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, {value});
                background-color: rgba(40, 40, 40, {value});
                padding: 5px 10px;
                border-radius: 4px;
                font-family: Verdana;
                font-size: 12px;
            }}
        """)
    
    # Definir la propiedad opacity
    opacity = Property(float, get_opacity, set_opacity)

def show_message(text):
    """Muestra un mensaje flotante cerca del cursor"""
    global floating_message
    
    # Asegurarse de que la instancia anterior se elimine
    if floating_message is not None:
        try:
            floating_message.deleteLater()
        except:
            pass
    
    # Crear nueva instancia
    floating_message = FloatingMessage(text)
    floating_message.show()

def zoom_toggle():
    """
    Alterna entre el zoom guardado y zoom total del DAG
    """
    global _zoom_state
    
    current_time = time.time()
    
    # Si pasaron más de MAX_TIME_BETWEEN_CLICKS segundos, resetear el estado
    if _zoom_state['is_zoomed_out'] and _zoom_state['timestamp']:
        if current_time - _zoom_state['timestamp'] > MAX_TIME_BETWEEN_CLICKS:
            _zoom_state['is_zoomed_out'] = False
            _zoom_state['zoom_level'] = None
            _zoom_state['timestamp'] = None
    
    if not _zoom_state['is_zoomed_out']:
        # Guardar zoom actual y timestamp
        _zoom_state['zoom_level'] = nuke.zoom()
        _zoom_state['timestamp'] = current_time
        
        # Hacer zoom out a todo el DAG (deseleccionar todo primero)
        nuke.selectAll()
        nuke.invertSelection()
        nuke.zoomToFitSelected()
        _zoom_state['is_zoomed_out'] = True
        
        # Mostrar mensaje de Zoom Out
        show_message("Zoom Out")
        
    else:
        # Obtener el widget bajo el cursor
        widget = QApplication.widgetAt(QCursor.pos())
        cursor_before = QCursor.pos()
        
        if widget:
            # Simular un click completo (press y release) en el widget
            local_pos = widget.mapFromGlobal(cursor_before)
            
            # Mouse press
            press_event = QMouseEvent(QEvent.MouseButtonPress, 
                                    local_pos,
                                    Qt.LeftButton, 
                                    Qt.LeftButton, 
                                    Qt.NoModifier)
            QApplication.sendEvent(widget, press_event)
            
            # Mouse release
            release_event = QMouseEvent(QEvent.MouseButtonRelease, 
                                      local_pos,
                                      Qt.LeftButton, 
                                      Qt.LeftButton, 
                                      Qt.NoModifier)
            QApplication.sendEvent(widget, release_event)
            
            # Crear un NoOp temporal
            temp_node = nuke.createNode("NoOp", inpanel=False)
            
            # Obtener el centro del nodo temporal
            xC = temp_node.xpos() + temp_node.screenWidth()/2
            yC = temp_node.ypos() + temp_node.screenHeight()/2
            
            # Hacer zoom al nivel guardado usando el centro del nodo temporal
            nuke.zoom(_zoom_state['zoom_level'], [xC, yC])
            
            # Eliminar el nodo temporal
            nuke.delete(temp_node)
            
            # Resetear el estado
            _zoom_state['is_zoomed_out'] = False
            _zoom_state['timestamp'] = None
            
            # Mostrar mensaje de Zoom In
            show_message("Zoom In")

class MiddleClickInterceptor(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.start_pos = None  # Guarda la posición inicial del clic

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.MiddleButton:
                self.start_pos = event.pos()  # Guarda la posición inicial del clic
                return False  # Permitimos el evento para no bloquear el drag

        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            if event.button() == QtCore.Qt.MiddleButton and self.start_pos:
                end_pos = event.pos()  # Obtiene la posición final
                distance = (end_pos - self.start_pos).manhattanLength()  # Calcula la distancia

                if distance < 5:  # Si no hubo arrastre (clic normal)
                    self.start_pos = None  # Reseteamos la posición inicial

                    # 🔹 🔹 FORZAMOS QUE Qt PROCESE EL EVENTO DE LIBERACIÓN 🔹 🔹
                    QtCore.QTimer.singleShot(10, self.force_mouse_release)

                    # 🔹 🔹 EJECUTAMOS LA FUNCIÓN DE ZOOM EN LUGAR DEL MENSAJE 🔹 🔹
                    QtCore.QTimer.singleShot(50, zoom_toggle)

                    return True  # Bloqueamos la acción original solo para clic sin drag

                self.start_pos = None
                return False  # Permitimos que el evento siga su curso normal

        return False  # Permitimos otros eventos

    def force_mouse_release(self):
        """ Envía manualmente un evento de liberación del botón del medio. """
        widget = QtWidgets.QApplication.instance().widgetAt(QtGui.QCursor.pos())  # Obtiene el widget actual
        if widget:
            release_event = QtGui.QMouseEvent(
                QtCore.QEvent.MouseButtonRelease,
                QtGui.QCursor.pos(),  # Usa la posición actual del cursor
                QtCore.Qt.MiddleButton,
                QtCore.Qt.NoButton,
                QtCore.Qt.NoModifier
            )
            QtWidgets.QApplication.sendEvent(widget, release_event)  # Envía el evento

# Instalar el filtro en la aplicación de Nuke
app = QtWidgets.QApplication.instance()
if app:
    interceptor = MiddleClickInterceptor()
    app.installEventFilter(interceptor)
