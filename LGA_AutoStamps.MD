# LGA_AutoStamps

Herramienta para Nuke que detecta conexiones "problematicas" entre nodos y las
reemplaza automaticamente por **Stamps** (sistema de Adrian Pueyo), dejando el
Node Graph mas limpio y legible.

---

## Objetivo general

Encontrar y reemplazar por Stamps:

1. **Conexiones muy largas** entre dos nodos lejanos. *(v0.01 - hecho)*
2. **Conexiones desde un nodo a un Dot y de ahi a multiples lugares** (un Dot que
   distribuye una misma salida a varios destinos). *(v0.02 - hecho)*
3. **Conexiones con hidden inputs** (inputs ocultos / clones a distancia). *(v0.03 - hecho)*
4. **Confirmacion por grupo** antes de dejar cada Stamp (cartel con nombre +
   Reemplazar/Cancelar, con zoom al grupo). *(v0.04 - hecho)*
5. **Zoom al contexto** (source + destinos) y **cartel no bloqueante**. *(v0.05 - hecho)*
6. **Two-phase** (preview con undo off + apply limpio): cancelar no ensucia el
   historial y un Ctrl+Z deshace sin avalancha de errores. *(v0.06 - hecho)*

El desarrollo es **incremental**: empezamos por lo mas simple y vamos sumando casos.

---

## Como funcionan los Stamps (resumen)

- **Anchor (padre):** nodo de referencia (normalmente un `NoOp`). Tiene un `title`
  y opcionalmente `tags`. Toma como input 0 al nodo fuente real.
- **Wired (hijo):** nodo (normalmente `PostageStamp` para 2D) que referencia a un
  Anchor por su nombre, guardado en el knob `anchor`. Su input al Anchor esta
  oculto (`hide_input = True`), por eso no se ve el cable largo.
- Flujo de datos: `Fuente -> Anchor ...(virtual)... Wired -> Destino`.
- Beneficio: se eliminan los cables largos/cruzados; un mismo Anchor puede tener
  muchos Wired hijos repartidos por todo el arbol.

### API de `stamps.py` que reutilizamos

| Funcion | Uso |
|---|---|
| `stamps.anchor(title, tags, input_node, node_type)` | Crea el Anchor. **OJO:** internamente NO conecta `input_node`; hay que hacer `anchor.setInput(0, src)` a mano. |
| `stamps.wired(anchor)` | Crea el Wired ya conectado (oculto) al Anchor. |
| `stamps.nodeType(node)` | Devuelve `2D`/`Deep`/`3D`/`Camera`/`Axis`/`Particle`. |
| `stamps.realInput(node, stopOnLabel, mode)` | Salta Dots/Stamps/Reformats para hallar el nodo "real". |
| `stamps.getDefaultTitle(node)` / `stamps.defaultTitle(node)` | Calculan un titulo por defecto (el 2do viene de `stamps_config`). |
| `stamps.isAnchor(n)` / `stamps.isWired(n)` | Identifican si un nodo ya es un Stamp. |

El modulo `stamps` ya esta importado en la sesion de Nuke (se carga desde
`~/.nuke/CollectedTools_LGA/stamps`). El script igual agrega ese path por las dudas.

---

## Estado actual

**Archivo:** `py/LGA_AutoStamps.py` — funcion principal `main()`.

`main()` usa una arquitectura **two-phase** (v0.06):

1. **Fase 1 — `preview_all()` con `nuke.Undo().disable()`:** corre los tres pases;
   por cada grupo construye los Stamps (`build_*`), hace zoom, muestra el cartel,
   guarda la decision (`{clave: titulo}`) y **revierte** el grupo (`GroupTx.revert`).
   Al terminar, el grafo quedo igual que al inicio y **nada entro al historial de
   undo**.
2. **Fase 2 — `apply_all()` dentro de un unico `nuke.Undo().begin()/end()`:**
   re-detecta los grupos (el grafo volvio al original) y **re-aplica solo los
   aceptados** (por `clave`), sin cartel, seteando el titulo elegido. Como solo hay
   creaciones limpias, **un solo Ctrl+Z deshace todo sin disparar la avalancha** de
   errores de los callbacks de stamps.

