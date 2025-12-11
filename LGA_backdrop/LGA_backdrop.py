"""
__________________________________________

  LGA_backdrop v0.81 | Lega Pugliese
  Backdrop personalizado con knobs modulares
__________________________________________

"""

import nuke
import nukescripts
import random
import colorsys
import gc
import weakref
from qt_compat import QtWidgets, QtGui, QtCore, QGuiApplication
from QtGui import QFontMetrics, QFont

# Importar modulos propios
import LGA_BD_knobs
import LGA_BD_callbacks
import LGA_BD_fit
import LGA_BD_config

# ===== CONTROL DE RECURSOS Y GESTIÓN DE MEMORIA =====
# Namespace único para evitar conflictos con otros scripts
LGA_BACKDROP_NAMESPACE = "LGA_Backdrop_v081"

# Control de instancias para evitar múltiples widgets
_BACKDROP_INSTANCES = weakref.WeakSet()
_BACKDROP_CLEANUP_ENABLED = True

def backdrop_cleanup_instances():
    """Limpia instancias anteriores de Backdrop"""
    if not _BACKDROP_CLEANUP_ENABLED:
        return
    
    instances_to_clean = list(_BACKDROP_INSTANCES)
    for instance in instances_to_clean:
        try:
            if hasattr(instance, '_cleanup_resources'):
                instance._cleanup_resources()
            if hasattr(instance, 'close'):
                instance.close()
        except (RuntimeError, ReferenceError):
            pass  # Instancia ya fue eliminada
    
    _BACKDROP_INSTANCES.clear()
    gc.collect()

# Variables configurables para el drop shadow - UNIQUE NAMES FOR BACKDROP
BACKDROP_SHADOW_BLUR_RADIUS_Backdrop = 25  # Radio de blur (más alto = más blureado)
BACKDROP_SHADOW_OPACITY_Backdrop = 60  # Opacidad (0-255, más alto = más opaco)
BACKDROP_SHADOW_OFFSET_X = 3  # Desplazamiento horizontal
BACKDROP_SHADOW_OFFSET_Y = 3  # Desplazamiento vertical
BACKDROP_SHADOW_MARGIN = 25  # Margen adicional para la sombra proyectada

# ===== INSTANCIACIÓN TARDÍA (LAZY INITIALIZATION) =====
# NO se crean widgets al importar el módulo para evitar crashes
# Los widgets se crean solo cuando se ejecuta show_text_dialog()

# Variable global para debug - UNIQUE NAME FOR BACKDROP
BACKDROP_DEBUG = False


def backdrop_debug_print(*message):
    """Debug print function with unique name for backdrop"""
    if BACKDROP_DEBUG:
        print("[BACKDROP DEBUG]", *message)


