> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# Google Doc ? Markdown (LGA Layout Tool Pack)

## Objetivos actuales
- Mantener un único origen editable en Markdown dentro de Doc/ para que Codex pueda modificar documentación sin depender de Google Docs.
- Seguir exportando a PDF/Google Doc cuando haga falta, pero con una representación .md que conserve la estructura, íconos y capturas.
- Dejar registrado el proceso para repetir la conversión sin improvisar pasos ni crear carpetas fuera de Doc/.

## Reglas y lineamientos pedidos por Lega
- Trabajar siempre dentro de C:/Users/leg4-pc/.nuke/LGA_ToolPack-Layout/Doc/ y evitar "hacer un desastre" de carpetas; cualquier carpeta nueva debe explicarse (p. ej. Doc_Media/).
- Conservar el estilo visual del PDF original (colores, alineaciones básicas, logos) aun sabiendo que Markdown es más limitado.
- El resultado debe verse correctamente en visores comunes como VS Code *y* GitHub; por eso no podemos depender de atributos Pandoc {width=...}.
- Preferir herramientas CLI ya disponibles (Pandoc portátil en Doc/pandoc-3.9/) y documentar cada comando.

## Flujo recomendado
1. **Exportar desde Google Docs a DOCX** (ya guardado como Doc/LGA_LayoutToolPack.docx). Cada vez que haya cambios importantes en el Google Doc, descargar un DOCX actualizado y reemplazarlo.
2. **Generar un volcado Pandoc para metadatos e imágenes a tamaño original**:
   ```powershell
   cd C:/Users/leg4-pc/.nuke/LGA_ToolPack-Layout/Doc
   .\pandoc-3.9\pandoc-3.9\pandoc.exe LGA_LayoutToolPack.docx `
       -o LGA_LayoutToolPack_pandoc.md `
       --extract-media=media_tmp
   ```
   Esto crea media_tmp/ (copias originales) y LGA_LayoutToolPack_pandoc.md con los atributos width="…in" que usamos como referencia y que también nos sirven para spotear duplicados o errores de conversión.
3. **Actualizar el Markdown principal (LGA_LayoutToolPack.md)** a mano copiando/pegando desde el volcado donde haga falta, ajustando encabezados, quotes, etc. Evitar guardar los atributos {width=…} porque GitHub los muestra como texto plano.
4. **Escalar las imágenes para visores Markdown**:
   - Instalar dependencias solo una vez (pip install pillow).
   - Ejecutar python scale_images.py. El script valida que existan LGA_LayoutToolPack_pandoc.md y las imágenes originales en Doc_Media/Originals/, calcula el ancho objetivo en píxeles (pulgadas * 96) y genera:
     - Copias escaladas en Doc_Media/.
     - Cambios dentro de LGA_LayoutToolPack.md para que apunte a Doc_Media/.
     - Un log con el detalle de cada redimensionado en scale_images.log (ideal para revisiones rápidas).
    - Si alguna imagen necesita ajustes extra (p. ej. agregar padding inferior para alinear íconos), editar el diccionario `ADJUSTMENTS` en scale_images.py; allí ya están configurados los íconos seccionales (`seccion_*.png`) para sumar 5?px de padding inferior.
   - Después de confirmar que la vista previa se ve bien, se puede eliminar media_tmp/ para no duplicar archivos.
5. **Aplicar formato final al Markdown**:
   - Reemplazar el encabezado inicial por un bloque `<p>` con la imagen usando `align="left"` y un `<br clear="left">` (como en README) para que GitHub mantenga logo + texto en la misma línea sin aplicar bordes.
   - Convertir cada sección de herramienta al estilo `## ![](Doc_Media/<icono>.png) Nombre de la herramienta`, asegurándose de que la imagen vaya primero y que el título quede en el mismo nivel que “Instalación”.
   - Mantener notas vinculadas a bullets (como la de `\_LGA_ToolPackLayout_Enabled.ini`) usando una barra invertida `\` al final de la línea para que queden dentro del mismo punto.
   - Revisar atajos/shortcut blocks para que continúen en texto plano con listas o blockquotes según corresponda.
   - Dejar dos líneas en blanco antes de cada encabezado `## ![](…)` (excepto `## Instalación`) para que cada bloque tenga el mismo aire que en el PDF.
   - Para los bullets “Select …” u otros que describen varias variantes:
     - Prefiere `- <span style="color:#914dcb;font-weight:600;">Nombre</span>` seguido del texto, con las dos capturas en la misma línea (`![](…) ![](…)`) y un `<br><br>` antes del siguiente bullet.
   - **Reglas de shortcuts**:
     - El encabezado debe verse como `Shortcuts` en gris y negrita + `(usando el teclado numérico)` en gris sin negrita.
     - Cada combinación (Alt/Meta + flechas) se lista en una línea con las flechas reales (`?`, `?`, `?`, `?`) y el número entre paréntesis.
     - Las aclaraciones (p. ej. “*Meta es la bandera…*”) van en una línea aparte, misma columna, con color gris claro (`#aaaaaa`) y `font-size` ligeramente menor (`0.9em`).
