# Tarea 3 — Modelado y Publicación de la Ontología

## IRI base / Namespace

```
https://example.org/partidos/
```

Prefijo: `ns:`

La ontología está en: [`TAREA_3/ontology/ontology.ttl`](TAREA_3/ontology/ontology.ttl)

## Alcance

La ontología cubre el dominio de las **competiciones deportivas municipales de deportes** del Ayuntamiento de Madrid, específicamente la temporada 2014–2015.

**Incluye:**
- Estructura organizativa (Competiciones, Grupos, Jornadas)
- Eventos deportivos (Partidos, resultados, estados).
- Entidades participantes (Equipos, Deportes).
- Infraestructura y localización (Campos deportivos, Distritos municipales).

## Preguntas de competencia

La ontología permite responder, entre otras, a las siguientes preguntas:

1. ¿Qué partidos se han disputado en un campo determinado?
2. ¿Cuántos partidos ha jugado un equipo como local en una temporada?
3. ¿Cuál es el resultado de un partido dado?
4. ¿Qué grupos forman parte de una competición de fútbol sala?
5. ¿En qué jornada y fecha se celebró un partido concreto?
6. ¿A qué distrito pertenece un campo deportivo?
7. ¿Qué deportes se engloban en la competición municipal?
8. ¿Cuál es el enlace Wikidata del deporte o del distrito?
9. ¿Cuántos partidos de una categoría determinada se han jugado en un distrito?
10. ¿Qué partidos han sido suspendidos o aplazados en una jornada concreta?

---

## Diagrama de la ontología

El diagrama fue generado con **Chowlk** y exportado como imagen:

- [`TAREA_3/ontology/ontology.png`](TAREA_3/ontology/ontology.png) — Diagrama PNG
- [`TAREA_3/ontology/ontology.svg`](TAREA_3/ontology/ontology.svg) — Diagrama SVG (vectorial)

### Clases principales

| Clase | Descripción |
|---|---|
| `ns:Deporte` | Tipo de deporte (fútbol, baloncesto, voleibol…) |
| `ns:Competicion` | Competición organizada por deporte y temporada |
| `ns:Grupo` | Grupo o categoría dentro de una competición |
| `ns:Jornada` | Jornada dentro de un grupo, con fecha |
| `ns:Partido` | Encuentro entre dos equipos en un campo |
| `ns:Equipo` | Equipo participante |
| `ns:Campo` | Instalación deportiva con coordenadas geográficas |
| `ns:Distrito` | Distrito geográfico de Madrid donde está el campo |

### Propiedades de objeto (relaciones entre entidades)

| Propiedad | Dominio → Rango |
|---|---|
| `ns:tipoDe` | Competicion → Deporte |
| `ns:tieneGrupo` | Competicion → Grupo |
| `ns:tieneJornada` | Grupo → Jornada |
| `ns:tienePartido` | Jornada → Partido |
| `ns:tieneEquipoLocal` | Partido → Equipo |
| `ns:tieneEquipoVisitante` | Partido → Equipo |
| `ns:ocurreEn` | Partido → Campo |
| `ns:localizadoEn` | Campo → Distrito |

## Modelado con Chowlk

El modelado se realizó visualmente con [Chowlk](https://chowlk.linkeddata.es/).

El flujo fue: diseño en Chowlk → exportación a Turtle → revisión manual del TTL para completar metadatos (`dcterms:title`, `dcterms:description`, `dcterms:creator`, `dcterms:license`, `owl:versionInfo`).

## Publicación con OnToology

La ontología fue registrada en [OnToology](https://ontoology.linkeddata.es/) conectándola al repositorio GitHub del grupo. OnToology monitorizó el fichero `TAREA_3/ontology/ontology.ttl` y generó automáticamente:

- **Documentación HTML** (Widoco) con descripción de clases y propiedades
- **Diagramas** de clases y taxonomía (AR2DTool)
- **Informe de evaluación** OOPS! con posibles pitfalls detectados
- **Contexto JSON-LD** (owl2jsonld)
- **Evaluación Themis**

Los artefactos generados se encuentran en la carpeta [`TAREA_3/ontoology/`](TAREA_3/ontoology/), que corresponde al Pull Request abierto por OnToology sobre el repositorio.

### Configuración OnToology utilizada

```ini
[widoco]
enable = True
languages = ['en']
webvowl = True

[ar2dtool]
enable = True

[oops]
enable = True

[owl2jsonld]
enable = True

[themis]
enable = True
```

---

## Enlace a la documentación publicada

La documentación de la ontología está publicada a través de **GitHub Pages** del repositorio del fork:

[Índicel](https://santipereeira.github.io/sw-kg/teams/pela/TAREA_3/ontoology/documentation/doc/index-en.html)
