# Práctica: Construcción de Knowledge Graphs a partir de CSV (LOT4KG – Tarea 4)

En esta práctica vais a realizar la Tarea 4 de la metodología \[LOT\]4KG: la construcción del Knowledge Graph a partir de fuentes tabulares en CSV. El objetivo es definir los mappings que transforman los datos a RDF y ejecutar el proceso completo de generación del grafo siguiendo el flujo visto en clase.

Herramientas obligatorias:
- Definición de mappings: YARRRML
- Traducción de mappings: Yatter
- Construcción del grafo: Morph-KGC



## Objetivo

A partir de vuestro dataset en CSV y de la ontología/modelo ya definido en las tareas anteriores, debéis:
1. Analizar la estructura de los CSV y decidir cómo se transforman a RDF.
2. Crear los mappings en YARRRML siguiendo la presentación de clase.
3. Traducir esos mappings a RML con Yatter.
4. Ejecutar Morph-KGC para construir el Knowledge Graph final.
5. Revisar el resultado generado y comprobar que el grafo representa correctamente los datos.

⸻

## Requisitos y entrega

Debéis entregar en vuestra carpeta del repositorio una estructura similar a esta:

- data/
	- \*.csv
- mappings/
	- mapping.yarrrml.yaml
	- mapping.rml.ttl
	- config.ini
- kg/
	- output.ttl
- README.md

El `README.md` debe incluir:
- una breve descripción del dataset usado,
- una explicación breve de cómo habéis modelado la transformación,
- los comandos utilizados para ejecutar Yatter y Morph-KGC,
- observaciones o decisiones de diseño relevantes.

⸻

## Flujo de trabajo

### 1) Análisis del dataset CSV

Antes de empezar a escribir mappings, revisad bien los ficheros CSV:
- qué representa cada fichero,
- qué columnas identifican entidades,
- qué columnas son atributos literales,
- qué columnas generan relaciones entre entidades,
- qué valores necesitan limpieza o transformación básica.

Recomendaciones:
- No intentéis mapear todo de golpe.
- Empezad por una entidad principal y unos pocos atributos, y ampliad después.

⸻

### 2) Creación de los mappings en YARRRML

Debéis definir los mappings en YARRRML siguiendo la sintaxis y los ejemplos vistos en la presentación:
- fuentes (`sources`) asociadas a cada CSV,
- sujetos (`s`) con plantillas de URI bien definidas,
- tipos RDF (`a`),
- predicados y objetos para atributos literales,
- relaciones entre recursos cuando corresponda.

Checklist mínimo:
- uso consistente de prefijos,
- URIs bien construidas y estables,
- uso de clases y propiedades acordes con vuestra ontología o modelo.

Recomendaciones:
- Usad identificadores del CSV para construir URIs siempre que sea posible.
- Mantened nombres legibles y consistentes.

⸻

### 3) Traducción de YARRRML a RML con Yatter

Una vez definidos los mappings en YARRRML, debéis traducirlos a RML utilizando Yatter.

El objetivo de este paso es obtener el fichero RDF con los mappings en un formato que pueda ejecutar Morph-KGC.


⸻

### 4) Construcción del grafo con Morph-KGC

Con el mapping ya traducido a RML, debéis configurar y ejecutar Morph-KGC para materializar el grafo RDF.

Para ello:
1. Preparad el fichero de configuración correspondiente.
2. Indicad la ruta del mapping RML.
3. Indicad el formato de salida.
4. Ejecutad Morph-KGC para generar el Knowledge Graph.

El resultado debe ser un fichero RDF con las instancias y relaciones extraídas desde los CSV.

⸻

### 5) Validación básica del resultado

Una vez generado el Knowledge Graph, debéis comprobar al menos:
- que el fichero RDF se genera correctamente,
- que aparecen las entidades esperadas,
- que las URIs siguen el patrón definido,
- que los tipos y propiedades son coherentes,
- que no se están generando relaciones incorrectas por errores en el mapping.

Recomendaciones:
- Revisad manualmente algunos recursos concretos.
- Comprobad especialmente los joins, referencias entre CSV y construcción de URIs.

⸻

## Qué se espera de la práctica

No se evalúa únicamente que “se genere un TTL”, sino que:
- el mapping esté bien planteado,
- la transformación sea coherente con el modelo de conocimiento,
- las URIs y clases estén bien elegidas,
- el resultado sea interpretable y reutilizable.

Es preferible un grafo más pequeño pero correctamente construido que un resultado más grande con errores conceptuales o estructurales.

⸻

## Entrega final

Debéis subir al repositorio:
- los CSV utilizados,
- el fichero YARRRML,
- el mapping traducido a RML,
- la configuración de Morph-KGC,
- el grafo RDF generado,
- el `README.md` explicando el proceso.