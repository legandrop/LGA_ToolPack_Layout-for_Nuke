> **Regla de documentacion**: este archivo describe el estado actual del codigo. No es un historial de cambios, changelog ni bitacora temporal.
> **Regla de documentacion**: este archivo debe incluir una seccion de referencias tecnicas con rutas completas a los archivos mas importantes relacionados, y para cada archivo nombrar las funciones, clases o metodos clave vinculados a este tema.

# LGA Check JSON Arrange

Este script valida si un **graph JSON** ya está correctamente *arranged*,
usando **solo el JSON** (sin `.nk`).

## Reglas actuales (2026-02-06)

1. **Alineación Y entre columnas**
   - Si dos nodos conectados están en **columnas distintas**, deben estar
     alineados en Y **de forma centrada**.
   - Se compara la **posición central** de cada nodo (`y`) y se considera su
     tamaño (`height`).
   - La alineación es válida si la diferencia de centros es menor o igual a
     **(h1 + h2) / 2** (overlap vertical de sus bounding boxes).

2. **Sin superposición en la misma columna**
   - Dentro de una misma columna no puede haber nodos cuyos bounding boxes
     se solapen en Y.

## Uso

```bash
python LGA_check_JSON_arrange.py -- /ruta/al/graph.json
```

## Salida

Genera un `.txt` en castellano al lado del JSON con el resultado:
- `OK: ...` si no hay problemas
- `FALLA: ...` con el listado de issues detectados
