"""
__________________________________________

  LGA Layout ToolPack v2.5 | Lega
__________________________________________

"""

import nuke
import nukescripts
import importlib
import sys
import os
import gc
import weakref
from collections import OrderedDict


# Importar iconos de la carpeta icons
def _get_icon(name):
    icons_root = os.path.join(os.path.dirname(__file__), "icons")
    path = os.path.join(icons_root, name) + ".png"
    return path.replace("\\", "/")


# ===== GESTIÓN DE MEMORIA MEJORADA =====
# Configuración para evitar errores de "bad allocation"
MAX_CACHED_MODULES = 3  # Reducir cache para evitar problemas de memoria
ENABLE_AUTO_CLEANUP = True  # Activar limpieza automática
ENABLE_MEMORY_MONITORING = True  # Activar monitoreo de memoria
ENABLE_AGGRESSIVE_CLEANUP = False  # Desactivar limpieza agresiva que causa problemas


class MemoryManager:
    """Gestor de memoria para evitar bad allocation errors"""

    def __init__(self):
        self.module_cache = OrderedDict()
        self.weak_refs = {}
        self.problematic_modules = {
            "LGA_StickyNote",
            "LGA_NodeLabel",
            "LGA_backdrop",
        }  # Módulos que causan conflictos

    def cleanup_old_modules(self):
        """Limpia módulos antiguos del cache"""
        if not ENABLE_AUTO_CLEANUP:
            return

        while len(self.module_cache) > MAX_CACHED_MODULES:
            oldest_key = next(iter(self.module_cache))
            removed_module = self.module_cache.pop(oldest_key)
            if ENABLE_MEMORY_MONITORING:
                print(f"[MEMORY] Limpiando módulo del cache: {oldest_key}")
            del removed_module

        # Forzar garbage collection solo si es necesario
        if len(self.module_cache) > MAX_CACHED_MODULES - 1:
            gc.collect()

    def register_module(self, module_name, module_obj):
        """Registra un módulo en el cache con gestión de memoria"""
        if module_obj is None:
            return

        # Limpiar módulos antiguos primero
        self.cleanup_old_modules()

        # Agregar el nuevo módulo
        self.module_cache[module_name] = module_obj

        # Crear weak reference para monitoreo
        if ENABLE_MEMORY_MONITORING:
            self.weak_refs[module_name] = weakref.ref(module_obj)
            print(
                f"[MEMORY] Módulo registrado: {module_name} (Cache: {len(self.module_cache)}/{MAX_CACHED_MODULES})"
            )

    def get_module(self, module_name):
        """Obtiene un módulo del cache"""
        cached_module = self.module_cache.get(module_name)
        if cached_module is not None and ENABLE_MEMORY_MONITORING:
            print(f"[MEMORY] Usando módulo desde cache: {module_name}")
        return cached_module

    def clear_problematic_modules(self):
        """Limpia solo los módulos problemáticos"""
        if ENABLE_MEMORY_MONITORING:
            print("[MEMORY] Limpiando solo módulos problemáticos...")

        for module_name in list(self.module_cache.keys()):
            if module_name in self.problematic_modules:
                removed_module = self.module_cache.pop(module_name)
                if ENABLE_MEMORY_MONITORING:
                    print(f"[MEMORY] Limpiando módulo problemático: {module_name}")
                del removed_module

        # Limpiar weak references
        for module_name in self.problematic_modules:
            if module_name in self.weak_refs:
                del self.weak_refs[module_name]

        gc.collect()

    def clear_all(self):
        """Limpia todo el cache de memoria"""
        if ENABLE_MEMORY_MONITORING:
            print(
                f"[MEMORY] Limpiando todo el cache ({len(self.module_cache)} módulos)"
            )
        self.module_cache.clear()
        self.weak_refs.clear()
        gc.collect()


# Instancia global del gestor de memoria
memory_manager = MemoryManager()