class BackdropNameDialog(QtWidgets.QDialog):
    def __init__(self):
        super(BackdropNameDialog, self).__init__()

        self.esc_exit = False
        self.user_text = ""
        self.drag_position = None  # Para el arrastre de la ventana
        
        # CONTROL DE RECURSOS: Registrar esta instancia
        _BACKDROP_INSTANCES.add(self)
        
        self.backdrop_setup_ui_BackDrop()
        self.backdrop_setup_connections_backdrop()

    def backdrop_setup_ui_BackDrop(self):
        """Configura la interfaz de usuario - UNIQUE NAME FOR BACKDROP"""
        # Configurar ventana contenedora transparente y siempre on top
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Window
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")

        # Layout principal con margenes para la sombra
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(
            BACKDROP_SHADOW_MARGIN,
            BACKDROP_SHADOW_MARGIN,
            BACKDROP_SHADOW_MARGIN,
            BACKDROP_SHADOW_MARGIN,
        )  # Margen para la sombra
        main_layout.setSpacing(0)

        # Frame principal que contendra todo el contenido
        self.main_frame = QtWidgets.QFrame()
        self.main_frame.setStyleSheet(
            """
            QFrame {
                background-color: #1f1f1f;
                border: 1px solid #555555;
                border-radius: 10px;
                color: #CCCCCC;
            }
        """
        )

        # Aplicar sombra al frame principal
        self.shadow = QtWidgets.QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(BACKDROP_SHADOW_BLUR_RADIUS_Backdrop)
        self.shadow.setColor(QtGui.QColor(0, 0, 0, BACKDROP_SHADOW_OPACITY_Backdrop))
        self.shadow.setOffset(BACKDROP_SHADOW_OFFSET_X, BACKDROP_SHADOW_OFFSET_Y)
        self.main_frame.setGraphicsEffect(self.shadow)

        # Layout del frame principal
        frame_layout = QtWidgets.QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Barra de título personalizada
        self.title_bar = QtWidgets.QLabel("Backdrop Name")
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet(
            """
            QLabel {
                background-color: #1f1f1f; 
                color: #cccccc; 
                padding-left: 10px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border: none;
                font-weight: bold;
            }
        """
        )
        self.title_bar.setAlignment(QtCore.Qt.AlignCenter)

        # Conectar eventos para arrastrar - UNIQUE NAMES FOR BACKDROP
        self.title_bar.mousePressEvent = self.backdrop_start_move_backdrop
        self.title_bar.mouseMoveEvent = self.backdrop_move_window_Backdrop
        self.title_bar.mouseReleaseEvent = self.backdrop_stop_move_Backdrop

        frame_layout.addWidget(self.title_bar)

        # Contenedor para el contenido con padding
        content_widget = QtWidgets.QWidget()
        content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #1f1f1f;
                border: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """
        )
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Campo de texto
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
                selection-background-color: #555555;
                selection-color: #FFFFFF;
            }
        """
        )
        # Configurar para 4 líneas de texto
        font_metrics = QtGui.QFontMetrics(self.text_edit.font())
        line_height = font_metrics.lineSpacing()
        self.text_edit.setFixedHeight(line_height * 4 + 20)  # 4 líneas + padding

        # Botones Cancel y OK
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(10)  # Espacio entre botones

        # Estilo común para ambos botones (grises)
        button_style = """
            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 5px;
                color: #CCCCCC;
                font-size: 12px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
        """

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.setFixedHeight(30)
        self.cancel_button.setStyleSheet(button_style)

        self.ok_button = QtWidgets.QPushButton("OK")
        self.ok_button.setFixedHeight(30)
        self.ok_button.setStyleSheet(button_style)

        # Crear tooltips personalizados - UNIQUE NAMES FOR BACKDROP
        self.tooltip_label = None
        self.cancel_button.enterEvent = lambda event: self.backdrop_show_custom_tooltip_Backdrop(
            "Esc", self.cancel_button
        )
        self.cancel_button.leaveEvent = (
            lambda event: self.backdrop_hide_custom_tooltip_Backdrop()
        )
        self.ok_button.enterEvent = lambda event: self.backdrop_show_custom_tooltip_Backdrop(
            "Ctrl+Enter", self.ok_button
        )
        self.ok_button.leaveEvent = lambda event: self.backdrop_hide_custom_tooltip_Backdrop()

        # Agregar botones con igual ancho (mitad cada uno)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.ok_button)

        # Agregar widgets al layout de contenido
        content_layout.addWidget(self.text_edit)
        content_layout.addSpacing(10)  # Espacio antes de los botones
        content_layout.addLayout(buttons_layout)

        # Agregar el contenedor al layout del frame
        frame_layout.addWidget(content_widget)

        # Agregar el frame principal al layout principal
        main_layout.addWidget(self.main_frame)

        self.setLayout(main_layout)
        self.adjustSize()  # Ajustar tamaño después de configurar todo

        # Hacer la ventana 40px más chica de ancho
        current_size = self.size()
        self.setFixedSize(current_size.width() - 40, current_size.height())

    def backdrop_start_move_backdrop(self, event):
        """Inicia el movimiento de la ventana - UNIQUE NAME FOR BACKDROP"""
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def backdrop_move_window_Backdrop(self, event):
        """Mueve la ventana durante el arrastre - UNIQUE NAME FOR BACKDROP"""
        if self.drag_position and event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def backdrop_stop_move_Backdrop(self, event):
        """Detiene el movimiento de la ventana - UNIQUE NAME FOR BACKDROP"""
        self.drag_position = None

    def backdrop_show_custom_tooltip_Backdrop(self, text, widget):
        """Muestra un tooltip personalizado - UNIQUE NAME FOR BACKDROP"""
        if self.tooltip_label:
            self.tooltip_label.close()

        self.tooltip_label = QtWidgets.QLabel(text, parent=self)
        self.tooltip_label.setWindowFlags(
            QtCore.Qt.Tool
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.tooltip_label.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.tooltip_label.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        try:
            self.destroyed.disconnect(self.backdrop_hide_custom_tooltip_Backdrop)
        except Exception:
            pass
        self.destroyed.connect(self.backdrop_hide_custom_tooltip_Backdrop)
        self.tooltip_label.setStyleSheet(
            """
            QLabel {
                background-color: #2a2a2a;
                color: #cccccc;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }
        """
        )

        # Posicionar el tooltip centrado encima del botón
        if widget:
            # Obtener la posición global del botón
            global_pos = widget.mapToGlobal(QtCore.QPoint(0, 0))
            # Centrar el tooltip horizontalmente respecto al botón
            button_width = widget.width()
            tooltip_width = self.tooltip_label.sizeHint().width()
            x_offset = (button_width - tooltip_width) // 2
            # Posicionar encima del botón
            self.tooltip_label.move(global_pos.x() + x_offset, global_pos.y() - 35)

        self.tooltip_label.show()

    def backdrop_hide_custom_tooltip_Backdrop(self):
        """Oculta el tooltip personalizado - UNIQUE NAME FOR BACKDROP"""
        if self.tooltip_label:
            self.tooltip_label.close()
            try:
                self.tooltip_label.deleteLater()
            except Exception:
                pass
            self.tooltip_label = None
        QtWidgets.QToolTip.hideText()
        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents, 50)

    def backdrop_setup_connections_backdrop(self):
        """Configura las conexiones de señales - UNIQUE NAME FOR BACKDROP"""
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.ok_button.clicked.connect(self.on_ok_clicked)

    def on_cancel_clicked(self):
        """Callback cuando se hace click en Cancel"""
        self.backdrop_hide_custom_tooltip_Backdrop()
        self.esc_exit = True
        self.reject()

    def on_ok_clicked(self):
        """Callback cuando se hace click en OK"""
        self.backdrop_hide_custom_tooltip_Backdrop()
        self.user_text = self.text_edit.toPlainText()
        self.accept()

    def keyPressEvent(self, event):
        """Maneja los eventos de teclado"""
        if event.key() == QtCore.Qt.Key_Escape:
            # ESC funciona como Cancel
            self.on_cancel_clicked()
        elif event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            # Ctrl+Enter funciona como OK
            if event.modifiers() & QtCore.Qt.ControlModifier:
                self.on_ok_clicked()
            else:
                # Enter normal solo inserta nueva línea
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Cierra y limpia tooltips persistentes"""
        try:
            self.backdrop_hide_custom_tooltip_Backdrop()
        except Exception:
            pass
        return super(BackdropNameDialog, self).closeEvent(event)

    def showEvent(self, event):
        """Se ejecuta cuando se muestra el diálogo"""
        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        self.text_edit.setFocus()
        self.text_edit.selectAll()

    def focusOutEvent(self, event):
        """Se ejecuta cuando la ventana pierde el foco - mantener siempre activa"""
        # Ignorar la pérdida de foco para mantener la ventana siempre visible
        super().focusOutEvent(event)
        # Reactivar la ventana después de un breve delay
        QtCore.QTimer.singleShot(50, self.reactivate_window)

    def reactivate_window(self):
        """Reactiva la ventana para mantenerla siempre on top"""
        if self.isVisible():
            self.activateWindow()
            self.raise_()

    def position_window_relative_to_cursor(self):
        """Posiciona la ventana respecto al cursor del mouse"""
        # Asegurarnos de que la ventana tenga el tamaño correcto
        self.adjustSize()
        window_width = self.width()
        window_height = self.height()

        # Obtener posición del cursor
        cursor_pos = QtGui.QCursor.pos()

        # Obtener geometría de la pantalla disponible
        screen = QGuiApplication.primaryScreen()
        if screen:
            avail_space = screen.availableGeometry(cursor_pos)
        else:
            # Fallback simple alrededor del cursor
            avail_space = QtCore.QRect(
                cursor_pos.x() - 400, cursor_pos.y() - 400, 800, 800
            )

        # Calcular posición centrada respecto al cursor
        posx = min(
            max(cursor_pos.x() - window_width // 2, avail_space.left()),
            avail_space.right() - window_width,
        )
        posy = min(
            max(cursor_pos.y() - window_height // 2, avail_space.top()),
            avail_space.bottom() - window_height,
        )

        self.move(QtCore.QPoint(posx, posy))

    def show_backdrop_dialog(self):
        """Ejecuta el diálogo - RENAMED from run() to avoid conflicts"""
        backdrop_debug_print("BackdropNameDialog.show_backdrop_dialog() called")

        # Posicionar la ventana respecto al cursor
        self.position_window_relative_to_cursor()

        # Mostrar el diálogo
        result = self.exec_()

        if result == QtWidgets.QDialog.Accepted:
            return self.esc_exit, self.user_text
        else:
            return self.esc_exit, None


def show_text_dialog():
    """
    Muestra el dialogo y retorna el resultado - USING RESOURCE CONTROL
    """
    backdrop_debug_print(
        "show_text_dialog() called - using resource control"
    )
    
    # CONTROL DE RECURSOS: Limpiar instancias anteriores
    backdrop_cleanup_instances()
    
    dialog = BackdropNameDialog()
    return dialog.show_backdrop_dialog()


def nodeIsInside(node, backdropNode):
    """
    Retorna True si el nodo esta dentro del backdrop
    """
    topLeftNode = [node.xpos(), node.ypos()]
    topLeftBackDrop = [backdropNode.xpos(), backdropNode.ypos()]
    bottomRightNode = [
        node.xpos() + node.screenWidth(),
        node.ypos() + node.screenHeight(),
    ]
    bottomRightBackdrop = [
        backdropNode.xpos() + backdropNode.screenWidth(),
        backdropNode.ypos() + backdropNode.screenHeight(),
    ]

    topLeft = (topLeftNode[0] >= topLeftBackDrop[0]) and (
        topLeftNode[1] >= topLeftBackDrop[1]
    )
    bottomRight = (bottomRightNode[0] <= bottomRightBackdrop[0]) and (
        bottomRightNode[1] <= bottomRightBackdrop[1]
    )

    return topLeft and bottomRight


def autoBackdrop():
    """
    Crea automaticamente un backdrop detras de los nodos seleccionados
    """
    backdrop_debug_print("autoBackdrop() called")

    # Obtener el texto del usuario usando el panel personalizado
    esc_exit, user_text = show_text_dialog()
    if esc_exit:
        backdrop_debug_print("User cancelled backdrop creation with ESC")
        return  # Si el usuario cancela con ESC, salir de la funcion
    if user_text is None:
        user_text = ""  # Si el usuario cancela, usar una cadena vacia

    backdrop_debug_print(f"User entered text: '{user_text}'")

    selNodes = nuke.selectedNodes()
    forced = False

    # Si no hay nada seleccionado, crear un nodo temporal
    if not selNodes:
        forced = True
        b = nuke.createNode("NoOp")
        selNodes.append(b)

    # Calcular limites para el backdrop
    bdX = min([node.xpos() for node in selNodes])
    bdY = min([node.ypos() for node in selNodes])
    bdW = max([node.xpos() + node.screenWidth() for node in selNodes]) - bdX
    bdH = max([node.ypos() + node.screenHeight() for node in selNodes]) - bdY

    zOrder = 0
    selectedBackdropNodes = nuke.selectedNodes("BackdropNode")

    # Si hay backdrops seleccionados, poner el nuevo inmediatamente detras del mas lejano
    if len(selectedBackdropNodes):
        zOrder = min([node["z_order"].getValue() for node in selectedBackdropNodes]) - 1
    else:
        # Si no hay backdrop en la seleccion, encontrar el backdrop mas cercano
        # si existe y poner el nuevo enfrente de el
        nonSelectedBackdropNodes = nuke.allNodes("BackdropNode")
        for nonBackdrop in selNodes:
            for backdrop in nonSelectedBackdropNodes:
                if nodeIsInside(nonBackdrop, backdrop):
                    zOrder = max(zOrder, backdrop["z_order"].getValue() + 1)

    # NUEVO: Evaluar si el nuevo backdrop contendra otros backdrops
    # y en caso afirmativo, asignar un Z mas bajo que el minimo de los contenidos
    allBackdropNodes = nuke.allNodes("BackdropNode")
    backdrops_contained = []

    # Crear los limites del nuevo backdrop temporalmente para la evaluacion
    new_backdrop_bounds = {
        "left": bdX,
        "top": bdY,
        "right": bdX + bdW,
        "bottom": bdY + bdH,
    }

    # Verificar que backdrops estarian contenidos dentro del nuevo backdrop
    for backdrop in allBackdropNodes:
        backdrop_bounds = {
            "left": backdrop.xpos(),
            "top": backdrop.ypos(),
            "right": backdrop.xpos() + backdrop.screenWidth(),
            "bottom": backdrop.ypos() + backdrop.screenHeight(),
        }

        # Verificar si este backdrop esta completamente dentro del nuevo backdrop
        if (
            backdrop_bounds["left"] >= new_backdrop_bounds["left"]
            and backdrop_bounds["top"] >= new_backdrop_bounds["top"]
            and backdrop_bounds["right"] <= new_backdrop_bounds["right"]
            and backdrop_bounds["bottom"] <= new_backdrop_bounds["bottom"]
        ):
            backdrops_contained.append(backdrop)

    # Si hay backdrops contenidos, asignar Z mas bajo que el minimo
    if backdrops_contained:
        min_contained_z = min(
            [backdrop["z_order"].getValue() for backdrop in backdrops_contained]
        )
        zOrder = min_contained_z - 1
        print(
            f"Backdrop will contain {len(backdrops_contained)} backdrops. Setting Z to {zOrder} (min contained Z was {min_contained_z})"
        )

    # Cargar valores por defecto desde configuración
    try:
        backdrop_defaults = LGA_BD_config.get_backdrop_defaults()
        note_font_size = backdrop_defaults["font_size"]
        default_font_name = backdrop_defaults["font_name"]
        default_bold = backdrop_defaults["bold"]
        default_italic = backdrop_defaults["italic"]
        default_align = backdrop_defaults["align"]
        margin_value = backdrop_defaults["margin"]
        default_appearance = backdrop_defaults["appearance"]
        default_border_width = backdrop_defaults["border_width"]
        print(f"Loaded backdrop defaults: {backdrop_defaults}")
    except Exception as e:
        print(f"Error loading backdrop defaults, using hardcoded values: {e}")
        # Usar valores hardcoded como fallback
        note_font_size = 42
        default_font_name = "Verdana"
        default_bold = False
        default_italic = False
        default_align = "left"
        margin_value = 50
        default_appearance = "Fill"
        default_border_width = 1.0

    # Calcular el tamaño adicional necesario para el texto
    extra_top = LGA_BD_fit.calculate_extra_top(user_text, note_font_size)

    # Calcular el ancho minimo necesario para el texto
    min_horizontal = LGA_BD_fit.calculate_min_horizontal(user_text, note_font_size)

    if margin_value < extra_top:
        top = -extra_top
    else:
        top = -margin_value

    bottom = margin_value
    left = -1 * margin_value

    # Ajustar para el ancho minimo del texto
    additional_width = max(0, min_horizontal - bdW)
    left_adjustment = additional_width / 2
    right_adjustment = additional_width / 2

    right = margin_value + right_adjustment
    left -= left_adjustment

    bdX += left
    bdY += top
    bdW += right - left
    bdH += bottom - top

    # Construir el valor de font con bold/italic
    font_value = default_font_name
    if default_bold:
        font_value += " Bold"
    if default_italic:
        font_value += " Italic"

    # Aplicar alignment al texto del label
    formatted_user_text = user_text
    if default_align == "center":
        formatted_user_text = '<div align="center">' + user_text + "</div>"
    elif default_align == "right":
        formatted_user_text = '<div align="right">' + user_text + "</div>"

    # Crear el backdrop
    n = nuke.nodes.BackdropNode(
        xpos=bdX,
        bdwidth=bdW,
        ypos=bdY,
        bdheight=bdH,
        tile_color=int((random.random() * (16 - 10))) + 10,
        note_font_size=note_font_size,
        note_font=font_value,
        z_order=zOrder,
        label=formatted_user_text,
        appearance=default_appearance,
        border_width=default_border_width,
    )

    # Agregar todos los knobs personalizados (pasar el alignment por defecto)
    LGA_BD_knobs.add_all_knobs(n, formatted_user_text, default_align)

    # IMPORTANTE: Sincronizar el slider zorder con el valor del z_order nativo después de crear los knobs
    if "zorder" in n.knobs():
        current_z_order = n["z_order"].getValue()
        n["zorder"].setValue(current_z_order)
        print(f"Sincronizado slider zorder con z_order nativo: {current_z_order}")

    # IMPORTANTE: Sincronizar el margin slider con el valor por defecto cargado
    if "margin_slider" in n.knobs():
        n["margin_slider"].setValue(margin_value)
        print(f"Sincronizado margin slider con valor por defecto: {margin_value}")

    # IMPORTANTE: Sincronizar el font size slider con el valor por defecto cargado
    if "lga_note_font_size" in n.knobs():
        n["lga_note_font_size"].setValue(note_font_size)
        print(f"Sincronizado font size slider con valor por defecto: {note_font_size}")

    # Configurar callbacks
    LGA_BD_callbacks.setup_callbacks(n)

    # Revertir a la seleccion previa
    n["selected"].setValue(False)
    if forced:
        nuke.delete(b)
    else:
        for node in selNodes:
            node["selected"].setValue(True)

    # Seleccionar el backdrop y mostrar sus propiedades
    n.setSelected(True)
    nuke.show(n)

    return n