Claves de grupo (para casar preview <-> apply): `H|<source>` (hidden),
`D|<source>` (dots), `L|<src>|<dst>|<idx>` (largas). Usan nombres de nodo, que no
cambian al revertir.

Los tres pases (su deteccion y la construccion de cada grupo) son:

### Pase 0 — Hidden inputs (v0.03)

Detecta nodos con `hide_input = true` y un `input(0)` real (conexion oculta a un
origen lejano). Se ignoran los Stamps (que tambien usan `hide_input` por diseno).
Corre **primero** para que los otros pases no lo pisen.

- **Si el nodo oculto es un Dot:** se **borra** y se reemplaza por un **Wired** en
  su misma posicion; los nodos que colgaban del Dot se reconectan al Wired.
- **Si es cualquier otro nodo (no-Dot):** **no se toca**; se crea un **Wired**
  arriba y se conecta a su `input(0)`, y se le pone `hide_input = false` para que
  la conexion corta sea visible.
- **Naming (regla del label):** si el nodo oculto tiene `label`, el Anchor (y por
  herencia el Wired) toma ese label; si no, el nombre derivado del origen.
- **Reuse:** **1 Anchor por nodo origen**. Si varios pickups apuntan al mismo
  origen, comparten Anchor (gana el `label`/titulo del primero). Tambien reusa un
  Anchor ya existente en el script si su `input(0)` es ese origen.

### Pase 1 — Distribuciones por Dots (v0.02)

Para cada nodo origen (no-Dot, no-Stamp) recorre **solo a traves de Dots** su
arbol de salida y junta los destinos finales (nodos reales alimentados por algun
Dot del arbol). Si hay `>= MIN_DESTINATIONS` destinos:

1. Crea **1 Anchor** justo debajo del origen, conectado a el.
2. Crea **1 Wired por destino**, justo arriba de cada uno, y reconecta el input
   correspondiente del destino al Wired.
3. **Borra todos los Dots** del arbol.

Los arboles de Dots son **disjuntos** (un Dot tiene un solo input), por eso se
pueden relevar todos primero y procesar despues sin pisarse.

### Pase 2 — Conexiones largas directas (v0.01)

Recorre las conexiones directas (ignorando Dots y Stamps en ambos extremos) y,
si la **distancia euclidea** entre centros supera `DISTANCE_THRESHOLD`, reemplaza
la conexion por Anchor (debajo del padre) + Wired (arriba del hijo).

### Confirmacion por grupo + two-phase (v0.04-v0.06)

En la **fase preview**, cada grupo (1 Anchor + sus Wireds) se construye y pasa por
`preview_confirm()`:

1. Los Stamps **ya estan creados** (el reemplazo ya ocurrio), asi el usuario los ve.
2. **Zoom-to-fit al CONTEXTO** (`zoom_to_nodes`): no encuadra los Stamps solos sino
   el **padre del padre** (el nodo origen = `anchor.input(0)`) y los **hijos de los
   hijos** (los nodos destino), para que el usuario entienda que se reemplazo.
   Calcula el bbox, busca el widget `DAG` (Qt) para su tamano en px y hace
   `nuke.zoom(min(dag_w/bw, dag_h/bh) * ZOOM_MARGIN / ZOOM_OUT_FACTOR, [cx, cy])`.
3. **Cartel NO bloqueante** (`ReplaceDialog`) con el nombre sugerido (editable) y
   botones **Reemplazar** / **Cancelar**, posicionado en una esquina del DAG y
   siempre arriba (`WindowStaysOnTopHint`). Se espera la respuesta con un
   **`QtCore.QEventLoop` anidado**, que bloquea el flujo del script pero deja la UI
   de Nuke navegable (pan/zoom/seleccion en el DAG).

