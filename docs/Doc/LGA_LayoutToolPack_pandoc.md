> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

#### ![](media_tmp/media/image22.png){width="0.5859372265966755in" height="0.3963692038495188in"}

#### **LGA LAYOUT TOOL PACK**

**Lega \| v2.51**

**Instalación:**

- Copiar la carpeta **LGA_ToolPack-Layout** que contiene todos los
  archivos **.py** a **%USERPROFILE%/.nuke**.

- Con un editor de texto, agregar esta línea de código al archivo
  **init.py** que está dentro de la carpeta **.nuke**:

  -----------------------------------------------------------------
  nuke.pluginAddPath(\'./LGA_ToolPack-Layout\')
  -----------------------------------------------------------------

  -----------------------------------------------------------------

- El ToolPack permite **activar/desactivar** herramientas sin tocar
  código El ToolPack permite activar/desactivar herramientas sin tocar
  código. Editando el archivo **\_LGA_ToolPackLayout_Enabled.ini**
  (dentro de **LGA_ToolPack-Layout**/).\
  Por defecto todas las herramientas están en **True**. Cambiar a
  **False** las oculta y evita cargar su script.

> Para conservar la configuración en futuras actualizaciones, se puede
> copiar el archivo a **\~/.nuke/\_LGA_ToolPackLayout_Enabled.ini**
>
> Si existen ambos, tiene prioridad el de **\~/.nuke/.**

**Add Dots before (aka Dots) v5.1 - Alexey Kuchinski \| Mod Lega
v2.2**![](media_tmp/media/image15.png){width="0.13in" height="7.0e-2in"}

[[https://www.nukepedia.com/python/nodegraph/dots]{.underline}](https://www.nukepedia.com/python/nodegraph/dots)

Agrega *Dots* antes del nodo seleccionado, generando líneas de conexión
con los nodos previos a 90 grados.

Si el nodo seleccionado está en la misma columna que el nodo conectado,
los alinea. Util para cuando se crea un nuevo nodo y no está alineado al
anterior.

![](media_tmp/media/image17.png){width="2.5263156167979in"
height="2.0in"}![](media_tmp/media/image14.png){width="2.4444444444444446in"
height="2.0in"}

![](media_tmp/media/image26.png){width="2.5156255468066493in"
height="1.3616688538932633in"}![](media_tmp/media/image25.png){width="2.463542213473316in"
height="1.3645833333333333in"}

*La mod del pack tiene varios fixes y suma la función de armar un árbol
cuando varios nodos seleccionados están conectados al mismo nodo y
permite agregar dots en cualquier input siempre y cuando el nodo
conectado al input no esté en la misma fila o columna que el nodo
seleccionado.*

Shortcut: ***,***

#### **Add Dots after v1.6 - Lega**![](media_tmp/media/image15.png){width="0.13in" height="7.0e-2in"}

Agrega un nodo Dot debajo del nodo seleccionado y luego otro Dot
conectado a este hacia la derecha o hacia la izquierda según el
shortcut.

![](media_tmp/media/image9.png){width="2.2552088801399823in"
height="1.2629166666666667in"}![](media_tmp/media/image8.png){width="2.234040901137358in"
height="1.2636996937882765in"}

Shortcuts:

***Shift + ,*** agrega el segundo Dot a la izquierda del primero

***Ctrl + shift + ,*** agrega el segundo Dot más a la izquierda del
primero

***Shift + .*** agrega el segundo Dot a la derecha del primero

***Ctrl + shift + .*** agrega el segundo Dot más a la derecha del
primero

**Create \| Edit StickyNote v1.0 -
Lega**![](media_tmp/media/image4.png){width="0.13in" height="7.0e-2in"}

Permite crear o editar un StickyNote seleccionado con algunas opciones
extras.

![](media_tmp/media/image10.png){width="1.7691655730533684in"
height="3.3623403324584427in"}

Shortcut:

***Shift + N*** crea un nuevo StickyNote o edita el StickyNote
seleccionado

**Create LGA_Backdrop v1.0 -
Lega**![](media_tmp/media/image4.png){width="0.13in" height="7.0e-2in"}

Reemplazo del autoBackdrop, con opciones extras:

- Resize basado en un margen, tomando en cuenta los nodos dentro del
  backdrop.

- Z order automatico.

- Dos filas de colores random y predeterminados, la segunda es con menos
  saturación.

![](media_tmp/media/image23.png){width="2.4234022309711287in"
height="1.9096850393700788in"}![](media_tmp/media/image11.png){width="4.100232939632546in"
height="2.090314960629921in"}

Shortcuts:

***Shift + B*** crea un nuevo LGA_Backdrop

***Ctrl + B*** reemplaza backdrops seleccionados (o todos) por
LGA_Backdrop

**Label Node v1.0 - Lega**![](media_tmp/media/image4.png){width="0.13in"
height="7.0e-2in"}

Permite cambiar el label de un nodo con una ventana emergente.

![](media_tmp/media/image21.png){width="3.7282830271216096in"
height="2.9443405511811025in"}

Shortcut: ***Shift + L***

**Select Nodes v1.3 -
Lega**![](media_tmp/media/image28.png){width="0.13in" height="7.0e-2in"}

A partir del nodo seleccionado selecciona nodos en la dirección
determinada por el shortcut.

- Select Nodes selecciona los nodos que están alineados con el nodo
  seleccionado. Es decir en la misma columna si la selección es hacia
  arriba o hacia abajo, o en la misma fila si es hacia los costados.

![](media_tmp/media/image12.png){width="2.4960728346456693in"
height="2.3729483814523187in"}![](media_tmp/media/image31.png){width="2.462739501312336in"
height="2.37in"}

> Shortcuts (usando el teclado numérico):
>
> ***Alt + Flechas (2, 4, 6, 8)***

- Select connected Nodes hace lo mismo que *Select Nodes*, pero solo
  selecciona nodos que estén conectados con el nodo seleccionado, y
  recurrentemente con el nodo siguiente en la selección.

![](media_tmp/media/image12.png){width="2.8113670166229223in"
height="2.6747036307961505in"}![](media_tmp/media/image7.png){width="2.7932305336832894in"
height="2.67in"}

> Shortcuts (usando el teclado numérico):
>
> ***Meta + Flechas (2, 4, 6, 8)*** \*Meta es la bandera en windows o la
> manzana en mac

- Select all Nodes selecciona todos los nodos en la dirección
  determinada por el shortcut.

![](media_tmp/media/image12.png){width="2.9974136045494313in"
height="2.85in"}![](media_tmp/media/image27.png){width="2.967930883639545in"
height="2.85in"}

**Align Nodes v1.2 -
Lega**![](media_tmp/media/image6.png){width="0.13in" height="7.0e-2in"}

Alinea los nodos seleccionados según el shortcut.\
Si hay más de un backdrop seleccionado, en vez de alinear nodos, alinea
backdrops.

![](media_tmp/media/image18.png){width="2.586538713910761in"
height="2.5in"}![](media_tmp/media/image29.png){width="2.6in"
height="2.5in"}

Shortcuts (usando el teclado numérico):

> ***Ctrl + Flechas (2, 4, 6, 8)***

**Distribute Nodes v1.1 -
Lega**![](media_tmp/media/image6.png){width="0.13in" height="7.0e-2in"}

Distribuye horizontalmente o verticalmente los nodos seleccionados según
el shortcut. Cuando distribuye horizontalmente tiene en cuenta la altura
de cada nodo para dejar el mismo espacio libre entre todos los nodos.\
Si hay más de un backdrop seleccionado, en vez de distribuir nodos,
distribuye backdrops.

![](media_tmp/media/image1.png){width="2.6125in"
height="2.5in"}![](media_tmp/media/image20.png){width="2.6in"
height="2.5in"}

Shortcuts (usando el teclado numérico):

> ***Ctrl + 0*** Horizontal \* El 0 es más ancho horizontalmente en el
> teclado numérico que el punto
>
> ***Ctrl + .*** Vertical

**Arrange Nodes v0.81 -
Lega**![](media_tmp/media/image6.png){width="0.13in" height="7.0e-2in"}

Alinea y distribuye los nodos seleccionados de múltiples columnas
tomando en cuenta las conexiones de los nodos entre sí.\
![](media_tmp/media/image30.png){width="2.5673075240594927in"
height="2.5in"}![](media_tmp/media/image24.png){width="2.5769225721784776in"
height="2.5in"}

Shortcut (usando el teclado numérico):

> ***Ctrl + Flechas (2, 4, 6, 8)***

**Scale Nodes v1.0 - Erwan
Leroy**![](media_tmp/media/image6.png){width="0.13in" height="7.0e-2in"}

Ajusta los espacios y la posición de los nodos seleccionados utilizando
un widget de escala.\
![](media_tmp/media/image5.png){width="2.6622003499562554in"
height="2.55in"}![](media_tmp/media/image13.png){width="2.631599956255468in"
height="2.55in"}

Shortcut (usando el teclado numérico):

> ***Ctrl + +***

**Push Nodes v1.0 - Mitja
Müller-Jend**![](media_tmp/media/image16.png){width="0.13in"
height="7.0e-2in"}

[[http://www.nukepedia.com/python/nodegraph/push_nodes]{.underline}](http://www.nukepedia.com/python/nodegraph/push_nodes)

Empuja nodos para crear espacio en la dirección correspondiente all
shortcut tomando como pivote la posición del puntero del mouse. Tiene en
cuenta los backdrops para generar espacios dentro sin mover los nodos de
otros backdrop, con lo cual es recomendable no dejar nodos sin un
backdrops. Útil para hacer lugar cuando hay que agregar nuevos nodos en
un sector sin espacio.

![](media_tmp/media/image32.png){width="2.5769225721784776in"
height="2.5in"}![](media_tmp/media/image2.png){width="2.596153762029746in"
height="2.5in"}

> Shortcuts (usando el teclado numérico):
>
> ***Ctrl + Alt + Flechas (2, 4, 6, 8)***

**Pull Nodes v1.0 - Mitja Müller-Jend \| Mod
Lega**![](media_tmp/media/image16.png){width="0.13in" height="7.0e-2in"}

[[http://www.nukepedia.com/python/nodegraph/push_nodes]{.underline}](http://www.nukepedia.com/python/nodegraph/push_nodes)

Mod simple del *Push Nodes* para hacer exactamente lo contrario: Achicar
el espacio en la dirección correspondiente al shortcut tomando como
pivote el puntero del mouse.

![](media_tmp/media/image2.png){width="2.5980391513560805in"
height="2.5in"}![](media_tmp/media/image32.png){width="2.5784317585301837in"
height="2.5in"}

> Shortcuts (usando el teclado numérico):
>
> ***Ctrl + Alt + Shift + Flechas (2, 4, 6, 8)***

**Easy Navigate v2.3 - Hossein
Karamian**![](media_tmp/media/image3.png){width="0.13in"
height="7.0e-2in"}

[[https://www.nukepedia.com/python/nodegraph/km-nodegraph-easy-navigate/]{.underline}](https://www.nukepedia.com/python/nodegraph/km-nodegraph-easy-navigate/)

Crea bookmarks de los nodos seleccionados y permite saltar rápidamente
de uno a otro. Util para scripts grandes.

![](media_tmp/media/image19.png){width="2.677037401574803in"
height="2.6in"}

> Shortcuts:
>
> ***Shift + A*** Abre la GUI

**Toggle Zoom v1.1 -
Lega**![](media_tmp/media/image3.png){width="0.13in" height="7.0e-2in"}

Alterna entre el zoom actual y un zoom que muestra todos los nodos en el
Node Graph.

Permite volver al nivel de zoom anterior usando la posición del cursor
como centro. Si pasan más de 9 segundos entre pulsaciones de la tecla H,
se reinicia el ciclo.

> Shortcut: ***H***
