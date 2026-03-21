<p>
  <img src="Doc_Media/image22.png" alt="LGA Layout Tool Pack logo" width="56" height="56" align="left" style="margin-right:8px;">
  <span style="font-size:1.6em;font-weight:700;line-height:1;">LGA LAYOUT TOOL PACK</span><br>
  <span style="font-style:italic;line-height:1;">Lega | v2.57</span>
</p>
<br clear="left">

## InstalaciÃ³n

- Copiar la carpeta **LGA_ToolPack-Layout** que contiene todos los archivos del ToolPack a **%USERPROFILE%/.nuke**.<br> DeberÃ­a quedar asÃ­:
   ```
   .nuke/
   â””â”€ LGA_ToolPack-Layout/
      â”œâ”€ menu.py
      â”œâ”€ py/
      â””â”€ ...
  ```

- Con un editor de texto, agregar esta lÃ­nea de cÃ³digo al archivo **init.py** que estÃ¡ dentro de la carpeta **.nuke**:

  ```
  nuke.pluginAddPath('./LGA_ToolPack-Layout')
  ```

- El ToolPack permite **activar/desactivar** herramientas editando el archivo **\_LGA_LayoutToolPack_Enabled.ini**<br>
  Por defecto todas las herramientas estÃ¡n en **True**. Las que se cambian a **False**, se ocultan y evitan cargarse.<br>
  Para conservar la configuraciÃ³n en futuras actualizaciones, se puede copiar el archivo **.ini** a la carpeta **\~/.nuke/**

<br><br><br>

## ![](Doc_Media/seccion_azul.png) Add Dots before (aka Dots) v5.1 | Alexey Kuchinski <font color="#8a8a8a">| Mod Lega v2.2</font>

[https://www.nukepedia.com/python/nodegraph/dots](https://www.nukepedia.com/python/nodegraph/dots)<br>
Agrega *Dots* antes del nodo seleccionado, generando lÃ­neas de conexiÃ³n
con los nodos previos a 90 grados.<br>
Si el nodo seleccionado estÃ¡ en la misma columna que el nodo conectado,
los alinea. Ãštil para cuando se crea un nuevo nodo y no estÃ¡ alineado al
anterior.

![](Doc_Media/Dots_Before_A_v01.gif)
![](Doc_Media/Dots_Before_B_v01.gif)<br>
*La mod del pack tiene varios fixes y suma la funciÃ³n de armar un Ã¡rbol
cuando varios nodos seleccionados estÃ¡n conectados al mismo nodo y
permite agregar dots en cualquier input siempre y cuando el nodo
conectado al input no estÃ¡ en la misma fila o columna que el nodo
seleccionado.*<br><br>
<img src="Doc_Media/add_dots_before_shortcut.svg" alt="Add Dots before shortcut" width="140" height="22"><br>
<br><br>

## ![](Doc_Media/seccion_azul.png) Add Dots after v1.6 | Lega

Agrega un nodo Dot debajo del nodo seleccionado y luego otro Dot
conectado a este hacia la derecha o hacia la izquierda segÃºn el
shortcut.

![](Doc_Media/Dots_After_v01.gif)


<img src="Doc_Media/add_dots_after_shortcuts.svg" alt="Add Dots after shortcuts" width="700" height="107"><br>
<br>

## ![](Doc_Media/seccion_amarilla.png) Script Checker v0.87 | Lega

Analiza todos los nodos del script y detecta conexiones que no respetan ciertas reglas de orden y convenciones de layout.<br>
La herramienta lista en una tabla unicamente los nodos que no cumplen estas reglas. Para cada nodo muestra:<br>
<strong>Node:</strong> nombre del nodo detectado.<br>
<strong>Input A / Input B / Input Mask:</strong> que nodo esta conectado en cada entrada.<br>
<strong>Posicion actual:</strong> la direccion donde se encuentra cada conexion (left, right, top, etc.).<br>
<strong>Posicion esperada:</strong> en rojo, la ubicacion correcta segun las reglas definidas.<br>
Esto permite identificar rapidamente conexiones incorrectas o desordenadas dentro del script.<br>
<br>
<strong>Al hacer clic en una fila:</strong><br>
&bull; Selecciona el nodo en el Node Graph.<br>
&bull; Ejecuta zoom to fit.<br>
&bull; Abre el panel de propiedades del nodo.<br>
De esta forma se puede corregir el problema rapidamente. El boton Refresh vuelve a ejecutar el analisis despues de ajustar las conexiones.
![](Doc_Media/ScriptChecker_v01.gif)
![](Doc_Media/ScriptChecker_v02.gif)

![](Doc_Media/Script_checker.png)


<img src="Doc_Media/script_checker_shortcut.svg" alt="Script Checker shortcut" width="450" height="43"><br>
<br>

## ![](Doc_Media/seccion_amarilla.png) StickyNote v1.0 | Lega

Permite crear o editar un StickyNote seleccionado con algunas opciones
extras.

![](Doc_Media/Stickynote_v01.gif)

<img src="Doc_Media/stickynote_shortcut.svg" alt="StickyNote shortcut" width="490" height="43"><br>
<br>

## ![](Doc_Media/seccion_amarilla.png) Create LGA_Backdrop v1.0 | Lega

Reemplazo del autoBackdrop, con opciones extras:
- Resize basado en un margen, tomando en cuenta los nodos dentro del backdrop.<br>
- Z order automatico.<br>
- Dos filas de colores random y predeterminados, la segunda es con menos saturaciÃ³n.

![](Doc_Media/BackDrop_v01.gif)

<img src="Doc_Media/create_lga_backdrop_shortcuts.svg" alt="Create LGA Backdrop shortcuts" width="520" height="63"><br>
<br>

## ![](Doc_Media/seccion_amarilla.png) Label Node v1.0 | Lega

Permite cambiar el label de un nodo con una ventana emergente.

![](Doc_Media/LabelNode_v01.gif)

<img src="Doc_Media/label_node_shortcut.svg" alt="Label Node shortcut" width="130" height="43"><br>
<br>

## ![](Doc_Media/seccion_violeta.png) Select Nodes v1.3 | Lega

A partir del nodo seleccionado selecciona nodos en la direcciÃ³n
determinada por el shortcut.

- <span style="color:#914dcb;font-weight:600;">Select Nodes</span> selecciona los nodos que estÃ¡n alineados con el nodo
  seleccionado sin importar si estÃ¡n o no conectados entre sÃ­.<br>
  ![](Doc_Media/Select_Nodes.gif)<br>
  <img src="Doc_Media/select_nodes_shortcuts.svg" alt="Select Nodes shortcuts" width="290" height="105"><br><br>
- <span style="color:#914dcb;font-weight:600;">Select connected Nodes</span> hace lo mismo que *Select Nodes*, pero solo
  selecciona nodos que estÃ¡n conectados con el nodo seleccionado, y
  recurrentemente con el nodo siguiente en la selecciÃ³n.<br>
  ![](Doc_Media/Select_conected_nodes.gif)<br>
  <img src="Doc_Media/select_connected_nodes_shortcuts.svg" alt="Select connected Nodes shortcuts" width="345" height="123"><br><br>
- <span style="color:#914dcb;font-weight:600;">Select all Nodes</span> selecciona todos los nodos en la direcciÃ³n
  determinada por el shortcut.<br>
  ![](Doc_Media/Select_all_nodes.gif)

<br>

## ![](Doc_Media/seccion_verde.png) Align Nodes v1.2 | Lega

Alinea los nodos seleccionados segÃºn el shortcut.\
Si hay mÃ¡s de un backdrop seleccionado, en vez de alinear nodos, alinea
backdrops.

![](Doc_Media/Align_v01.gif)

<img src="Doc_Media/align_nodes_shortcuts.svg" alt="Align Nodes shortcuts" width="300" height="105"><br>
<br>

## ![](Doc_Media/seccion_verde.png) Distribute Nodes v1.1 | Lega

Distribuye horizontalmente o verticalmente los nodos seleccionados segÃºn
el shortcut. Cuando distribuye verticalmente tiene en cuenta la altura
de cada nodo para dejar el mismo espacio libre entre todos los nodos.\
Si hay mÃ¡s de un backdrop seleccionado, en vez de distribuir nodos,
distribuye backdrops.

![](Doc_Media/Distribute_v01.gif)

<img src="Doc_Media/distribute_nodes_shortcuts.svg" alt="Distribute Nodes shortcuts" width="520" height="62"><br>
<br>

## ![](Doc_Media/seccion_verde.png) Arrange Nodes v0.81 | Lega

Alinea y distribuye los nodos seleccionados de mÃºltiples columnas
tomando en cuenta las conexiones de los nodos entre sÃ­.\
![](Doc_Media/Arrange_v01.gif)

<img src="Doc_Media/arrange_nodes_shortcuts.svg" alt="Arrange Nodes shortcuts" width="470" height="83"><br>

<br>

## ![](Doc_Media/seccion_verde.png) Scale Nodes v1.0 | Erwan Leroy

Ajusta los espacios y la posiciÃ³n de los nodos seleccionados utilizando
un widget de escala.\
![](Doc_Media/Scale_v01.gif)

<img src="Doc_Media/scale_nodes_shortcuts.svg" alt="Scale Nodes shortcuts" width="300" height="43"><br><br>


## ![](Doc_Media/seccion_naranja.png) Push Nodes v1.0 | Mitja MÃ¼ller-Jend

[http://www.nukepedia.com/python/nodegraph/push_nodes](http://www.nukepedia.com/python/nodegraph/push_nodes)<br>
Empuja nodos para crear espacio en la direcciÃ³n correspondiente al
shortcut tomando como pivote la posiciÃ³n del puntero del mouse. Tiene en
cuenta los backdrops para generar espacios dentro sin mover los nodos de
otros backdrop, con lo cual es recomendable no dejar nodos sin un
backdrops. Ãštil para hacer lugar cuando hay que agregar nuevos nodos en
un sector sin espacio.

![](Doc_Media/Push_v01.gif)

<img src="Doc_Media/push_nodes_shortcuts.svg" alt="Push Nodes shortcuts" width="360" height="105"><br><br>


## ![](Doc_Media/seccion_naranja.png) Pull Nodes v1.0 | Mitja MÃ¼ller-Jend \| Mod Lega

[http://www.nukepedia.com/python/nodegraph/push_nodes](http://www.nukepedia.com/python/nodegraph/push_nodes)<br>
Mod simple del *Push Nodes* para hacer exactamente lo contrario: Achicar
el espacio en la direcciÃ³n correspondiente al shortcut tomando como
pivote el puntero del mouse.

![](Doc_Media/Pull_v01.gif)

<img src="Doc_Media/pull_nodes_shortcuts.svg" alt="Pull Nodes shortcuts" width="420" height="105"><br><br>


## ![](Doc_Media/seccion_rosa.png) Easy Navigate v2.3 | Hossein Karamian

[https://www.nukepedia.com/python/nodegraph/km-nodegraph-easy-navigate/](https://www.nukepedia.com/python/nodegraph/km-nodegraph-easy-navigate/)<br>
Crea bookmarks de los nodos seleccionados y permite saltar rÃ¡pidamente
de uno a otro. Ãštil para scripts grandes.

![](Doc_Media/EasyNavigate.gif)

<img src="Doc_Media/easy_navigate_shortcuts.svg" alt="Easy Navigate shortcuts" width="235" height="42"><br><br>


## ![](Doc_Media/seccion_rosa.png) Toggle Zoom v1.1 | Lega

Alterna entre el zoom actual y un zoom que muestra todos los nodos en el
Node Graph.<br>
Permite volver al nivel de zoom anterior usando la posiciÃ³n del cursor
como centro. Si pasan mÃ¡s de 9 segundos entre pulsaciones de la tecla H,
se reinicia el ciclo.

![](Doc_Media/Toggle_Zoom.gif)

<img src="Doc_Media/toggle_zoom_shortcuts.svg" alt="Toggle Zoom shortcuts" width="160" height="60"><br><br>




