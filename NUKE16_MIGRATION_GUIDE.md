# Guía de Migración: Nuke 15 → Nuke 16

## Resumen Ejecutivo

Nuke 16 introduce un cambio significativo en su arquitectura de interfaz: la migración de **PySide2 a PySide6**. Este cambio, aunque necesario para mantener la modernidad y rendimiento del software, requiere actualizaciones en todos los scripts Python que utilicen PySide para interfaces gráficas.

**Fecha de lanzamiento**: Febrero 2025  
**Impacto**: Todos los scripts que usen PySide2 requieren modificaciones  
**Complejidad**: Media-Alta (dependiendo de la complejidad del script)

---

## 🎯 Cambios Principales

### 1. Migración PySide2 → PySide6

Nuke 16 actualiza directamente de PySide2 (introducido en Nuke 11) a PySide6, siguiendo la evolución natural de Qt. Esta actualización trae mejoras significativas en rendimiento pero también cambios breaking en la API.

**¿Por qué el cambio?**
- PySide2 estaba basado en Qt5 (obsoleto)
- PySide6 está basado en Qt6 (actual y mantenido)
- Mejor rendimiento y soporte moderno

### 2. Impacto en Scripts Existentes

Si tu script usa cualquiera de estas librerías, necesita actualización:
- PySide2
- shiboken2
- Interfaces que acceden al DAG widget
- Cualquier funcionalidad Qt/PySide

---

## 🔄 Cambios Técnicos Detallados

### Renombramiento de Módulos PySide6

#### Imports Básicos
```python
# ❌ Nuke 15 (PySide2)
from PySide2.QtWidgets import QApplication, QWidget, QPushButton
from PySide2.QtGui import QPixmap, QIcon
from PySide2.QtCore import Qt, QTimer

# ✅ Nuke 16 (PySide6)
from PySide6.QtWidgets import QApplication, QWidget, QPushButton
from PySide6.QtGui import QPixmap, QIcon, QGuiApplication
from PySide6.QtCore import Qt, QTimer
```

#### Cambios Específicos por Módulo

| Módulo | Nuke 15 (PySide2) | Nuke 16 (PySide6) | Notas |
|--------|------------------|-------------------|-------|
| **QtWidgets** | `PySide2.QtWidgets` | `PySide6.QtWidgets` | Sin cambios mayores |
| **QtGui** | `PySide2.QtGui` | `PySide6.QtGui` | + `QGuiApplication` |
| **QtCore** | `PySide2.QtCore` | `PySide6.QtCore` | Sin cambios mayores |
| **QtMultimedia** | `PySide2.QtMultimedia` | `PySide6.QtMultimedia` | Cambios en audio |

### Shiboken Update

```python
# ❌ Viejo
import shiboken2
wrapped_pointer = shiboken2.wrapInstance(long_ptr, QSomeClass)

# ✅ Nuevo
import shiboken6
wrapped_pointer = shiboken6.wrapInstance(long_ptr, QSomeClass)
```

### Cambios en Enums y Constantes

#### ❌ Antes (PySide2)
```python
button = QtWidgets.QPushButton()
# Las constantes estaban disponibles directamente en las clases
button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
```

#### ✅ Después (PySide6)
```python
button = QtWidgets.QPushButton()
# Las constantes ya no están disponibles en instancias de clase
sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
button.setSizePolicy(sizePolicy)
```

### Cambios en QAction

```python
# ❌ PySide2 - QAction en QtWidgets
from PySide2.QtWidgets import QAction

# ✅ PySide6 - QAction vuelve a QtGui
from PySide6.QtGui import QAction

# ⚠️  PySide2 tenía QAction en QtWidgets (cambio temporal)
# ✅ PySide6 lo regresa a QtGui donde pertenece originalmente
```

### QPixmap.fromImage Changes

```python
# ❌ Viejo - aceptaba string path
pixmap = QtGui.QPixmap.fromImage("path/to/image.png")

# ✅ Nuevo - requiere QImage primero
image = QtGui.QImage("path/to/image.png")
pixmap = QtGui.QPixmap.fromImage(image)
```

### QDesktopWidget Deprecado

```python
# ❌ Obsoleto en Qt6/PySide6
desktop = QtWidgets.QDesktopWidget()
screen_size = desktop.screenGeometry()

# ✅ Nuevo enfoque
app = QtGui.QGuiApplication.instance()
screen = app.primaryScreen()
screen_size = screen.geometry()
```

### Reproducción de Audio

```python
# ❌ Viejo - QSound ya no existe
from PySide2.QtMultimedia import QSound
QSound.play("sound.wav")

# ✅ Nuevo - Usar QMediaPlayer + QAudioOutput
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

player = QMediaPlayer()
audioOutput = QAudioOutput()
player.setAudioOutput(audioOutput)
player.setSource(QUrl.fromLocalFile("sound.wav"))
player.play()
```

