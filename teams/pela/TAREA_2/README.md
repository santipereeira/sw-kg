# Tarea 2 — Limpieza y Preparación de Datos con OpenRefine

## Dataset

**Nombre:** Competiciones deportivas municipales de deportes colectivos — Temporada 2014/2015  
**Fuente:** [datos.gob.es](https://datos.gob.es/es/catalogo/l01280796-deportes-competiciones-deportivas-municipales-de-deportes-colectivos-temporadas-anteriores)  
**Archivo original:** `data/raw_partidos_2014_2015.csv`  
**Registros:** 43 596 filas | Separador: `;` | Codificación original: IBM866  

El dataset contiene una fila por partido disputado en competición local del Ayuntamiento de Madrid, con columnas para el deporte, sistema de competición, temporada, grupo, categoría, fase, jornada, equipos (local y visitante), marcador, campo (con coordenadas), distrito y estado del partido.

---

## Problemas de calidad detectados

| Problema | Columnas afectadas | Tipo |
|---|---|---|
| Fechas en formato `DD/MM/YYYY` | `Fecha` | Formato no estándar |
| Hora separada de la fecha | `Hora` | Campos a combinar |
| Horas de un solo dígito (`9:00`) | `Hora` | Formato incorrecto |
| Códigos numéricos guardados como texto | `Codigo_grupo`, `Jornada`, `Partido`, `Codigo_equipo1/2`, `Resultado1/2`, `Codigo_campo` | Tipo incorrecto |
| Coordenadas como texto | `COORD_X_CAMPO`, `COORD_Y_CAMPO` | Tipo incorrecto |
| Valores de estado inconsistentes (`F`, `S`, `O`, `a`, `C`, celdas vacías) | `Estado` | Inconsistencia tipográfica |
| Filas con código de equipo o campo = 0 (sin datos de campo/equipo) | `Codigo_equipo1`, `Codigo_equipo2`, `Codigo_campo` | Valores inválidos |
| Columnas redundantes o no necesarias | `Observaciones`, `Codigo_competicion`, `Codigo_temporada`, `Nombre_competicion`, `Nombre_jornada`, `Codigo_fase` | Columnas a eliminar |
| Espacios en blanco al final de cadenas | `Nombre_deporte`, `Nombre_categoria`, etc. | Ruido tipográfico |
| Entidades textuales no enlazadas a LOD | `Nombre_deporte`, `Distrito` | Sin identificadores semánticos |

---

## Operaciones de limpieza aplicadas (OpenRefine)

El historial completo y reproducible se encuentra en `data/history.json`.

### 1. Eliminación de columnas no necesarias

Se eliminaron las columnas `Observaciones`, `Codigo_competicion`, `Codigo_temporada`, `Nombre_competicion`, `Nombre_jornada` y `Codigo_fase`, que o bien estaban vacías, eran redundantes con otras columnas más legibles, o no aportaban información relevante para la ontología.

### 2. Normalización del formato de fecha

La columna `Fecha` venía en formato `DD/MM/YYYY`. Se transformó a `YYYY/MM/DD` con la expresión GREL:

```grel
value.split('/')[2] + '/' + value.split('/')[1] + '/' + value.split('/')[0]
```

A continuación se convirtió al tipo fecha interno de OpenRefine con `value.toDate()`.

### 3. Construcción de la columna `Fecha_Hora`

Se creó una nueva columna `Fecha_Hora` combinando la fecha ISO con el valor de la columna `Hora`:

```grel
value.substring(0, 11) + cells["Hora"].value + ":00Z"
```

Esto genera timestamps del tipo `2014-09-27T10:30:00Z`. La columna resultante se convirtió a fecha. Una vez creada `Fecha_Hora`, se eliminaron las columnas originales `Fecha` y `Hora`.

### 4. Corrección de horas de un solo dígito

Algunos partidos tenían horas registradas como `T9:00:00Z` en lugar de `T09:00:00Z`, lo que rompe el estándar ISO 8601. Se corrigió con la expresión:

```grel
value.replace(/T(\d):/, "T0$1")
```

### 5. Tipado de columnas numéricas

Se convirtieron a número (`value.toNumber()`) las columnas: `Codigo_grupo`, `Jornada`, `Partido`, `Codigo_equipo1`, `Codigo_equipo2`, `Resultado1`, `Resultado2`, `Codigo_campo`, `COORD_X_CAMPO`, `COORD_Y_CAMPO`.

### 6. Normalización del campo `Estado`

Los valores originales eran códigos de una letra. Se normalizaron a valores legibles:

```grel
if(value.trim().length() == 0, "no jugado",
  if(or(value.trim().toLowercase() == "o", value.trim().toLowercase() == "a"), "aplazado",
    if(value.trim().toLowercase() == "f", "finalizado",
      if(value.trim().toLowercase() == "s", "suspendido", value)
    )
  )
)
```

También se normalizaron variantes del tipo `"No presentado..."` → `"No presentado"`.

### 7. Eliminación de filas con datos inválidos

Se eliminaron las filas donde `Codigo_equipo1`, `Codigo_equipo2` o `Codigo_campo` tuviesen valor `0`, ya que representan partidos sin equipo o campo asignado y no son representables en el grafo.

Se eliminaron también las filas con `Estado == "C"` (registros cancelados sin datos de resultado).

### 8. Reconciliación de entidades con Wikidata

#### Columna `Nombre_deporte` → tipo Wikidata `Q31629` (tipo de deporte)

Se reconciliaron los deportes presentes en el dataset contra Wikidata:

| Valor original | Enlace Wikidata |
|---|---|
| FUTBOL | [Q1081491](http://www.wikidata.org/entity/Q1081491) — football |
| VOLEIBOL | [Q1734](http://www.wikidata.org/entity/Q1734) — volleyball |
| HOCKEY | [Q1622659](http://www.wikidata.org/entity/Q1622659) — hockey |
| MINIBALONCESTO | [Q114049601](http://www.wikidata.org/entity/Q114049601) — minibasketball |
| (otros deportes) | reconciliados automáticamente |

Se añadió la columna `Deporte_ID` extrayendo el identificador Wikidata: `cell.recon.match.id`.

#### Columna `Distrito` → tipo Wikidata `Q3032114` (distrito de Madrid)

Se reconciliaron los distritos de Madrid contra Wikidata. Se añadió la columna `Distrito_ID` con el identificador Wikidata correspondiente. Los distritos con puntuación de `recon < 90` se marcaron como nulos para no introducir enlaces erróneos.

---

## Archivos entregados

| Archivo | Descripción |
|---|---|
| `data/raw_partidos_2014_2015.csv` | Dataset original sin modificar |
| `data/clean_partidos_2014_2015.csv` | Dataset limpio exportado desde OpenRefine |
| `data/history.json` | Historial de operaciones exportado desde OpenRefine (reproducible) |

> **Nota:** El archivo limpio para la construcción del KG se denomina `ontologia-deportes.csv` y se encuentra en `TAREA_4/data/`, ya que en esa tarea se añadieron columnas con IDs de Wikidata y se realizaron los últimos ajustes de formato requeridos por el mapping.