Tras el cartel, en la **fase preview siempre se revierte** el grupo (`GroupTx.revert`)
y se guarda la decision. En la **fase apply** se re-crea solo lo aceptado y se aplica
el titulo elegido (`apply_title` al Anchor + Wireds).

**Por que two-phase (v0.06):** antes todo (incluido el revert de los cancelados)
ocurria dentro de un unico `nuke.Undo()`. Aunque el neto de un cancelado era cero,
el "churn" (crear -> revertir, que recrea nodos) quedaba grabado, y al hacer Ctrl+Z
Nuke recreaba esos Wireds disparando los `knobChanged` de stamps sobre nodos
detached -> **avalancha de errores**. Con two-phase, la fase preview corre con
`nuke.Undo().disable()` (no graba nada) y la fase apply solo graba creaciones
limpias de los aceptados -> **un Ctrl+Z deshace todo sin errores**.

#### `GroupTx` (transaccion por grupo)

- `created(node)` — registra nodos creados (se borran en revert).
- `change_input(node, idx, new)` — cambia un input cuyo valor previo **sobrevive**
  (ej. el `source`); guarda el viejo para restaurar.
- `change_knob(node, knob, val)` — idem para knobs (ej. `hide_input`).
- `snapshot_and_delete_dots(dots, children)` — fotografia los Dots (pos, label,
  `hide_input`, input desde source/otro Dot, destinos externos) y los borra.
- `revert()` — borra creados → restaura inputs/knobs → `restore_dots()` recrea.

> Importante: las reconexiones cuyo input viejo era **un Dot que se borra** NO se
> registran con `change_input` (la referencia moriria). Se hacen con `setInput`
> plano y el `snapshot_dots` se encarga de restaurarlas al recrear el Dot.

### Variables de configuracion (arriba del archivo)

- `DISTANCE_THRESHOLD = 250` — umbral de distancia en px (pase 2).
- `MIN_DESTINATIONS = 3` — minimo de destinos para colapsar un arbol de Dots (pase 1).
- `ANCHOR_GAP_Y = 40` — separacion vertical padre → Anchor.
- `WIRED_GAP_Y = 40` — separacion vertical Wired → hijo.
- `ZOOM_MARGIN = 0.9` — aire base alrededor del grupo en el zoom-to-fit.
- `ZOOM_OUT_FACTOR = 1.0` — cuanto MAS zoom out para dar contexto (1.0 = justo;
  >1.0 = mas alejado, ej. 1.5 = 50% mas lejos).
- `SKIP_CLASSES` — clases ignoradas (`Viewer`, `BackdropNode`, `Root`).
- `DEBUG = True` — prints de diagnostico.

### Como probarlo en Nuke

```python
import LGA_AutoStamps
import importlib; importlib.reload(LGA_AutoStamps)
LGA_AutoStamps.main()
```

(`py/` ya esta en el plugin path del ToolPack, asi que es importable directo.)

---

## Aprendizajes / Notas tecnicas

- **`stamps.anchor()` ignora el parametro `input_node`.** La conexion al padre
  hay que forzarla con `setInput`. (En la tool original el `nuke.createNode`
  autoconecta al nodo seleccionado; nosotros lo hacemos explicito para no
  depender de la seleccion.)
- **`stamps.wired()` ya posiciona** el nodo relativo al Anchor y setea
  `hide_input`. Lo reposicionamos despues sobre el hijo.
- **El pase de distancia DEBE ignorar Dots y Stamps.** Si no, despues de crear
  los Stamps detecta el cable oculto Wired→Anchor (que es largo) e intenta
  estamparlo de nuevo. Filtramos con `stamps.isAnchor` / `stamps.isWired`.
- **No hashear nodos directamente:** para deduplicar Dots/destinos usamos
  `node.name()` (string) como clave, mas seguro que poner objetos Node en un set.
- Medimos distancia entre **centros** (`xpos + screenWidth/2`, `ypos + screenHeight/2`),
  no entre esquinas.