---

## 🏗️ Estrategias de Compatibilidad Cruzada

### Opción 1: Qt.py (Recomendado) ⭐

Qt.py es una librería de abstracción que unifica las APIs de Qt/PySide a través de versiones.

```python
# Instalar: pip install Qt.py
from qtpy.QtWidgets import QApplication, QWidget, QPushButton
from qtpy.QtGui import QPixmap, QIcon
from qtpy.QtCore import Qt, QTimer

# Código funciona en Nuke 11-15 (PySide2) y 16+ (PySide6)
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

widget = QWidget()
layout = QVBoxLayout(widget)
button = QPushButton("Hola Mundo")
layout.addWidget(button)

widget.show()
```

**Ventajas:**
- ✅ Compatibilidad total entre versiones
- ✅ Mantiene APIs consistentes
- ✅ Abstracción automática de diferencias
- ✅ Comunidad activa y mantenido

**Limitaciones:**
- Solo expone APIs comunes entre versiones Qt4/5/6
- APIs específicas de Qt6 no disponibles

### Opción 2: Detección de Versión de Nuke

```python
import nuke

# Estrategia basada en versión de Nuke
if nuke.NUKE_VERSION_MAJOR >= 16:
    # PySide6 imports
    from PySide6.QtWidgets import QApplication, QWidget
    from PySide6.QtGui import QPixmap
    from PySide6.QtCore import Qt
else:
    # PySide2 imports
    from PySide2.QtWidgets import QApplication, QWidget
    from PySide2.QtGui import QPixmap
    from PySide2.QtCore import Qt

# Resto del código igual para ambas versiones
```

### Opción 3: Try/Except

```python
try:
    # Intentar PySide6 primero (Nuke 16+)
    from PySide6.QtWidgets import QApplication, QWidget
    from PySide6.QtGui import QPixmap
    PYSIDE_VERSION = 6
except ImportError:
    # Fallback a PySide2 (Nuke 11-15)
    from PySide2.QtWidgets import QApplication, QWidget
    from PySide2.QtGui import QPixmap
    PYSIDE_VERSION = 2

# Usar PYSIDE_VERSION para lógica condicional si es necesario
```

### Opción 4: Imports Dinámicos

```python
import importlib

def get_pyside_module(module_name):
    """Obtiene el módulo PySide correcto según la versión"""
    try:
        return importlib.import_module(f'PySide6.{module_name}')
    except ImportError:
        return importlib.import_module(f'PySide2.{module_name}')

# Uso
QtWidgets = get_pyside_module('QtWidgets')
QtGui = get_pyside_module('QtGui')
QtCore = get_pyside_module('QtCore')

# Ahora puedes usar QtWidgets.QApplication, etc.
```

---

## 🎨 Cambios en DAG Widget

### Contexto del Cambio

En Nuke 16, el DAG (Node Graph) deja de ser un widget OpenGL y se convierte en un QWidget estándar debido a la depreciación de OpenGL en Qt6.

### Impacto en Scripts

```python
# ❌ Código que ya NO funciona en Nuke 16
def get_dag_widget():
    """Ya no funciona - el DAG ya no es OpenGL"""
    for widget in QtWidgets.QApplication.allWidgets():
        if hasattr(widget, 'getBuffer'):  # Método OpenGL
            return widget
    return None

# ❌ Acceso al buffer OpenGL
dag_buffer = dag_widget.getBuffer()  # Ya no disponible
```

### Soluciones

#### Enfoque 1: Usar Nombres de Widget (Recomendado)

```python
def find_dag_widget():
    """Encuentra widgets DAG por nombre (funciona en Nuke 16)"""
    dag_widgets = []

    def find_dag_recursive(widget):
        # DAG principal
        if widget.objectName() == "DAG":
            dag_widgets.append(widget)

        # DAGs de grupos
        if widget.objectName().startswith("DAG."):
            dag_widgets.append(widget)

        # Recursión
        for child in widget.children():
            if isinstance(child, QtWidgets.QWidget):
                find_dag_recursive(child)

    # Buscar desde la ventana principal
    main_window = get_main_window()
    find_dag_recursive(main_window)

    return dag_widgets

def get_main_window():
    """Obtiene la ventana principal de Nuke"""
    app = QtWidgets.QApplication.instance()
    for widget in app.topLevelWidgets():
        if widget.objectName() == "Foundry::UI::MainWindow":
            return widget
    return None
```

#### Enfoque 2: Screenshot del DAG

