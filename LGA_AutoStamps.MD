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
3. **Conexiones con hidden inputs** (inputs ocultos / clones a distancia). *(pendiente)*

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

`main()` corre tres pases dentro de un unico bloque `nuke.Undo()`:

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

### Variables de configuracion (arriba del archivo)

- `DISTANCE_THRESHOLD = 250` — umbral de distancia en px (pase 2).
- `MIN_DESTINATIONS = 3` — minimo de destinos para colapsar un arbol de Dots (pase 1).
- `ANCHOR_GAP_Y = 40` — separacion vertical padre → Anchor.
- `WIRED_GAP_Y = 40` — separacion vertical Wired → hijo.
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
- **Reuse de Anchor:** `get_or_create_anchor` usa un `registry` por
  `source.name()` + busca Anchors existentes con ese `input(0)`. El `title` solo
  se aplica al crearlo; si se reusa, se mantiene el del primero.
- El `label` se toma como `label.split("\n")[0].strip()` (primera linea limpia).
- En el pase de hidden inputs, los **Dots de ruteo** del pase 1 se distinguen de
  los **pickups ocultos** por `hide_input`: `collect_dot_tree` ignora los Dots con
  `hide_input` activo.
- **No usar un nodo despues de `nuke.delete()`:** da
  `ValueError: A PythonObject is not attached to a node`. Hay que capturar lo que
  se necesite (ej. `node.name()`) ANTES de borrar. Si el error salta dentro del
  `try` del Undo, aborta los pases siguientes y parece que "se rompio todo".

---

## Pendientes / Roadmap

- [x] Caso simple (2 nodos lejanos) — v0.01.
- [x] Caso Dot → multiples destinos: 1 Anchor en la fuente + 1 Wired por destino — v0.02.
- [x] Filtrar para no actuar sobre nodos que ya son Stamps/Dots.
- [x] Caso hidden inputs (Dot y no-Dot) con regla del label y reuse de Anchor — v0.03.
- [x] Reusar Anchor existente si la fuente ya tiene uno (al menos en el pase de hidden inputs).
- [ ] Extender el reuse de Anchor a TODOS los pases (hoy el pase 1 y 2 pueden
      duplicar Anchor si la misma fuente aparece en varios casos).
- [ ] Caso ruteo por Dots con **1 solo destino** (codos de ruteo largo).
- [ ] Hidden input en input distinto de 0 (ej. mask): hoy asumimos `input(0)`.
- [ ] Multi-input al mismo destino (origen llega por input 0 y 1): hoy crea 2
      Wireds que pueden solaparse arriba del destino.
- [ ] Decidir el criterio de distancia (¿euclidea, solo vertical, solo horizontal?).
- [ ] Opcion de trabajar solo sobre la seleccion vs. todo el script.
- [ ] Registro en `menu.py` (atajo + icono) cuando este maduro.
