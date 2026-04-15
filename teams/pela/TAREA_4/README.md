# Tarea 4 — Construcción del Knowledge Graph (LOT4KG)

## Dataset utilizado

Se emplea el archivo **`data/ontologia-deportes.csv`**, resultado de la limpieza realizada en la Tarea 2 con OpenRefine. Este CSV es una versión enriquecida del original que incorpora:

- Columna `Fecha_Hora`: timestamp ISO 8601 combinando fecha y hora del partido (`YYYY-MM-DDTHH:MM:00Z`)
- Columna `Deporte_ID`: identificador Wikidata del deporte (obtenido por reconciliación)
- Columna `Distrito_ID`: identificador Wikidata del distrito (obtenido por reconciliación)
- Tipos de datos corregidos (campos numéricos, booleanos, coordenadas)
- Valores de estado normalizados (`finalizado`, `aplazado`, `suspendido`, `no jugado`, `No presentado`)

El CSV contiene aproximadamente **43 596 filas** y cubre la temporada 2014–2015 de competiciones deportivas municipales de deportes colectivos del Ayuntamiento de Madrid.

---

## Diseño del mapping

El mapping sigue la estructura jerárquica definida en la ontología (`TAREA_3/ontology/ontology.ttl`), con el namespace base `https://example.org/partidos/` (prefijo `ns:`).

### Entidades mapeadas y construcción de URIs

| Mapping | Clase | URI generada (ejemplo) |
|---|---|---|
| `deporte` | `ns:Deporte` | `ns:deporte/FUTBOL` |
| `competicion` | `ns:Competicion` | `ns:competicion/LIGA_2014/2015_FUTBOL` |
| `grupo` | `ns:Grupo` | `ns:grupo/12345` |
| `jornada` | `ns:Jornada` | `ns:jornada/12345_3` |
| `partido` | `ns:Partido` | `ns:partido/12345_3_2` |
| `equipo_local` | `ns:Equipo` | `ns:equipo/678` |
| `equipo_visitante` | `ns:Equipo` | `ns:equipo/901` |
| `campo` | `ns:Campo` | `ns:campo/42` |
| `distrito` | `ns:Distrito` | `ns:distrito/Arganzuela` |

Las URIs se construyen siempre a partir de **identificadores numéricos del CSV** (`Codigo_grupo`, `Jornada`, `Partido`, `Codigo_equipo1/2`, `Codigo_campo`) o de valores canónicos tras limpieza (`Nombre_deporte`, `Distrito`), garantizando estabilidad y ausencia de colisiones.

### Relaciones entre entidades (joins)

Las relaciones entre clases se modelan mediante referencias explícitas a URIs con la directiva `~iri` de YARRRML:

```yaml
- [ns:tipoDe,      ns:deporte/$(Nombre_deporte)~iri]
- [ns:tieneGrupo,  ns:grupo/$(Codigo_grupo)~iri]
- [ns:tieneJornada, ns:jornada/$(Codigo_grupo)_$(Jornada)~iri]
- [ns:tienePartido, ns:partido/$(Codigo_grupo)_$(Jornada)_$(Partido)~iri]
- [ns:ocurreEn,    ns:campo/$(Codigo_campo)~iri]
- [ns:localizadoEn, ns:distrito/$(Distrito)~iri]
- [ns:sameAsDeporte, wd:$(Deporte_ID)~iri]
- [ns:sameAsDistrito, wd:$(Distrito_ID)~iri]
```

El uso de `~iri` es imprescindible para que Morph-KGC codifique correctamente caracteres especiales (barras `/`, espacios, etc.) en las URIs de los joins.

---

## Comandos de ejecución

### Paso 1: Instalación de dependencias

```bash
pip install yatter morph-kgc
```

### Paso 2: Traducción de YARRRML a RML con Yatter

```bash
cd TAREA_4
yatter -i mappings/mapping.yarrrml.yaml -o mappings/mapping.rml.ttl
```

Esto genera el fichero `mappings/mapping.rml.ttl` con los mappings en formato RML estándar, que es el que consume Morph-KGC.

### Paso 3: Generación del Knowledge Graph con Morph-KGC

```bash
python3 -m morph_kgc mappings/config.ini
```

El fichero de configuración `mappings/config.ini` especifica:

```ini
[CONFIGURATION]
na_values=NA,N/A,null
output_file=kg/output.ttl
output_format=N-TRIPLES

[DataSource]
mappings=mappings/mapping.rml.ttl
```

El resultado se escribe en `kg/output.nt` (N-Triples). Si Morph-KGC genera cabeceras de tipo `.nt`, el fichero puede renombrarse:

```bash
mv kg/output.nt kg/output.ttl
```

---

## Resultado generado

El Knowledge Graph materializado contiene **529 597 tripletas N-Triples** representando:

- Instancias de los 8 tipos de entidades definidos en la ontología
- Propiedades de datos tipadas (strings, integers, floats, booleans, dateTime)
- Relaciones entre entidades según la jerarquía de la ontología
- enlaces `sameAs` a recursos de Wikidata para deportes y distritos

---

## Observaciones y decisiones de diseño

- **URIs compuestas para identificar sin ambigüedad:** Las jornadas se identifican por `Codigo_grupo + Jornada`, y los partidos por `Codigo_grupo + Jornada + Partido`, porque en el CSV no existe un identificador único de partido. Esto refleja la estructura jerárquica del dominio.
- **`~iri` en los joins:** La directiva `~iri` en YARRRML es clave para que Morph-KGC no escape caracteres como `/` o espacios dentro de los valores usados como parte de URIs. Sin ella, se generarían URIs incorrectas en los joins.
- **Equipos duplicados para local y visitante:** Se definieron dos mappings separados (`equipo_local` y `equipo_visitante`) porque cada fila del CSV contiene los datos de ambos equipos en columnas distintas. Morph-KGC deduplica las instancias por URI al materializar.
- **Formato de salida N-Triples:** Se eligió N-Triples por su eficiencia en la serialización de grafos grandes y por ser el formato requerido en el script de validación de la Tarea 5.
- **Deporte como nodo reutilizado:** Al construir la URI del deporte desde `$(Nombre_deporte)`, un mismo deporte comparte la misma URI en todas sus filas, creando el nodo único correctamente sin necesidad de deduplicación manual.