```python
def capture_dag_screenshot():
    """Captura screenshot del DAG widget"""
    dag_widget = find_dag_widget()[0]  # Primer DAG encontrado

    if dag_widget:
        # Crear pixmap del tamaño del widget
        pixmap = QtGui.QPixmap(dag_widget.size())
        dag_widget.render(pixmap)

        # Guardar o procesar
        pixmap.save("/path/to/dag_screenshot.png")
        return pixmap

    return None
```

#### Limitaciones Conocidas

- **Buffer OpenGL**: Ya no accesible directamente
- **Renderizado**: Puede haber diferencias visuales menores
- **Performance**: El nuevo QWidget puede ser ligeramente diferente en performance

---

## 🛠️ Herramientas y Scripts Actualizados

### Herramientas de Comunidad Actualizadas

| Herramienta | Autor | Estado | Enlace |
|-------------|-------|--------|--------|
| **hortcuteditor-nuke** | Ben Dicken | ✅ Actualizado | [GitHub](https://github.com/boyliang/ShortcutEditor) |
| **nuke_nodegraph_util** | Erwan Leroy | ✅ Actualizado | [GitHub](https://github.com/erwanleroy/nuke_nodegraph_util) |
| **tabtabtab-nuke** | Charles Taylor | ✅ Actualizado | [GitHub](https://github.com/christlett/tabtabtab-nuke) |
| **nuke_dag_capture** | Erwan Leroy | ⚠️ Parcialmente | [GitHub](https://github.com/erwanleroy/nuke_dag_capture) |

### Scripts de Ejemplo Actualizados

#### Ejemplo Completo: Panel Básico

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ejemplo de panel compatible con Nuke 15/16
Usa Qt.py para compatibilidad cruzada
"""

try:
    from qtpy.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit, QApplication)
    from qtpy.QtCore import Qt, Signal
    from qtpy.QtGui import QIcon
    QT_PY_AVAILABLE = True
except ImportError:
    QT_PY_AVAILABLE = False

# Fallback si no hay Qt.py
if not QT_PY_AVAILABLE:
    import nuke
    if nuke.NUKE_VERSION_MAJOR >= 16:
        from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                      QPushButton, QLabel, QLineEdit, QApplication)
        from PySide6.QtCore import Qt, Signal
        from PySide6.QtGui import QIcon
    else:
        from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                      QPushButton, QLabel, QLineEdit, QApplication)
        from PySide2.QtCore import Qt, Signal
        from PySide2.QtGui import QIcon

class MiPanel(QWidget):
    """Panel de ejemplo compatible con Nuke 15/16"""

    # Señales
    value_changed = Signal(str)

    def __init__(self, parent=None):
        super(MiPanel, self).__init__(parent)

        self.setWindowTitle("Mi Panel Nuke 15/16")
        self.setMinimumWidth(300)

        # Layout principal
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Panel Compatible")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Valor:"))

        self.input_field = QLineEdit()
        self.input_field.textChanged.connect(self._on_text_changed)
        input_layout.addWidget(self.input_field)

        layout.addLayout(input_layout)

        # Botones
        button_layout = QHBoxLayout()

        self.apply_btn = QPushButton("Aplicar")
        self.apply_btn.clicked.connect(self._on_apply)
        button_layout.addWidget(self.apply_btn)

        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        # Espaciador
        layout.addStretch()

    def _on_text_changed(self, text):
        """Maneja cambio de texto"""
        self.value_changed.emit(text)

    def _on_apply(self):
        """Aplica el valor"""
        value = self.input_field.text()
        print(f"Aplicando valor: {value}")
        nuke.message(f"Valor aplicado: {value}")

def mostrar_panel():
    """Función principal para mostrar el panel"""
    # Obtener instancia de aplicación
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    # Crear y mostrar panel
    panel = MiPanel()
    panel.show()

    # Centrar en pantalla (compatible con PySide6)
    if hasattr(app, 'primaryScreen'):
        # PySide6
        screen = app.primaryScreen()
        screen_geometry = screen.geometry()
    else:
        # PySide2
        desktop = app.desktop()
        screen_geometry = desktop.screenGeometry()

    panel.move(
        (screen_geometry.width() - panel.width()) // 2,
        (screen_geometry.height() - panel.height()) // 2
    )

    return panel

# Ejecutar si se llama directamente
if __name__ == "__main__":
    mostrar_panel()
```

---

## 🔍 Checklist de Migración

### Pre-Migración
- [ ] **Backup**: Crear backup completo de scripts
- [ ] **Inventario**: Listar todos los scripts que usan PySide/PyQt
- [ ] **Testing**: Verificar que funcionan en Nuke 15
- [ ] **Dependencias**: Instalar Qt.py si es posible

### Durante la Migración
- [ ] **Imports**: Actualizar todos los imports PySide2 → PySide6
- [ ] **Enums**: Cambiar acceso a constantes de clase
- [ ] **DAG Widget**: Reemplazar código OpenGL si es necesario
- [ ] **Shiboken**: Actualizar shiboken2 → shiboken6
- [ ] **Multimedia**: Actualizar reproducción de audio

### Post-Migración
- [ ] **Testing Nuke 16**: Verificar funcionamiento en Nuke 16
- [ ] **Testing Nuke 15**: Verificar compatibilidad backward
- [ ] **Performance**: Comparar rendimiento
- [ ] **UI**: Verificar apariencia y comportamiento
- [ ] **Documentación**: Actualizar documentación del script

---

## ⚠️ Problemas Conocidos y Soluciones

### Problema 1: Centrado de Ventanas
```python
# ❌ No funciona en PySide6
desktop = QtWidgets.QDesktopWidget()
screen_geometry = desktop.screenGeometry()

# ✅ Solución
app = QtGui.QGuiApplication.instance()
screen = app.primaryScreen()
screen_geometry = screen.geometry()
```

### Problema 2: QAction Location
```python
# ❌ PySide2 tenía QAction en QtWidgets
from PySide2.QtWidgets import QAction

# ✅ PySide6 lo regresa a QtGui
from PySide6.QtGui import QAction
```

### Problema 3: QSound Deprecado
```python
# ❌ QSound ya no existe
from PySide6.QtMultimedia import QSound  # ImportError

# ✅ Usar QMediaPlayer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
```

### Problema 4: QWidget.findChild Type Hints
```python
# En PySide6, findChild requiere type hints más específicos
button = widget.findChild(QtWidgets.QPushButton, "myButton")
# En lugar de solo el nombre
```

---

## 📚 Recursos y Documentación

### Documentación Oficial

1. **Release Notes Nuke 16** (Learn Foundry)
   - URL: https://learn.foundry.com/content/release-notes-for-nuke-and-hiero-16-0v3
   - Contenido: Notas oficiales de la versión 16.0v3

2. **Qt6 Migration Guide** (Qt Project)
   - URL: https://doc.qt.io/qt-6/portingguide.html
   - Contenido: Guía oficial de migración Qt5 → Qt6

3. **PySide6 Documentation**
   - URL: https://doc.qt.io/qtforpython/
   - Contenido: Documentación completa de PySide6

### Artículos y Tutoriales

4. **Updating Python Scripts for Nuke 16 and PySide6** (Erwan Leroy)
   - URL: https://erwanleroy.com/updating-your-python-scripts-for-nuke-16-and-pyside6/
   - Contenido: **Artículo principal usado como base para esta guía**

5. **Qt.py Documentation**
   - URL: https://github.com/mottosso/Qt.py
   - Contenido: Librería de compatibilidad Qt/PySide

### Comunidades y Foros

6. **Nukepedia Forum**
   - URL: https://www.nukepedia.com/
   - Contenido: Comunidad de scripts y herramientas Nuke

7. **Foundry Community**
   - URL: https://community.foundry.com/
   - Contenido: Foro oficial de soporte Foundry

8. **Reddit r/NukeVFX**
   - URL: https://www.reddit.com/r/NukeVFX/
   - Contenido: Comunidad Reddit de Nuke

### Herramientas Actualizadas

9. **hortcuteditor-nuke** (Ben Dicken)
   - URL: https://github.com/boyliang/ShortcutEditor

10. **nuke_nodegraph_util** (Erwan Leroy)
    - URL: https://github.com/erwanleroy/nuke_nodegraph_util

11. **tabtabtab-nuke** (Charles Taylor)
    - URL: https://github.com/christlett/tabtabtab-nuke

---

## 🎯 Recomendaciones Finales

### Para Desarrolladores Individuales
1. **Usar Qt.py** para nuevos proyectos
2. Mantener compatibilidad backward cuando sea posible
3. Documentar cambios en comentarios del código

### Para Estudios/Pipelines
1. **Planificar migración** con tiempo suficiente
2. **Testing exhaustivo** en entornos de desarrollo
3. **Actualizar gradualmente** equipos de trabajo
4. **Documentar cambios** en wiki interna

### Mejores Prácticas
- ✅ Usar control de versiones (Git)
- ✅ Escribir tests automatizados
- ✅ Documentar dependencias y compatibilidad
- ✅ Mantener versiones backward compatibles
- ✅ Usar manejo de errores robusto

---

## 🤝 Contribución

Esta guía se basa principalmente en el artículo "Updating Your Python Scripts for Nuke 16 and PySide6" de Erwan Leroy. Si encuentras errores, mejoras o información adicional, por favor contribuye actualizando este documento.

**Última actualización**: Diciembre 2025  
**Versión Nuke**: 16.0v3  
**Autor**: Basado en investigación y artículo de Erwan Leroy

---

*Recuerda: La migración a Nuke 16 es inevitable. Mejor prepararse ahora que esperar a que sea urgente.*