# ===== ENCAPSULACIÓN CON GESTIÓN DE MEMORIA MEJORADA =====
class ModuleNamespace:
    """Clase para encapsular módulos con gestión de memoria mejorada"""

    def __init__(self, module_name, plugin_path=None):
        self.module_name = module_name
        self.plugin_path = plugin_path
        self._module = None
        self._loaded = False
        self._loading = False  # Flag para evitar cargas concurrentes

    def _load_module(self):
        """Carga el módulo con gestión de memoria mejorada"""
        if self._loading:
            print(
                f"[MEMORY WARNING] Módulo {self.module_name} ya está cargándose, evitando carga concurrente"
            )
            return None

        # Verificar si está en cache primero
        cached_module = memory_manager.get_module(self.module_name)
        if cached_module is not None:
            self._module = cached_module
            self._loaded = True
            return self._module

        # Si ya está cargado y es válido, devolverlo
        if self._loaded and self._module is not None:
            return self._module

        self._loading = True

        try:
            # Limpiar memoria antes de cargar SOLO si es necesario
            if (
                ENABLE_AUTO_CLEANUP
                and self.module_name in memory_manager.problematic_modules
            ):
                memory_manager.clear_problematic_modules()

            # Agregar path si es necesario
            if self.plugin_path:
                abs_plugin_path = os.path.abspath(self.plugin_path)
                if abs_plugin_path not in sys.path:
                    sys.path.insert(0, abs_plugin_path)
                    nuke.pluginAddPath(abs_plugin_path)

            # NUEVO ENFOQUE: No usar reload(), siempre importar fresh
            # Esto evita el error "reload() argument must be a module"
            if self.module_name in sys.modules:
                # En lugar de reload, eliminar del cache de Python y reimportar
                if ENABLE_MEMORY_MONITORING:
                    print(
                        f"[MEMORY] Eliminando módulo de sys.modules: {self.module_name}"
                    )
                del sys.modules[self.module_name]

            # Importar el módulo fresh
            self._module = importlib.import_module(self.module_name)

            # Registrar en el gestor de memoria
            memory_manager.register_module(self.module_name, self._module)

            self._loaded = True
            if ENABLE_MEMORY_MONITORING:
                print(f"[MEMORY] Módulo '{self.module_name}' cargado exitosamente")

            return self._module

        except Exception as e:
            print(f"[MEMORY ERROR] Error cargando módulo '{self.module_name}': {e}")
            # En caso de error, intentar cargar sin eliminar de sys.modules
            try:
                if self.module_name in sys.modules:
                    self._module = sys.modules[self.module_name]
                    if ENABLE_MEMORY_MONITORING:
                        print(
                            f"[MEMORY] Usando módulo existente de sys.modules: {self.module_name}"
                        )
                    return self._module
            except:
                pass
            return None
        finally:
            self._loading = False

    def get_function(self, function_name):
        """Obtiene una función del módulo con manejo de errores mejorado"""
        try:
            module = self._load_module()
            if module and hasattr(module, function_name):
                return getattr(module, function_name)
            else:
                print(
                    f"[MEMORY ERROR] Función '{function_name}' no encontrada en módulo '{self.module_name}'"
                )
                return None
        except Exception as e:
            print(f"[MEMORY ERROR] Error obteniendo función '{function_name}': {e}")
            return None

    def call_function(self, function_name, *args, **kwargs):
        """Llama a una función con manejo de memoria mejorado"""
        try:
            func = self.get_function(function_name)
            if func:
                result = func(*args, **kwargs)
                return result
            return None
        except Exception as e:
            print(f"[MEMORY ERROR] Error ejecutando función '{function_name}': {e}")
            return None

    def cleanup(self):
        """Limpia el módulo de memoria de forma segura"""
        if ENABLE_AGGRESSIVE_CLEANUP:
            # Solo hacer cleanup agresivo si está habilitado
            if self._module is not None:
                if hasattr(self._module, "__dict__"):
                    self._module.__dict__.clear()
                self._module = None
            self._loaded = False
            if ENABLE_MEMORY_MONITORING:
                print(f"[MEMORY] Módulo '{self.module_name}' limpiado de memoria")
        else:
            # Cleanup suave - solo marcar como no cargado
            self._loaded = False
            if ENABLE_MEMORY_MONITORING:
                print(f"[MEMORY] Módulo '{self.module_name}' marcado para recarga")


