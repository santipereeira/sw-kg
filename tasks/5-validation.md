# Práctica: Validación del Knowledge Graph (LOT4KG – Tarea 5)

En esta práctica vais a realizar la Tarea 5 de la metodología LOT4KG: la validación del Knowledge Graph. El objetivo es generar restricciones de validación en SHACL a partir del grafo, la ontología y/o los mappings, y utilizarlas después para validar vuestro KG con `pyshacl`.

Herramientas recomendadas:
- Generación de shapes desde el grafo: SheXer, QSE o SCOOP
- Validación del grafo: pySHACL (o cualquier otra que se menciona en clase)

No es obligatorio usar las tres herramientas de generación de shapes. Basta con que utilicéis al menos una, aunque es recomendable comparar resultados si queréis enriquecer la práctica.

## Objetivo

A partir del Knowledge Graph construido en la tarea anterior, de vuestra ontología/modelo y de los mappings, debéis:

1. Generar un conjunto de shapes SHACL a partir del RDF materializado (QSE/Java o SheXer/Python).
2. Generar, si es posible, otro conjunto de shapes a partir de la ontología y/o de los mappings (SCOOP).
3. Revisar y ajustar las shapes generadas automáticamente si fuera necesario.
4. Validar el grafo con `pyshacl`.
5. Analizar el resultado de la validación e identificar posibles errores o inconsistencias.

⸻

## Requisitos y entrega

Debéis entregar en vuestra carpeta del repositorio una estructura similar a esta:

- shapes/
	- shapes_from_data.ttl
	- shapes_from_ontology_or_mappings.ttl
	- validation/
		- validate_data_shapes.py
		- validate_ontology_or_mappings_shapes.py
		- report_data_shapes.ttl
		- report_model_shapes.ttl
- README.md

Si solo generáis un conjunto de shapes, podéis entregar únicamente un fichero de shapes y un script de validación, pero es preferible que comparéis al menos dos aproximaciones:
- una basada en el RDF materializado,
- otra basada en la ontología y/o los mappings.

El `README.md` debe incluir:
- una breve descripción del KG validado,
- qué herramienta habéis utilizado para generar las shapes,
- desde qué fuente habéis generado cada conjunto de shapes,
- los comandos o scripts utilizados,
- una breve interpretación de los resultados de validación,
- observaciones o decisiones de diseño relevantes.

⸻

## Flujo de trabajo

### 1) Preparación de los recursos a validar

Antes de generar las shapes, debéis tener localizados y organizados al menos estos elementos:
- el grafo RDF materializado en la tarea anterior,
- la ontología o vocabulario usado en vuestro proyecto,
- los mappings definidos en RML.

El objetivo es que podáis contrastar dos perspectivas:
- lo que realmente aparece en los datos,
- lo que vuestro modelo espera o prescribe.

Recomendación:
- No asumáis que las shapes generadas automáticamente son correctas sin revisión.
- La validación es útil precisamente para detectar incoherencias entre datos, modelo y transformación.

⸻

### 2) Generación de shapes a partir del RDF

Debéis utilizar SheXer o QSE para inferir restricciones a partir del grafo RDF materializado.

Estas herramientas permiten extraer patrones estructurales del grafo, por ejemplo:
- qué clases aparecen,
- qué propiedades suelen tener las instancias,
- qué tipos de valores se observan,
- qué cardinalidades parecen frecuentes o esperables.

El resultado de este paso debe ser un fichero de shapes SHACL, por ejemplo:

- `shapes/shapes_from_data.ttl`

Recomendaciones:
- Revisad si la herramienta está generando shapes demasiado permisivas o demasiado específicas.
- Comprobad si aparecen restricciones inducidas por ruido o por casos muy concretos del dataset.
- Si la herramienta lo permite, ajustad parámetros para obtener shapes más útiles.

⸻

### 3) Generación de shapes a partir de la ontología y/o los mappings

Además de las shapes extraídas del RDF, debéis intentar obtener un segundo conjunto de shapes a partir del conocimiento de diseño:
- la ontología,
- los mappings.

La idea es capturar restricciones que no siempre pueden inferirse solo observando datos, por ejemplo:
- clases esperadas,
- propiedades obligatorias según el modelo,
- rangos o tipos de valores,
- relaciones que deberían existir aunque algún dato concreto no las materialice bien.

