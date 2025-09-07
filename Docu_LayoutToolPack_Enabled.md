# Sistema de Configuración de Herramientas LGA Layout ToolPack

## 🎯 ¿Qué es este sistema?

El **Sistema de Configuración de Herramientas** es una funcionalidad avanzada del LGA Layout ToolPack que permite a los usuarios personalizar completamente qué herramientas se cargan y muestran en el menú de Nuke. Esto proporciona un control total sobre el entorno de trabajo, optimizando la carga y evitando clutter en el menú.

## 📁 Archivos del Sistema

### Archivos de Configuración
- **`_LGA_LayoutToolPack_Enabled.ini`** (en carpeta del paquete): Configuración por defecto
- **`_LGA_LayoutToolPack_Enabled.ini`** (en `~/.nuke/`): Configuración personal del usuario

### Archivos del Sistema
- **`menu.py`**: Menú principal con el sistema integrado
- **`Docu_LayoutToolPack_Enabled.md`**: Esta documentación

## ⚙️ Cómo Funciona

### 1. Carga de Configuración
```python
# El sistema busca archivos .ini en este orden:
1. ~/.nuke/_LGA_LayoutToolPack_Enabled.ini (usuario) - PRIORIDAD
2. LGA_ToolPack-Layout/_LGA_LayoutToolPack_Enabled.ini (paquete) - DEFAULTS
```

### 2. Evaluación de Herramientas
- **True**: La herramienta se carga y muestra en el menú
- **False**: La herramienta NO se carga ni muestra
- **No existe**: Se asume **True** (compatibilidad hacia atrás)

### 3. Carga Perezosa (Lazy Loading)
- Los módulos de las herramientas se importan **solo** cuando están habilitadas
- Mejora significativamente el tiempo de inicio de Nuke
- Reduce el uso de memoria

## 📝 Formato del Archivo .ini

```ini
[Tools]
; LGA Layout ToolPack – Tool Switches
; Set to False to hide a tool from the menu AND avoid importing its script.
; Leave True to keep it visible and load on demand.
; Example: Add_Dots_Before = False

; === SECCIÓN A: DOTS ===
Add_Dots_Before = True
Dots_After_System = True
; ... todas las demás herramientas
```

## 🛠️ Lista Completa de Herramientas Configurables

### **🟢 Herramientas Individuales:**
- **Add_Dots_Before**: "Add Dots Before" (Dots.Dots)
- **Script_Checker**: "Script Checker" (LGA_scriptChecker)
- **StickyNote**: "Create StickyNote" (LGA_StickyNote)
- **NodeLabel**: "Label Nodes" (LGA_NodeLabel)
- **Toggle_Zoom**: "Toggle Zoom" (LGA_zoom)

### **🟡 Herramientas Agrupadas:**

#### **1. Dots_After_System** (4 comandos)
*Variantes de "Add Dots After":*
- "Add Dots After - Left" (LGA_dotsAfter)
- "Add Dots After - Left +" (LGA_dotsAfter)
- "Add Dots After - Right" (LGA_dotsAfter)
- "Add Dots After - Right +" (LGA_dotsAfter)

#### **2. LGA_Backdrop_System** (2 comandos)
*Sistema completo LGA Backdrop:*
- "Create LGA_Backdrop"
- "Replace with LGA_Backdrop"

#### **3. Select_Nodes** (12 comandos)
*Todas las funciones de selección de nodos:*
- "Select Nodes - Left/Right/Top/Bottom" (4 comandos)
- "Select Connected Nodes - Left/Right/Top/Bottom" (4 comandos)
- "Select All Nodes - Left/Right/Top/Bottom" (4 comandos)

#### **4. Align_Nodes** (4 comandos)
*Herramientas de alineación únicamente:*
- "Align Nodes or Bdrps - Left/Right/Top/Bottom" (4 comandos)

#### **5. Distribute_Nodes** (2 comandos)
*Herramientas de distribución únicamente:*
- "Dist Nodes or Bdrps - Horizontal/Vertical" (2 comandos)

#### **6. Arrange_Nodes** (1 comando)
*Herramientas de organización:*
- "Arrange Nodes" (LGA_arrangeNodes)

#### **7. Scale_Nodes** (1 comando)
*Herramientas de escalado:*
- "Scale Nodes" (scale_widget)

#### **8. Push_Pull_Nodes** (8 comandos)
*Herramientas de movimiento de nodos:*
- "Push Nodes - Up/Down/Left/Right" (4 comandos)
- "Pull Nodes - Up/Down/Left/Right" (4 comandos)