# ===== FUNCIÓN DE LIMPIEZA GLOBAL MEJORADA =====
def cleanup_all_modules():
    """Limpia todos los módulos y libera memoria de forma segura"""
    print("[MEMORY] Iniciando limpieza global de memoria...")

    # Solo limpiar módulos problemáticos, no todos
    memory_manager.clear_problematic_modules()

    # Limpiar solo los namespaces problemáticos
    problematic_namespaces = [sticky_note_ns, node_label_ns, lga_backdrop_ns]

    for namespace in problematic_namespaces:
        try:
            namespace.cleanup()
        except Exception as e:
            print(f"[MEMORY ERROR] Error limpiando namespace: {e}")

    # Forzar garbage collection una sola vez
    gc.collect()

    print("[MEMORY] Limpieza global completada")


def cleanup_specific_module(module_name):
    """Limpia un módulo específico"""
    print(f"[MEMORY] Limpiando módulo específico: {module_name}")

    # Limpiar del cache
    if module_name in memory_manager.module_cache:
        removed_module = memory_manager.module_cache.pop(module_name)
        del removed_module

    # Limpiar weak reference
    if module_name in memory_manager.weak_refs:
        del memory_manager.weak_refs[module_name]

    gc.collect()
    print(f"[MEMORY] Módulo {module_name} limpiado")


# ===== INSTANCIAS DE NAMESPACES CON GESTIÓN DE MEMORIA =====
# Cada módulo problemático tendrá su propio namespace aislado con gestión de memoria

# Módulos básicos
dots_ns = ModuleNamespace("Dots")
dots_after_ns = ModuleNamespace("LGA_dotsAfter")
script_checker_ns = ModuleNamespace("LGA_scriptChecker")

# Módulos problemáticos que causan conflictos (con gestión de memoria especial)
sticky_note_ns = ModuleNamespace("LGA_StickyNote")
node_label_ns = ModuleNamespace("LGA_NodeLabel")

# Backdrop modules con paths específicos
backdrop_path = os.path.join(os.path.dirname(__file__), "LGA_backdrop")
lga_backdrop_ns = ModuleNamespace("LGA_backdrop", backdrop_path)
lga_backdrop_replacer_ns = ModuleNamespace("LGA_backdropReplacer")

oz_backdrop_path = os.path.join(os.path.dirname(__file__), "oz_backdrop")
oz_backdrop_ns = ModuleNamespace("oz_backdrop", oz_backdrop_path)
oz_backdrop_replacer_ns = ModuleNamespace("LGA_oz_backdropReplacer")

# Otros módulos
select_nodes_ns = ModuleNamespace("LGA_selectNodes")
align_nodes_ns = ModuleNamespace("LGA_alignNodes_Backdrops")
distribute_nodes_ns = ModuleNamespace("LGA_distributeNodes_Backdrops")
arrange_nodes_ns = ModuleNamespace("LGA_arrangeNodes")
scale_widget_ns = ModuleNamespace("scale_widget")

# Módulos de movimiento de nodos
push_nodes_ns = ModuleNamespace("nuke_move_nodes.push_nodes")
pull_nodes_ns = ModuleNamespace("nuke_move_nodes.pull_nodes")

# Easy Navigate modules
km_nodegraph_path = os.path.join(os.path.dirname(__file__), "Km_NodeGraphEN")
easy_navigate_ns = ModuleNamespace("Km_NodeGraph_Easy_Navigate", km_nodegraph_path)
model_ns = ModuleNamespace("model", km_nodegraph_path)

# Zoom module
zoom_ns = ModuleNamespace("LGA_zoom")

# ===== FUNCIONES WRAPPER CON GESTIÓN DE MEMORIA =====
# Estas funciones usan los namespaces con gestión de memoria mejorada


def _run_dots():
    """Ejecuta Dots con gestión de memoria"""
    return dots_ns.call_function("Dots")


def _run_dots_after_left():
    """Ejecuta dotsAfter left con gestión de memoria"""
    return dots_after_ns.call_function("dotsAfter", direction="l")


