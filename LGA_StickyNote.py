"""
_______________________________________________

  LGA_StickyNote v1.0 | 2024 | Lega  
  Dialogo para crear notas rapidas en el Node Graph  
_______________________________________________

"""

import nuke
from PySide2 import QtWidgets, QtGui, QtCore


class StickyNote(QtWidgets.QDialog):
    def __init__(self):
        super(StickyNote, self).__init__()
        
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.title = QtWidgets.QLabel("<b>StickyNote</b>")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setStyleSheet("color: #AAAAAA;")

        self.help = QtWidgets.QLabel('<span style="font-size:7pt; color:#AAAAAA;">Ctrl+Enter para confirmar</span>')
        self.help.setAlignment(QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.help)
        self.setLayout(self.layout)
        self.resize(200, 150)
        self.setStyleSheet("background-color: #242527;")
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        self.text_edit.installEventFilter(self)
        self.texto_ingresado = ""
        
    def eventFilter(self, widget, event):
        if isinstance(event, QtGui.QKeyEvent):
            if event.key() == QtCore.Qt.Key_Return and event.modifiers() == QtCore.Qt.ControlModifier:
                self.texto_ingresado = self.text_edit.toPlainText()
                print("Texto ingresado:", self.texto_ingresado)
                self.close()
                return True
            elif event.key() == QtCore.Qt.Key_Escape:
                print("Se presionó ESC para salir")
                self.texto_ingresado = ""
                self.close()
                return True
        return False
    
    def showEvent(self, event):
        """Se llama cuando el diálogo se muestra"""
        super().showEvent(event)
        self.activateWindow()  # Activar la ventana
        self.raise_()          # Traer al frente
        self.text_edit.setFocus()  # Dar foco al text_edit

    def simulate_dag_click(self):
        """Simula un click en el DAG en la posición actual del cursor"""
        widget = QtWidgets.QApplication.widgetAt(QtGui.QCursor.pos())
        if widget:
            cursor_pos = QtGui.QCursor.pos()
            local_pos = widget.mapFromGlobal(cursor_pos)
            
            # Mouse press
            press_event = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress, 
                                    local_pos,
                                    QtCore.Qt.LeftButton, 
                                    QtCore.Qt.LeftButton, 
                                    QtCore.Qt.NoModifier)
            QtWidgets.QApplication.sendEvent(widget, press_event)
            
            # Mouse release
            release_event = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonRelease, 
                                      local_pos,
                                      QtCore.Qt.LeftButton, 
                                      QtCore.Qt.LeftButton, 
                                      QtCore.Qt.NoModifier)
            QtWidgets.QApplication.sendEvent(widget, release_event)

    def run(self):
        # Usar QApplication.primaryScreen() en lugar de QDesktopWidget
        cursor_pos = QtGui.QCursor.pos()
        screen = QtWidgets.QApplication.primaryScreen()
        avail_space = screen.availableGeometry()
        
        posx = min(max(cursor_pos.x()-100, avail_space.left()), avail_space.right()-200)
        posy = min(max(cursor_pos.y()-80, avail_space.top()), avail_space.bottom()-150)
        
        self.move(QtCore.QPoint(posx, posy))
        self.text_edit.clear()
        self.texto_ingresado = ""
        self.activateWindow()  # Asegurar que la ventana está activa
        self.raise_()          # Traer al frente
        self.text_edit.setFocus()
        self.exec_()  # Usar exec_ en lugar de show() para que sea modal
        
        # Después de cerrar el diálogo, crear el nodo StickyNote si hay texto
        if self.texto_ingresado:
            # Simular click en el DAG para posicionar correctamente el nodo
            self.simulate_dag_click()
            
            # Crear el nodo StickyNote
            sticky = nuke.createNode("StickyNote")
            
            # Configurar el texto y formato
            sticky['label'].setValue(self.texto_ingresado)
            
            # Configurar propiedades visuales si es necesario
            sticky['note_font_size'].setValue(20)
            
            # Seleccionar el nodo para que el usuario pueda manipularlo fácilmente
            sticky['selected'].setValue(True)


# Variables globales
app = None
sticky_note = None

def main():
    """Función principal para mostrar el diálogo de StickyNote."""
    global app, sticky_note
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    sticky_note = StickyNote()
    sticky_note.run()

# Para uso en Nuke (no crea una nueva QApplication)
def run_sticky_note():
    """Mostrar el StickyNote dentro de Nuke"""
    global sticky_note
    if sticky_note is None:
        sticky_note = StickyNote()
    sticky_note.run()

# Ejecutar cuando se carga en Nuke
#run_sticky_note() 