- `setInput(i, nuevoNodo)` reemplaza el input anterior: no hace falta desconectar
  a mano antes de reconectar.
- Recorremos el grafo con un mapa `{nodo: [(downstream, input_index), ...]}`
  construido una sola vez (mas robusto que `node.dependent()`).
- **`node.input(0)` devuelve el origen aunque `hide_input` este activo:** la
  conexion existe, solo esta oculta visualmente. Por eso los hidden inputs se
  resuelven igual que cualquier otra conexion.
- **Los Wireds tienen `hide_input = true` por diseno** → en el pase de hidden
  inputs hay que excluir Stamps (`is_stamp`) para no procesarlos como pickups.
- **Reuse de Anchor:** en el pase de hidden inputs se agrupan los pickups por
  `source.name()` (1 Anchor por origen). Ademas `existing_anchor_for_source`
  reutiliza un Anchor ya presente cuyo `input(0)` sea ese origen. El `title` solo
  se aplica al crearlo; si se reusa, se mantiene.
- El `label` se toma como `label.split("\n")[0].strip()` (primera linea limpia).
- En el pase de hidden inputs, los **Dots de ruteo** del pase 1 se distinguen de
  los **pickups ocultos** por `hide_input`: `collect_dot_tree` ignora los Dots con
  `hide_input` activo.
- **No usar un nodo despues de `nuke.delete()`:** da
  `ValueError: A PythonObject is not attached to a node`. Hay que capturar lo que
  se necesite (ej. `node.name()`) ANTES de borrar. Si el error salta dentro del
  `try` del Undo, aborta los pases siguientes y parece que "se rompio todo".
- **Zoom-to-fit:** el widget del Node Graph se llama `DAG` (Qt). Su `width()/height()`
  dan el viewport en px. `nuke.zoom(scale, [cx, cy])` hace zoom Y scroll de una.
  Tambien existe `nuke.center()` si se quisiera restaurar la vista despues.
- **Zoom al contexto, no a los Stamps:** los Stamps recien creados solos no le
  dicen nada al usuario. Encuadramos `anchor.input(0)` (source) + los destinos.
- **Cartel no bloqueante:** en vez de `dlg.exec_()` (modal, bloquea la UI) usamos
  `dlg.setModal(False)` + `dlg.show()` + un `QtCore.QEventLoop` anidado que se
  cierra con la senal `finished`. Asi el script "espera" la decision pero el DAG
  sigue navegable. `WindowStaysOnTopHint` evita que el cartel quede atras.
- **OJO con los callbacks de Stamps + event loop:** el loop anidado procesa la cola
  de eventos de Nuke, y ahi disparan los `knobChanged` de Stamps. Si un Wired fue
  borrado (cancel), su callback corre sobre un nodo muerto y crashea en
  `stamps.py` (`n.inputs()` -> "A PythonObject is not attached to a node").
  **Fix:** poner `stamps.Stamps_LockCallbacks = True` durante toda la corrida
  (restaurar en `finally`). El callback retorna antes de tocar el nodo. Esto ademas
  evita el popup "update linked stamps title?" al renombrar.
- **Con callbacks silenciados hay que setear el estilo del Wired a mano** con
  `stamps.wiredGetStyle(wired)` (es una funcion directa, no depende del flag), si no
  el Wired podria quedar con apariencia "broken".
- **`nuke.createNode` hace SPLICE si hay un nodo seleccionado:** inserta el nodo
  nuevo entre el seleccionado y su primer dependiente (le roba el input). Por eso
  NO hay que seleccionar el source al crear el Anchor: se crea suelto (con
  `deselect_all()`) y se conecta con `anchor.setInput(0, source)`. Si no, el dot/
  hidden quedaba apuntando al Anchor, el snapshot guardaba el Anchor como input
  original, y al cancelar (que borra el Anchor) la referencia moria y el nodo
  quedaba desconectado. **Sintoma:** accept andaba pero cancel dejaba todo suelto.
- **Las creaciones de Wired no splicean** porque cada `create_wired_above` hace
  `deselect_all()` al final, dejando la seleccion limpia para la siguiente.