def _run_dots_after_left_plus():
    """Ejecuta dotsAfter left+ con gestión de memoria"""
    return dots_after_ns.call_function("dotsAfter", direction="ll")


def _run_dots_after_right():
    """Ejecuta dotsAfter right con gestión de memoria"""
    return dots_after_ns.call_function("dotsAfter", direction="r")


def _run_dots_after_right_plus():
    """Ejecuta dotsAfter right+ con gestión de memoria"""
    return dots_after_ns.call_function("dotsAfter", direction="rr")


def _run_script_checker():
    """Ejecuta scriptChecker con gestión de memoria"""
    return script_checker_ns.call_function("main")


def _run_sticky_note():
    """Ejecuta StickyNote con gestión de memoria especial"""
    print("[MEMORY] Ejecutando StickyNote con gestión de memoria especial...")
    # Limpiar solo el módulo específico si es necesario
    cleanup_specific_module("LGA_StickyNote")
    return sticky_note_ns.call_function("run_sticky_note_editor")


def _run_lga_backdrop():
    """Ejecuta LGA_backdrop con gestión de memoria"""
    print("[MEMORY] Ejecutando LGA_backdrop con gestión de memoria especial...")
    # Limpiar solo el módulo específico si es necesario
    cleanup_specific_module("LGA_backdrop")
    return lga_backdrop_ns.call_function("autoBackdrop")


def _run_lga_backdrop_replacer():
    """Ejecuta LGA_backdropReplacer con gestión de memoria"""
    return lga_backdrop_replacer_ns.call_function("replace_with_lga_backdrop")


def _run_oz_backdrop():
    """Ejecuta oz_backdrop con gestión de memoria"""
    return oz_backdrop_ns.call_function("autoBackdrop")


def _run_oz_backdrop_replacer():
    """Ejecuta oz_backdropReplacer con gestión de memoria"""
    return oz_backdrop_replacer_ns.call_function("replace_with_oz_backdrop")


def _run_node_label():
    """Ejecuta NodeLabel con gestión de memoria especial"""
    print("[MEMORY] Ejecutando NodeLabel con gestión de memoria especial...")
    # Limpiar solo el módulo específico si es necesario
    cleanup_specific_module("LGA_NodeLabel")
    return node_label_ns.call_function("run_node_label_editor")


def _run_select_nodes_left():
    """Ejecuta selectNodes left con gestión de memoria"""
    return select_nodes_ns.call_function("selectNodes", "l")


def _run_select_nodes_right():
    """Ejecuta selectNodes right con gestión de memoria"""
    return select_nodes_ns.call_function("selectNodes", "r")


def _run_select_nodes_top():
    """Ejecuta selectNodes top con gestión de memoria"""
    return select_nodes_ns.call_function("selectNodes", "t")


def _run_select_nodes_bottom():
    """Ejecuta selectNodes bottom con gestión de memoria"""
    return select_nodes_ns.call_function("selectNodes", "b")


def _run_select_connected_nodes_left():
    """Ejecuta selectConnectedNodes left con gestión de memoria"""
    return select_nodes_ns.call_function("selectConnectedNodes", "l")


def _run_select_connected_nodes_right():
    """Ejecuta selectConnectedNodes right con gestión de memoria"""
    return select_nodes_ns.call_function("selectConnectedNodes", "r")


def _run_select_connected_nodes_top():
    """Ejecuta selectConnectedNodes top con gestión de memoria"""
    return select_nodes_ns.call_function("selectConnectedNodes", "t")


def _run_select_connected_nodes_bottom():
    """Ejecuta selectConnectedNodes bottom con gestión de memoria"""
    return select_nodes_ns.call_function("selectConnectedNodes", "b")


def _run_select_all_nodes_left():
    """Ejecuta selectAllNodes left con gestión de memoria"""
    return select_nodes_ns.call_function("selectAllNodes", "l")


def _run_select_all_nodes_right():
    """Ejecuta selectAllNodes right con gestión de memoria"""
    return select_nodes_ns.call_function("selectAllNodes", "r")