6. **Normalizar íconos de sección**:
   - Usamos archivos canónicos en `Doc_Media/`: `seccion_azul.png` (Add Dots), `seccion_amarilla.png` (Create/Label), `seccion_violeta.png` (Select Nodes), `seccion_verde.png` (Align/Distribute/Arrange/Scale), `seccion_naranja.png` (Push/Pull) y `seccion_rosa.png` (Easy Navigate/Toggle Zoom).
   - En `Doc_Media/Originals/` existen las versiones originales con el mismo nombre; `scale_images.py` incluye un mapa `ICON_ALIASES` para recuperar las medidas del DOCX (p. ej. `seccion_azul.png` ? `image15.png`). Si se agrega un nuevo ícono, recordar sumar su alias allí.

## Tabla de tamaños actuales
| Archivo | Original (px) | Escalado (px) |
| --- | --- | --- |
| image1.png | 739x708 | 251x240 |
| image10.png | 322x612 | 170x323 |
| image11.png | 940x482 | 394x202 |
| image12.png | 740x704 | 288x274 |
| image13.png | 733x713 | 253x246 |
| image14.png | 734x713 | 235x228 |
| seccion_azul.png (ex image15) | 676x285 | 12x12 |
| seccion_naranja.png (ex image16) | 135x252 | 12x12 |
| image17.png | 734x709 | 243x235 |
| image18.png | 733x710 | 248x240 |
| image19.png | 736x713 | 257x249 |
| image2.png | 736x708 | 249x240 |
| image20.png | 741x711 | 250x240 |
| image21.png | 409x323 | 358x283 |
| image22.png | 256x256 | 56x56 |
| image23.png | 655x510 | 233x181 |
| image24.png | 732x710 | 247x240 |
| image25.png | 973x528 | 237x129 |
| image26.png | 901x479 | 242x129 |
| image27.png | 734x708 | 285x275 |
| seccion_violeta.png (ex image28) | 78x149 | 12x12 |
| image29.png | 744x712 | 250x239 |
| seccion_rosa.png (ex image3) | 118x272 | 12x12 |
| image30.png | 733x715 | 246x240 |
| image31.png | 736x708 | 236x227 |
| image32.png | 730x710 | 248x241 |
| seccion_amarilla.png (ex image4) | 109x228 | 12x12 |
| image5.png | 738x705 | 256x245 |
| seccion_verde.png (ex image6) | 102x168 | 12x12 |
| image7.png | 733x707 | 268x258 |
| image8.png | 1150x452 | 214x84 |
| image9.png | 904x506 | 217x121 |


## Notas y descubrimientos
- GitHub y la vista previa básica de VS Code no interpretan las extensiones Pandoc {width=... height=...}, por eso aparecía texto crudo debajo del logo original.
- El encabezado con logo + título se resuelve usando un `<p>` con la imagen alineada a la izquierda (`align="left"`) y un `<br clear="left">`; GitHub respeta ese atributo heredado, mantiene todo en la misma fila y no agrega bordes extra.
- Los íconos pequeños del PDF estaban configurados a ~0.13" de ancho; al convertirlos a píxeles equivalentes (~12?px) se ven como en el DOCX. Para que GitHub respete ese tamaño, necesitamos las imágenes físicamente escaladas (no sólo CSS).
- Doc_Media/Originals/ conserva los bitmaps originales por si hace falta regenerar otra versión; Doc_Media/ es la carpeta que usa el .md final.
- scale_images.py sobrescribe Doc_Media/, así que cualquier ajuste manual en esa carpeta debe hacerse después de correr el script.
- Mantener LGA_LayoutToolPack_pandoc.md a mano facilita detectar diffs con la versión original del DOCX y volver a extraer medidas cuando el documento cambie.
- Los encabezados de cada herramienta se formatean como `## ![](Doc_Media/icon.png) Nombre`, así el icono queda alineado a la izquierda del título y GitHub respeta la jerarquía visual.
- Cuando se necesita reducir la presencia de parte del título (ej. “| Mod Lega v2.2”), se puede envolver esa porción en `<font color="#8a8a8a">...</font>` para que GitHub lo muestre con un gris suave.
- Si se necesita publicar un PDF desde el Markdown, usar Pandoc apuntando al .md ya limpio; las imágenes en Doc_Media/ mantienen las proporciones esperadas en cualquier export.
- Cuando un comportamiento conviene verse animado (p. ej. Add Dots), reemplazamos las capturas estáticas por GIFs manteniendo el mismo bloque de Markdown. Guardamos el original sin escalar dentro de `Doc_Media/Originals/` y publicamos la copia escalada (por ejemplo `Doc_Media/Dots_Before_A_v01.gif`) en `Doc_Media/`.