#### **9. Easy_Navigate** (5 comandos)
*Sistema completo de navegación:*
- "Easy Navigate/Show Panel" (Km_NodeGraph_Easy_Navigate)
- "Easy Navigate/Settings | Help"
- "Easy Navigate/Edit Bookmarks"
- "Easy Navigate/Templates"
- "Easy Navigate/Survive (Reset Bookmarks)"

## 📊 **Resumen Final:**

**Total de herramientas configurables:** 14 configuraciones
**Comandos totales controlados:** 38 comandos del menú

## 🚀 Cómo Configurar

### Paso 1: Localizar el Archivo
1. Abre tu carpeta personal de Nuke: `~/.nuke/`
2. Si no existe, crea el archivo: `_LGA_LayoutToolPack_Enabled.ini`

### Paso 2: Copiar la Configuración Base
Copia el contenido del archivo de defaults desde la carpeta del paquete:
```
LGA_ToolPack-Layout/_LGA_LayoutToolPack_Enabled.ini
```

### Paso 3: Personalizar
Edita las líneas cambiando `True` por `False` para deshabilitar herramientas:

```ini
[Tools]
; Deshabilitar herramientas que no uso
Dots_After_System = False
Select_Nodes = False

; Mantener las que sí uso
LGA_Backdrop_System = True
Easy_Navigate = True
```

### Paso 4: Aplicar Cambios
1. Guarda el archivo
2. Reinicia Nuke
3. Las herramientas deshabilitadas no aparecerán en el menú

## 💡 Ventajas del Sistema

### Para Usuarios Individuales
- **Personalización**: Solo ver las herramientas que necesitas
- **Performance**: Inicio más rápido de Nuke
- **Limpieza**: Menú menos cluttered
- **Flexibilidad**: Cambiar configuración sin reinstalar

### Para Estudios/Equipos
- **Consistencia**: Configuraciones estándar por rol
- **Mantenimiento**: Fácil actualizar sin afectar usuarios
- **Escalabilidad**: Nuevas herramientas se agregan automáticamente

### Para Desarrolladores
- **Modularidad**: Código más organizado
- **Debugging**: Fácil identificar problemas de carga
- **Mantenibilidad**: Cambios centralizados
- **Compatibilidad**: Sistema backward-compatible

## 🔧 Casos de Uso Comunes

### Artista de Layout Básico
```ini
[Tools]
; Solo herramientas básicas
Add_Dots_Before = True
LGA_Backdrop_System = True
Align_Nodes = True

; Deshabilitar avanzadas
Select_Nodes = False
Easy_Navigate = False
```

### Artista de Layout Avanzado
```ini
[Tools]
; Todas las herramientas disponibles
Dots_After_System = True
Select_Nodes = True
Push_Pull_Nodes = True
Easy_Navigate = True
```

### Configuración Minimalista
```ini
[Tools]
; Solo lo esencial
LGA_Backdrop_System = True
Align_Nodes = True
Distribute_Nodes = True

; Todo lo demás deshabilitado
Dots_After_System = False
Select_Nodes = False
Easy_Navigate = False
```

## ⚠️ Notas Importantes

### Compatibilidad
- Si no existe el archivo .ini, **todas las herramientas se habilitan por defecto**
- Valores no reconocidos se tratan como `True`
- El sistema es completamente backward-compatible

### Troubleshooting
- **Herramienta no aparece**: Verificar que esté en `True` en el .ini
- **Error al cargar**: Revisar sintaxis del archivo .ini
- **Cambios no aplican**: Reiniciar Nuke completamente

### Archivos de Configuración
- **Usuario**: `~/.nuke/_LGA_LayoutToolPack_Enabled.ini` - **Pisa** la configuración del paquete
- **Paquete**: `LGA_ToolPack-Layout/_LGA_LayoutToolPack_Enabled.ini` - Valores por defecto

## 🔄 Actualizaciones y Nuevas Herramientas

Cuando se actualiza el LGA Layout ToolPack:

1. **Nuevas herramientas**: Se agregan automáticamente con `True` por defecto
2. **Configuración existente**: Se mantiene sin cambios
3. **Compatibilidad**: Nunca se pierden configuraciones personalizadas

## 📞 Soporte

Si tienes problemas con el sistema de configuración:

1. Verifica la sintaxis del archivo .ini
2. Asegúrate de que Nuke se reinició completamente
3. Revisa la consola de Nuke por mensajes de warning
4. Consulta esta documentación

---

**Versión**: LGA Layout ToolPack v2.5
**Última actualización**: $(date)
**Autor**: Sistema de configuración automática