def _run_select_all_nodes_top():
    """Ejecuta selectAllNodes top con gestión de memoria"""
    return select_nodes_ns.call_function("selectAllNodes", "t")


def _run_select_all_nodes_bottom():
    """Ejecuta selectAllNodes bottom con gestión de memoria"""
    return select_nodes_ns.call_function("selectAllNodes", "b")


def _run_align_nodes_left():
    """Ejecuta alignNodes left con gestión de memoria"""
    return align_nodes_ns.call_function("alignNodes", direction="l")


def _run_align_nodes_right():
    """Ejecuta alignNodes right con gestión de memoria"""
    return align_nodes_ns.call_function("alignNodes", direction="r")


def _run_align_nodes_top():
    """Ejecuta alignNodes top con gestión de memoria"""
    return align_nodes_ns.call_function("alignNodes", direction="t")


def _run_align_nodes_bottom():
    """Ejecuta alignNodes bottom con gestión de memoria"""
    return align_nodes_ns.call_function("alignNodes", direction="b")


def _run_distribute_nodes_horizontal():
    """Ejecuta distribute horizontal con gestión de memoria"""
    return distribute_nodes_ns.call_function("distribute", direction="h")


def _run_distribute_nodes_vertical():
    """Ejecuta distribute vertical con gestión de memoria"""
    return distribute_nodes_ns.call_function("distribute", direction="v")


def _run_arrange_nodes():
    """Ejecuta arrangeNodes con gestión de memoria"""
    return arrange_nodes_ns.call_function("main")


def _run_scale_nodes():
    """Ejecuta scale_widget con gestión de memoria"""
    return scale_widget_ns.call_function("scale_tree")


def _run_push_nodes_up():
    """Ejecuta push nodes up con gestión de memoria"""
    try:
        push_module = push_nodes_ns._load_module()
        if push_module:
            return push_module.push(up=True)
    except Exception as e:
        print(f"[MEMORY ERROR] Error en push_nodes_up: {e}")
        return None


def _run_push_nodes_down():
    """Ejecuta push nodes down con gestión de memoria"""
    try:
        push_module = push_nodes_ns._load_module()
        if push_module:
            return push_module.push(down=True)
    except Exception as e:
        print(f"[MEMORY ERROR] Error en push_nodes_down: {e}")
        return None


def _run_push_nodes_left():
    """Ejecuta push nodes left con gestión de memoria"""
    try:
        push_module = push_nodes_ns._load_module()
        if push_module:
            return push_module.push(left=True)
    except Exception as e:
        print(f"[MEMORY ERROR] Error en push_nodes_left: {e}")
        return None


def _run_push_nodes_right():
    """Ejecuta push nodes right con gestión de memoria"""
    try:
        push_module = push_nodes_ns._load_module()
        if push_module:
            return push_module.push(right=True)
    except Exception as e:
        print(f"[MEMORY ERROR] Error en push_nodes_right: {e}")
        return None


def _run_pull_nodes_up():
    """Ejecuta pull nodes up con gestión de memoria"""
    try:
        pull_module = pull_nodes_ns._load_module()
        if pull_module:
            return pull_module.pull(up=True)
    except Exception as e:
        print(f"[MEMORY ERROR] Error en pull_nodes_up: {e}")
        return None


def _run_pull_nodes_down():
    """Ejecuta pull nodes down con gestión de memoria"""
    try:
        pull_module = pull_nodes_ns._load_module()
        if pull_module:
            return pull_module.pull(down=True)
    except Exception as e:
        print(f"[MEMORY ERROR] Error en pull_nodes_down: {e}")
        return None


def _run_pull_nodes_left():
    """Ejecuta pull nodes left con gestión de memoria"""
    try:
        pull_module = pull_nodes_ns._load_module()
        if pull_module:
            return pull_module.pull(left=True)
    except Exception as e:
        print(f"[MEMORY ERROR] Error en pull_nodes_left: {e}")
        return None