El resultado de este paso debe ser otro fichero, por ejemplo:

- `shapes/shapes_from_ontology_or_mappings.ttl`

Importante:
- Si la generación no es completamente automática, podéis complementar o editar manualmente las shapes.
- Se valorará positivamente que expliquéis qué parte proviene de generación automática y qué parte habéis refinado vosotros.

⸻

### 4) Revisión y ajuste de las shapes

Antes de validar con `pyshacl`, debéis revisar las shapes generadas.

Checklist mínimo:
- que las clases objetivo (`sh:targetClass`) tengan sentido,
- que las propiedades restringidas correspondan con vuestro modelo,
- que los datatypes sean razonables,
- que las cardinalidades mínimas y máximas no sean arbitrarias,
- que no se estén introduciendo restricciones por accidente debido a sesgos del dataset.

Recomendación:
- No hace falta que construyáis unas shapes perfectas ni completas.
- Sí hace falta que se entienda que habéis reflexionado sobre su utilidad y limitaciones.

⸻

### 5) Validación con pySHACL

Una vez preparadas las shapes, debéis validar el Knowledge Graph utilizando `pyshacl`.

Debéis entregar los scripts de validación (puede ser un solo script con CLI para pasarle el fichero de shapes como entrada). Por ejemplo:
- `validation/validate_data_shapes.py`
- `validation/validate_model_shapes.py`

El script debe:
1. cargar el grafo RDF,
2. cargar el fichero de shapes correspondiente,
3. ejecutar la validación con `pyshacl`,
4. mostrar por pantalla si el grafo conforma o no,
5. guardar, si es posible, el informe de validación (esto es otro grafo en RDF).

El resultado de la validación puede ser, por ejemplo:
- conformidad total,
- violaciones de cardinalidad,
- valores con datatype incorrecto,
- ausencia de propiedades obligatorias,
- recursos que no cumplen la estructura esperada.

Recomendaciones:
- Guardad también los informes de validación en RDF.
- Si el grafo no conforma, intenta entender dónde está el problema, si en los datos o en las shapes.
- Si se puede, revisa la generación del RDF o las shapes para tratar de obtener una conformidad total.

⸻

## Qué se espera de la práctica

No se evalúa únicamente que “pySHACL se ejecute”, sino que:
- hayáis generado shapes de forma razonada,
- entendáis la diferencia entre validar contra patrones observados en los datos y validar contra restricciones del modelo,
- sepáis interpretar los resultados,
- detectéis problemas reales del KG, de la ontología o de los mappings.
⸻

## Posibles enfoques de validación

Podéis plantear la práctica de varias formas. Por ejemplo:

### Enfoque 1: Validación basada en datos
- Generáis shapes desde el RDF con SheXer, QSE o SCoop.
- Validáis el propio KG frente a esas shapes.
- Analizáis qué patrones estructurales se repiten y cuáles no.

### Enfoque 2: Validación basada en modelo
- Generáis o definís shapes a partir de la ontología y/o de los mappings.
- Validáis el KG frente a restricciones más normativas.
- Analizáis si los datos construidos cumplen lo que vuestro modelo pretendía representar.

### Enfoque 3: Comparación entre ambos
- Validáis el mismo KG con shapes derivadas de los datos y con shapes derivadas del modelo.
- Comparáis diferencias.
- Discutís qué enfoque detecta mejor determinados errores.

Este tercer enfoque es especialmente interesante porque muestra la diferencia entre:
- describir cómo son los datos,
- prescribir cómo deberían ser.

⸻

## Entrega final

Debéis subir al repositorio:
- uno o dos ficheros de shapes SHACL,
- los scripts de validación con `pyshacl`,
- los informes de validación generados,
- el `README.md` explicando el proceso y los resultados.

## Nota importante

La práctica no consiste solo en “pasar un validador”, sino en utilizar la validación como mecanismo para inspeccionar la calidad del Knowledge Graph.

Por tanto, debéis prestar atención a preguntas como:
- ¿qué restricciones aparecen si observo solo los datos?
- ¿qué restricciones debería imponer realmente mi modelo?
- ¿qué errores del mapping o del dataset afloran al validar?
- ¿qué limitaciones tienen las shapes generadas automáticamente?
