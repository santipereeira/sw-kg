# Knowledge Graph Construction from CSV (LOT4KG – Tarea 4)

## 1. Descripción del dataset

El dataset utilizado contiene información sobre los Juegos Deportivos Municipales de Madrid. Incluye datos relativos a:

* Partidos (fecha, resultado, equipos participantes, campo, etc.)
* Equipos
* Competiciones
* Grupos y fases
* Campos deportivos
* Distritos municipales
* Temporadas

Los datos están distribuidos en múltiples ficheros CSV relacionados entre sí mediante identificadores.

---

## 2. Modelado del Knowledge Graph

Se ha construido un Knowledge Graph siguiendo la ontología definida en las tareas anteriores. Las principales entidades modeladas son:

* **Partido**
* **Equipo**
* **Competicion**
* **Grupo**
* **Fase**
* **Campo**
* **DistritoMunicipal**
* **Temporada**

### Decisiones de modelado

* Las URIs se han construido utilizando los identificadores presentes en los CSV (por ejemplo: `ex:Partido/1234`).
* Se ha mantenido una estructura consistente y legible para todas las URIs.
* Los atributos numéricos se han tipado utilizando `xsd:integer` y `xsd:decimal`.
* Las relaciones entre entidades (por ejemplo, partido–equipo o partido–campo) se han definido mediante joins en YARRRML.

---

## 3. Proceso de transformación

El proceso seguido para la construcción del Knowledge Graph ha sido el siguiente:

### 3.1 Definición de mappings en YARRRML

Se han definido mappings declarativos en el fichero:

```
mappings/mapping.yarrrml.yaml
```

En ellos se especifica:

* La fuente de datos (CSV)
* La construcción de sujetos (URIs)
* Las propiedades y atributos
* Las relaciones entre entidades mediante condiciones

---

### 3.2 Traducción a RML con Yatter

Los mappings en YARRRML se han traducido a RML mediante el siguiente comando:

```
python -m yatter -i mappings/mapping.yarrrml.yaml -o mappings/mapping.rml.ttl
```

Este paso genera un fichero RDF que describe las reglas de transformación.

---

### 3.3 Generación del Knowledge Graph con Morph-KGC

Se ha utilizado Morph-KGC para materializar el grafo RDF a partir de los mappings.
El fichero de configuración se encuentra en `mappings/config.ini`, por lo que el
comando debe ejecutarse desde la carpeta `task4`:

```
python -m morph_kgc mappings/config.ini
```

El resultado es un fichero RDF con todas las instancias y relaciones:

```
kg/output.nt
```

---

## 4. Resultado del Knowledge Graph

El fichero completo del Knowledge Graph generado con Morph-KGC (`kg/output.nt`) no se
incluye en el repositorio porque su tamaño es elevado para una entrega en GitHub.

En su lugar, se incluye una muestra reducida del resultado en:

```bash
kg/output_sample.nt
```

Esta muestra contiene 1000 triples RDF en formato N-Triples y permite revisar la
estructura general del grafo generado, incluyendo URIs, tipos RDF, propiedades de datos y
relaciones entre recursos.

El Knowledge Graph completo puede regenerarse localmente desde la carpeta `task4`
utilizando los siguientes archivos:

* `data/*.csv`
* `mappings/mapping.yarrrml.yaml`
* `mappings/mapping.rml.ttl`
* `mappings/config.ini`

Si se modifica el fichero YARRRML, primero debe regenerarse el mapping RML con Yatter:

```bash
python -m yatter -i mappings/mapping.yarrrml.yaml -o mappings/mapping.rml.ttl
```

Después, se ejecuta Morph-KGC desde la carpeta `task4`:

```bash
python -m morph_kgc mappings/config.ini
```

El resultado completo se genera en:

```bash
kg/output.nt
```

En la versión completa generada durante la práctica, el Knowledge Graph contiene
**298.653 triples RDF**, calculados con:

```bash
wc -l kg/output.nt
```

El grafo contiene instancias de todas las entidades definidas y relaciones entre ellas.

---

## 5. Validación del resultado

Se ha realizado una validación manual del Knowledge Graph, comprobando:

* La correcta generación del fichero RDF
* La existencia de las entidades esperadas
* La coherencia de las URIs
* La correcta asignación de tipos RDF (`rdf:type`)
* La correcta generación de relaciones entre entidades (joins)
* La ausencia de valores incorrectos o mal formados

Se ha verificado manualmente el Knowledge Graph comprobando:

- La existencia de instancias de todas las entidades (Partido, Equipo, Campo, etc.)
- La correcta asignación de tipos RDF (rdf:type)
- La correcta generación de relaciones entre entidades (por ejemplo, partido–equipo)
- La consistencia de las URIs generadas
---

## 6. Problemas encontrados y soluciones

Durante el desarrollo de la práctica se han identificado varios problemas:

* **Inconsistencias en nombres de columnas**
  - Se han ajustado los mappings para coincidir exactamente con los CSV.

* **Regeneración del mapping RML**
  - Fue necesario regenerar el `.ttl` tras cambios en el YARRRML.

* **Duplicados en CSV auxiliares**
  - Se eliminaron filas duplicadas exactas en `competicion.csv`, `distritoMunicipal.csv`,
  `equipo.csv`, `fase.csv`, `grupo.csv` y `temporada.csv`.

* **Filas mal parseadas en `campo.csv`**
  - Se corrigieron registros en los que comas internas del nombre del campo habían
  desplazado valores hacia las columnas `coordX`, `coordY` o `nombreDistrito`.

* **Campos sin identificador válido**
  - Se eliminaron de `campo.csv` las filas con `codigoCampo` igual a `0` para evitar
  la generación del recurso artificial `Campo/0`.
  - Algunos partidos mantienen `codigoCampo` igual a `0` en `partidos.csv`. Estos casos
  se interpretan como partidos con campo desconocido, por lo que no generan una relación
  válida `ta:seJuegaEn` hacia un recurso de tipo `Campo`.

---

## 7. Conclusión

Se ha construido un Knowledge Graph a partir de datos tabulares en CSV siguiendo la metodología LOT4KG.

El resultado representa las principales entidades del dataset y sus relaciones. Tras la
deduplicación de los CSV auxiliares, la corrección de `campo.csv` y la regeneración del
mapping RML, se ha generado una versión más consistente del Knowledge Graph.