def _run_pull_nodes_right():
    """Ejecuta pull nodes right con gestión de memoria"""
    try:
        pull_module = pull_nodes_ns._load_module()
        if pull_module:
            return pull_module.pull(right=True)
    except Exception as e:
        print(f"[MEMORY ERROR] Error en pull_nodes_right: {e}")
        return None


def _run_easy_navigate_show_panel():
    """Ejecuta Easy Navigate show panel con gestión de memoria"""
    return easy_navigate_ns.call_function("ShowMainWindow")


def _run_easy_navigate_settings():
    """Ejecuta Easy Navigate settings con gestión de memoria"""
    return easy_navigate_ns.call_function("ShowSettings")


def _run_easy_navigate_edit_bookmarks():
    """Ejecuta Easy Navigate edit bookmarks con gestión de memoria"""
    return easy_navigate_ns.call_function("ShowEditBookmarksWindow")


def _run_easy_navigate_templates():
    """Ejecuta Easy Navigate templates con gestión de memoria"""
    return easy_navigate_ns.call_function("ShowTemplatesWindow")


def _run_easy_navigate_survive():
    """Ejecuta Easy Navigate survive con gestión de memoria"""
    return easy_navigate_ns.call_function("Survive")


def _run_toggle_zoom():
    """Ejecuta toggle zoom con gestión de memoria"""
    return zoom_ns.call_function("main")


# ===== CONFIGURACIÓN DE BACKDROP CON GESTIÓN DE MEMORIA =====
def _setup_backdrop_nukescripts():
    """Configura nukescripts.autoBackdrop con gestión de memoria"""
    try:
        if USE_LGA_BACKDROP:
            autoBackdrop_func = lga_backdrop_ns.get_function("autoBackdrop")
            if autoBackdrop_func:
                nukescripts.autoBackdrop = autoBackdrop_func
        else:
            autoBackdrop_func = oz_backdrop_ns.get_function("autoBackdrop")
            if autoBackdrop_func:
                nukescripts.autoBackdrop = autoBackdrop_func
    except Exception as e:
        print(f"[MEMORY ERROR] Error configurando backdrop: {e}")


# ===== FUNCIÓN PARA OBTENER SETTINGS CON GESTIÓN DE MEMORIA =====
def _get_easy_navigate_settings():
    """Obtiene settings de Easy Navigate con gestión de memoria"""
    try:
        model_module = model_ns._load_module()
        if model_module and hasattr(model_module, "Settings"):
            return model_module.Settings().Load()
    except Exception as e:
        print(f"[MEMORY ERROR] Error obteniendo settings: {e}")
    return {"shortcut": ""}


# ===== CREACIÓN DEL MENÚ =====

# Crear el menu "TPL"
n = nuke.menu("Nuke").addMenu("TPL", icon=_get_icon("LGA_Node"))

# -----------------------------------------------------------------------------

# Agrega el comando "NODE GRAPH" al menu "LAYOUT TOOLPACK"
n.addCommand("LAYOUT TOOLPACK", lambda: None)

# Define el icono para los items A
icon_LTPA = _get_icon("LTPA")

# Comandos con gestión de memoria
n.addCommand("  Add Dots Before", _run_dots, ",", shortcutContext=2, icon=icon_LTPA)