- **Undo del usuario + callbacks de Stamps:** al hacer Ctrl+Z, Nuke recrea nodos y
  dispara `knobChanged`; con el lock ya restaurado (False) eso tira el error
  `n.inputs()` sobre nodos detached. Pasa cuando el historial tiene "churn" de
  crear/revertir (recrear Wireds = setear knobs = disparar callbacks). **Solucion
  (v0.06):** two-phase. La fase preview corre con `nuke.Undo().disable()` (no graba)
  y revierte cada grupo; la fase apply graba solo creaciones limpias de los
  aceptados en un unico `nuke.Undo()`. Asi el Ctrl+Z deshace creaciones (= deletes,
  que no setean knobs) sin disparar la avalancha.
- **`nuke.Undo().disable()` / `.enable()`** desactivan el registro del historial.
  Hay que balancearlos con try/finally. Las decisiones del preview se casan con los
  grupos del apply por una clave estable basada en nombres de nodo (no cambian al
  revertir): `H|<source>`, `D|<source>`, `L|<src>|<dst>|<idx>`.
- **Cancel sin romper el Undo:** NO usar undo nativo por grupo. Se revierte a mano
  (`GroupTx.revert`) dentro del mismo `nuke.Undo`. Asi un solo Ctrl+Z deshace todo
  lo aceptado y los cancelados quedan en neto cero.
- **Recrear Dots borrados (cancel):** se guarda snapshot (pos, label, hide_input,
  tile_color, input desde source/otro Dot, destinos externos) y en `restore_dots`
  se crean, se renombran a su nombre original (ya libre) y se reconectan. Las
  conexiones son por referencia, asi que aunque falle el `setName` el grafo queda
  funcionalmente igual.
- **Reconexiones a un Dot que se borra** no se trackean con `change_input` (la
  referencia al Dot muere); se hacen con `setInput` plano y las restaura el
  snapshot del Dot. Solo se trackean inputs cuyo viejo valor sobrevive (el source).

---

## Pendientes / Roadmap

- [x] Caso simple (2 nodos lejanos) — v0.01.
- [x] Caso Dot → multiples destinos: 1 Anchor en la fuente + 1 Wired por destino — v0.02.
- [x] Filtrar para no actuar sobre nodos que ya son Stamps/Dots.
- [x] Caso hidden inputs (Dot y no-Dot) con regla del label y reuse de Anchor — v0.03.
- [x] Reusar Anchor existente si la fuente ya tiene uno (al menos en el pase de hidden inputs).
- [x] Confirmacion por grupo (cartel nombre + Reemplazar/Cancelar) con zoom-to-fit
      y revert manual sin romper el Undo — v0.04.
- [x] Zoom al contexto (source + destinos) y cartel no bloqueante — v0.05.
- [ ] Extender el reuse de Anchor a TODOS los pases (hoy el pase 1 y 2 pueden
      duplicar Anchor si la misma fuente aparece en varios casos).
- [ ] Restaurar la vista (zoom/scroll) original al terminar (hoy queda en el ultimo grupo).
- [ ] Hacer el cartel mas lindo (estilo, atajos).
- [x] Two-phase (preview con undo deshabilitado + apply limpio): los grupos
      cancelados no dejan churn y un Ctrl+Z no tira la avalancha de errores — v0.06.
- [ ] Caso ruteo por Dots con **1 solo destino** (codos de ruteo largo).
- [ ] Hidden input en input distinto de 0 (ej. mask): hoy asumimos `input(0)`.
- [ ] Multi-input al mismo destino (origen llega por input 0 y 1): hoy crea 2
      Wireds que pueden solaparse arriba del destino.
- [ ] Decidir el criterio de distancia (¿euclidea, solo vertical, solo horizontal?).
- [ ] Opcion de trabajar solo sobre la seleccion vs. todo el script.
- [ ] Registro en `menu.py` (atajo + icono) cuando este maduro.
