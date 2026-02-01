# LGA Layout Panel

Nota: Priorizar código modular siempre que sea posible.

UI
- Fondo panel/teclas: #161616
- Texto/íconos base: #a9a9a9
- Hover: #cccccc
- Mod activado (toggle): fondo #2a2a2a, texto #774dcb
- Teclas con función cambiada: fondo #1d1d1d, texto #443a91
- Atenuado (greyed out): #5a5959
- En modo base (sin modificadores) todo el numpad está atenuado
- Cuando hay modo activo con cambios, el resto del numpad se atenúa (greyed out)
- Si no hay funciones activas (ej: Shift solo), todo el numpad se mantiene atenuado
- Hover solo aplica a teclas con función (no a greyed out)
- Barra superior con botón X alineado a la derecha para cerrar
- Botón de cierre usa SVG (close_base/close_hover) con CLOSE_SIZE_PX y CLOSE_WIDE_SCALE
- Escala general del panel/botones: LAYOUT_SCALE = 1.2 (no cambia la tipografía)
- Tipografía escala levemente con LAYOUT_SCALE (FONT_SIZE y FONT_WEIGHT; >=1.1 usa peso 600)
- Sin números en el numpad: se muestran flechas/Home/PgUp/PgDn/End/Ins centrados
- En modo con función: arriba símbolo y abajo el nombre de la función
- Flechas usan arrow_down.svg con variantes de color (base/active/dimmed/mode/hover) y se rotan por código
- Tecla 5 muestra "5" en modo base y "5 + Arrange" cuando corresponde
- Flechas siempre se renderizan con ARROW_ACTIVE_SCALE (0.8)
- Texto de flechas izquierda/derecha se desplaza 5px hacia arriba
- Botones de función debajo de modificadores: Push/Pull/Select/Sel Con y Align/Distrib/Arrange/Scale (toggle exclusivo)
- Al activar un modificador manual, se sincronizan los botones de función
- Con Ctrl manual se encienden Align/Distrib/Arrange/Scale en bloque
- Labels de acciones sin sufijos L/T/R/B; nombre de tecla en violeta y nombre de función en #cccccc
- Clic en Align/Distrib/Arrange/Scale desactiva el bloque Ctrl si está activo

Idea
- Panel estilo numpad para el Layout ToolPack.
- Muestra los atajos y permite ejecutar herramientas desde el panel.
- Sirve como ayuda visual para aprender combinaciones con Shift/Ctrl/Alt/Win(Meta).

Atajos relevados (desde "Layout Panel" hacia abajo en menu.py)

Layout Panel
- Layout Panel: Alt+5

Select Nodes
- Select Nodes - Left: Alt+4
- Select Nodes - Right: Alt+6
- Select Nodes - Top: Alt+8
- Select Nodes - Bottom: Alt+2
- Select Conected Nodes - Left: Meta+4
- Select Conected Nodes - Right: Meta+6
- Select Conected Nodes - Top: Meta+8
- Select Conected Nodes - Bottom: Meta+2
- Select All Nodes - Left: (sin atajo)
- Select All Nodes - Right: (sin atajo)
- Select All Nodes - Top: (sin atajo)
- Select All Nodes - Bottom: (sin atajo)

Align Nodes or Bdrps
- Align Nodes or Bdrps - Left: Ctrl+4
- Align Nodes or Bdrps - Right: Ctrl+6
- Align Nodes or Bdrps - Top: Ctrl+8
- Align Nodes or Bdrps - Bottom: Ctrl+2

Distribute Nodes or Bdrps
- Dist Nodes or Bdrps - Horizontal: Ctrl+0
- Dist Nodes or Bdrps - Vertical: Ctrl+.

Arrange / Scale
- Arrange Nodes: Ctrl+5
- Scale Nodes: Ctrl++

Push / Pull Nodes
- Push Nodes - Up: Ctrl+Alt+8
- Push Nodes - Down: Ctrl+Alt+2
- Push Nodes - Left: Ctrl+Alt+4
- Push Nodes - Right: Ctrl+Alt+6
- Pull Nodes - Up: Ctrl+Alt+Shift+8
- Pull Nodes - Down: Ctrl+Alt+Shift+2
- Pull Nodes - Left: Ctrl+Alt+Shift+4
- Pull Nodes - Right: Ctrl+Alt+Shift+6

Easy Navigate
- Show Panel: (atajo configurable en settings["shortcut"])
- Settings | Help: (sin atajo)
- Edit Bookmarks: (sin atajo)
- Templates: (sin atajo)
- Survive (Reset Bookmarks): (sin atajo)

Otros
- Toggle Zoom: h