n.addCommand(
    "  Add Dots After - Left",
    _run_dots_after_left,
    "Shift+,",
    shortcutContext=2,
    icon=icon_LTPA,
)
n.addCommand(
    "  Add Dots After - Left +",
    _run_dots_after_left_plus,
    "Ctrl+Shift+,",
    shortcutContext=2,
    icon=icon_LTPA,
)
n.addCommand(
    "  Add Dots After - Right",
    _run_dots_after_right,
    "Shift+.",
    shortcutContext=2,
    icon=icon_LTPA,
)
n.addCommand(
    "  Add Dots After - Right +",
    _run_dots_after_right_plus,
    "Ctrl+Shift+.",
    shortcutContext=2,
    icon=icon_LTPA,
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items B
icon_LTPB = _get_icon("LTPB")

n.addCommand(
    "  Script Checker",
    _run_script_checker,
    "Ctrl+Alt+h",
    shortcutContext=2,
    icon=icon_LTPB,
)

n.addCommand(
    "  Create StickyNote",
    _run_sticky_note,
    "Shift+n",
    shortcutContext=2,
    icon=icon_LTPB,
)

# Flag para elegir entre LGA_backdrop o oz_backdrop
USE_LGA_BACKDROP = True  # Cambiar a False para usar oz_backdrop

# Configurar nukescripts.autoBackdrop con gestión de memoria
_setup_backdrop_nukescripts()

if USE_LGA_BACKDROP:
    n.addCommand(
        "  Create LGA_Backdrop",
        _run_lga_backdrop,
        "Shift+b",
        shortcutContext=2,
        icon=icon_LTPB,
    )

    n.addCommand(
        "  Replace with LGA_Backdrop",
        _run_lga_backdrop_replacer,
        "Ctrl+b",
        shortcutContext=2,
        icon=icon_LTPB,
    )
else:
    n.addCommand(
        "  Create Oz_Backdrop",
        _run_oz_backdrop,
        "Shift+b",
        shortcutContext=2,
        icon=icon_LTPB,
    )

    n.addCommand(
        "  Replace with Oz_Backdrop",
        _run_oz_backdrop_replacer,
        "Ctrl+b",
        shortcutContext=2,
        icon=icon_LTPB,
    )

n.addCommand(
    "  Label Nodes",
    _run_node_label,
    "shift+l",
    shortcutContext=2,
    icon=icon_LTPB,
)

# Agregar comando de limpieza de memoria para debug
n.addCommand(
    "  [DEBUG] Clean Memory",
    cleanup_all_modules,
    "",
    shortcutContext=2,
    icon=icon_LTPB,
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items C
icon_LTPC = _get_icon("LTPC")

n.addCommand(
    "  Select Nodes - Left",
    _run_select_nodes_left,
    "Alt+4",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Nodes - Right",
    _run_select_nodes_right,
    "Alt+6",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Nodes - Top",
    _run_select_nodes_top,
    "Alt+8",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Nodes - Bottom",
    _run_select_nodes_bottom,
    "Alt+2",
    shortcutContext=2,
    icon=icon_LTPC,
)

n.addCommand(
    "  Select Conected Nodes - Left",
    _run_select_connected_nodes_left,
    "Meta+4",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Conected Nodes - Right",
    _run_select_connected_nodes_right,
    "Meta+6",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Conected Nodes - Top",
    _run_select_connected_nodes_top,
    "Meta+8",
    shortcutContext=2,
    icon=icon_LTPC,
)
n.addCommand(
    "  Select Conected Nodes - Bottom",
    _run_select_connected_nodes_bottom,
    "Meta+2",
    shortcutContext=2,
    icon=icon_LTPC,
)

n.addCommand("  Select All Nodes - Left", _run_select_all_nodes_left, icon=icon_LTPC)
n.addCommand("  Select All Nodes - Right", _run_select_all_nodes_right, icon=icon_LTPC)
n.addCommand("  Select All Nodes - Top", _run_select_all_nodes_top, icon=icon_LTPC)
n.addCommand(
    "  Select All Nodes - Bottom", _run_select_all_nodes_bottom, icon=icon_LTPC
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items D
icon_LTPD = _get_icon("LTPD")

n.addCommand(
    "  Align Nodes or Bdrps - Left",
    _run_align_nodes_left,
    "Ctrl+4",
    shortcutContext=2,
    icon=icon_LTPD,
)
n.addCommand(
    "  Align Nodes or Bdrps - Right",
    _run_align_nodes_right,
    "Ctrl+6",
    shortcutContext=2,
    icon=icon_LTPD,
)
n.addCommand(
    "  Align Nodes or Bdrps - Top",
    _run_align_nodes_top,
    "Ctrl+8",
    shortcutContext=2,
    icon=icon_LTPD,
)
n.addCommand(
    "  Align Nodes or Bdrps - Bottom",
    _run_align_nodes_bottom,
    "Ctrl+2",
    shortcutContext=2,
    icon=icon_LTPD,
)

n.addCommand(
    "  Dist Nodes or Bdrps - Horizontal",
    _run_distribute_nodes_horizontal,
    "Ctrl+0",
    shortcutContext=2,
    icon=icon_LTPD,
)
n.addCommand(
    "  Dist Nodes or Bdrps - Vertical",
    _run_distribute_nodes_vertical,
    "Ctrl+.",
    shortcutContext=2,
    icon=icon_LTPD,
)

n.addCommand(
    "  Arrange Nodes",
    _run_arrange_nodes,
    "Ctrl+5",
    shortcutContext=2,
    icon=icon_LTPD,
)

n.addCommand(
    "  Scale Nodes",
    _run_scale_nodes,
    "ctrl++",
    shortcutContext=2,
    icon=icon_LTPD,
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items E
icon_LTPE = _get_icon("LTPE")

n.addCommand(
    "  Push Nodes - Up",
    _run_push_nodes_up,
    "Ctrl+Alt+8",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Push Nodes - Down",
    _run_push_nodes_down,
    "Ctrl+Alt+2",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Push Nodes - Left",
    _run_push_nodes_left,
    "Ctrl+Alt+4",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Push Nodes - Right",
    _run_push_nodes_right,
    "Ctrl+Alt+6",
    shortcutContext=2,
    icon=icon_LTPE,
)

n.addCommand(
    "  Pull Nodes - Up",
    _run_pull_nodes_up,
    "Ctrl+Alt+shift+8",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Pull Nodes - Down",
    _run_pull_nodes_down,
    "Ctrl+Alt+shift+2",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Pull Nodes - Left",
    _run_pull_nodes_left,
    "Ctrl+Alt+shift+4",
    shortcutContext=2,
    icon=icon_LTPE,
)
n.addCommand(
    "  Pull Nodes - Right",
    _run_pull_nodes_right,
    "Ctrl+Alt+shift+6",
    shortcutContext=2,
    icon=icon_LTPE,
)

# -----------------------------------------------------------------------------
# Separador
n.addSeparator()

# Define el icono para los items F
icon_LTPF = _get_icon("LTPF")

# Easy Navigate con gestión de memoria
easy_nav_menu = n.addMenu("  Easy Navigate", icon=icon_LTPF)

# Obtener settings para shortcut
settings = _get_easy_navigate_settings()

n.addCommand(
    "  Easy Navigate/Show Panel",
    _run_easy_navigate_show_panel,
    settings.get("shortcut", ""),
    shortcutContext=2,
    icon=icon_LTPF,
)
n.addCommand(
    "  Easy Navigate/Settings | Help",
    _run_easy_navigate_settings,
    "",
    icon=icon_LTPF,
)
n.addCommand(
    "  Easy Navigate/Edit Bookmarks",
    _run_easy_navigate_edit_bookmarks,
    "",
    icon=icon_LTPF,
)
n.addCommand(
    "  Easy Navigate/Templates",
    _run_easy_navigate_templates,
    "",
    icon=icon_LTPF,
)
n.addCommand(
    "  Easy Navigate/Survive (Reset Bookmarks)",
    _run_easy_navigate_survive,
    "",
    icon=icon_LTPF,
)

n.addCommand("  Toggle Zoom", _run_toggle_zoom, "h", shortcutContext=2, icon=icon_LTPF)

# -----------------------------------------------------------------------------
#                                 Version
# -----------------------------------------------------------------------------
# Crea separador y titulo
n.addSeparator()

import webbrowser

LTP_script_dir = os.path.dirname(os.path.realpath(__file__))
LTP_pdf_path = os.path.join(LTP_script_dir, "LGA_LayoutToolPack.pdf")

n.addCommand("Documentation v2.5", lambda: webbrowser.open("file://" + LTP_pdf_path))

print("[MEMORY] Sistema de gestión de memoria inicializado")
print(
    f"[MEMORY] Configuración: MAX_CACHED_MODULES={MAX_CACHED_MODULES}, AUTO_CLEANUP={ENABLE_AUTO_CLEANUP}"
)
print(
    "[MEMORY] Cada módulo está aislado con gestión de memoria para evitar 'bad allocation'"
)
