# LGA_AutoStamps

Herramienta para Nuke que detecta conexiones "problematicas" entre nodos y las
reemplaza automaticamente por **Stamps** (sistema de Adrian Pueyo), dejando el
Node Graph mas limpio y legible.

---

## Objetivo general

Encontrar y reemplazar por Stamps:

1. **Conexiones muy largas** entre dos nodos lejanos. *(en desarrollo)*
2. **Conexiones desde un nodo a un Dot y de ahi a multiples lugares** (un Dot que
   distribuye una misma salida a varios destinos). *(pendiente)*
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

## Estado actual: v0.1 (simple)

**Archivo:** `py/LGA_AutoStamps.py` — funcion principal `main()`.

### Que hace

1. Recorre **todas** las conexiones del script (`node.input(i)` de cada nodo).
2. Mide la **distancia euclidea** entre los centros del nodo padre (fuente) y el
   hijo (destino).
3. Si la distancia supera `DISTANCE_THRESHOLD`:
   - Crea un **Anchor** justo debajo del padre y lo conecta a el.
   - Crea un **Wired** justo arriba del hijo.
   - Reconecta el input del hijo al Wired (lo que desconecta del padre).
4. Todo dentro de un bloque `nuke.Undo()` para poder deshacer en un paso.

### Variables de configuracion (arriba del archivo)

- `DISTANCE_THRESHOLD = 250` — umbral de distancia en px.
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
- Medimos distancia entre **centros** (`xpos + screenWidth/2`, `ypos + screenHeight/2`),
  no entre esquinas.
- `setInput(i, nuevoNodo)` reemplaza el input anterior: no hace falta desconectar
  a mano antes de reconectar.

---

## Pendientes / Roadmap

- [ ] Confirmar que el caso simple (2 nodos) funciona bien en Nuke real.
- [ ] Decidir el criterio de distancia (¿euclidea, solo vertical, solo horizontal?).
- [ ] Reusar Anchor existente si la fuente ya tiene uno (evitar duplicados).
- [ ] Caso Dot → multiples destinos: 1 Anchor en la fuente + 1 Wired por destino.
- [ ] Caso hidden inputs / clones.
- [ ] Filtrar para no actuar sobre nodos que ya son Stamps/Dots.
- [ ] Opcion de trabajar solo sobre la seleccion vs. todo el script.
- [ ] Registro en `menu.py` (atajo + icono) cuando este maduro.
