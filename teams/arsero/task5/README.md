# Validación del Knowledge Graph

## Descripción

En esta tarea se valida el Knowledge Graph generado en la Tarea 4 para el dominio de
los Juegos Deportivos Municipales de Madrid. El grafo validado corresponde a la versión
regenerada después de corregir los CSV auxiliares, reparar `campo.csv`, eliminar el
recurso artificial `Campo/0` y actualizar los mappings.

Recurso validado:

```bash
../task4/kg/output.nt
```

El grafo contiene 298.653 triples RDF en formato N-Triples.

---

## Enfoques de validación

Se han utilizado dos conjuntos de shapes SHACL para contrastar dos perspectivas:

* **Shapes generadas desde los datos**: describen la estructura observada directamente
  en el RDF materializado.
* **Shapes definidas desde el modelo**: recogen restricciones esperadas según la
  ontología y los mappings del proyecto.

Esto permite comparar la validación descriptiva, basada en lo que aparece en el KG, con
una validación más normativa, basada en lo que el modelo espera.

---

## Shapes desde los datos

Las shapes basadas en datos se generaron con **SheXer** a partir del KG materializado:

```bash
cd teams/arsero/task5
python -m shexer -i ../task4/kg/output.nt -o shapes/shapes_from_data.ttl -f nt
```

Después se revisó el fichero generado para asegurar que las restricciones fueran
compatibles con SHACL y pySHACL.

Fichero generado:

```bash
shapes/shapes_from_data.ttl
```

Estas shapes incluyen restricciones observadas para clases como `Partido`, `Campo`,
`Equipo`, `Competicion`, `Fase`, `Grupo`, `DistritoMunicipal` y `Temporada`.

---

## Shapes desde el modelo

Además de las shapes generadas automáticamente, se creó un segundo conjunto de shapes
a partir de la ontología y los mappings:

```bash
shapes/shapes_from_model.ttl
```

Estas shapes comprueban restricciones esperadas, por ejemplo:

* `Partido` debe tener fecha, jornada, número de partido, estado y programación.
* `Partido` debe relacionarse con competición, fase, grupo y equipos local/visitante.
* `Campo` debe tener nombre, coordenadas y distrito.
* `Equipo`, `Competicion`, `Fase`, `Grupo`, `DistritoMunicipal` y `Temporada` deben
  tener sus identificadores o nombres principales.

La relación `ta:seJuegaEn` no se marca como obligatoria con `sh:minCount 1` porque
algunos registros originales tienen `codigoCampo=0` en `partidos.csv`. Estos casos se
interpretan como partidos con campo desconocido y se evita generar un recurso artificial
`Campo/0`.

---

## Validación con pySHACL

La validación se realizó con **pySHACL** mediante dos scripts:

```bash
cd teams/arsero/task5/shapes/validation
python validate_data_shapes.py
python validate_model_shapes.py
```

Los scripts usan rutas robustas calculadas desde su propia ubicación, por lo que cargan
siempre el KG desde:

```bash
../../../task4/kg/output.nt
```

Informes generados:

```bash
shapes/validation/report_data_shapes.ttl
shapes/validation/report_model_shapes.ttl
```

---

## Resultados

### Validación con shapes desde datos

Resultado:

```text
Conforms: True
```

El KG cumple las restricciones estructurales inferidas desde los propios datos. Esto
indica que, tras las correcciones de la Tarea 4, no aparecen ya errores como coordenadas
no numéricas, recursos `Campo/0` o campos deportivos mal parseados en las shapes
generadas desde el RDF.

### Validación con shapes desde modelo

Resultado:

```text
Conforms: True
```

El KG también cumple las restricciones definidas desde el modelo. La validación confirma
que las entidades principales tienen los atributos esperados y que las relaciones
principales entre partidos, equipos, competiciones, fases, grupos, campos, distritos y
temporadas son coherentes.

---

## Interpretación

Las shapes generadas desde los datos son útiles para describir los patrones reales del
KG. En cambio, las shapes de modelo permiten expresar decisiones de diseño que no siempre
se deducen automáticamente, como el tratamiento de partidos con campo desconocido.

En esta validación se decidió no exigir `ta:seJuegaEn` como propiedad obligatoria para
todos los partidos, porque algunos registros tienen `codigoCampo=0` en el CSV original.
Forzar esa restricción produciría violaciones conocidas y esperadas, no necesariamente
errores del KG corregido.

---

## Conclusión

Se han validado dos perspectivas del Knowledge Graph:

* una validación descriptiva basada en shapes generadas desde el RDF materializado;
* una validación normativa basada en la ontología y los mappings.

Ambas validaciones son conformes (`Conforms: True`). Por tanto, la versión regenerada del
Knowledge Graph cumple las restricciones SHACL definidas para esta tarea.
