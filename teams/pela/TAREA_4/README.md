\# Tarea 4 LOT4KG - Generador de Grafo de Conocimiento


Este proyecto implementa un mapping para inyectar datos tubulares de la temporada de los Juegos Deportivos de Chamartin en un Grafo Semántico bajo nuestra nueva ontología construida en tareas previas.


\## Dataset

Se proporciona `data/ontologia-deportes.csv`, en el cual hemos basado nuestra ejecución porque contiene datos más enrriquecidos, como un ID limpio de WikiData, distritos separados y fechas consolidadas. Corresponde a los partidos de competición local.


\## Diseño del Mapping (Tarea 4)

Utilizando YARRRML creamos reglas asociando:

\- Deporte (`ns:Deporte`) en conjunto a su enlace de WikiData mediante el `Deporte\_ID`.

\- Competiciones generadas por combinación semántica de deporte y fase.

\- Partidos con local, visitante y resultado (marcador), asignados a Grupos y Jornadas específicas.

\- Entidades geográficas como `ns:Campo` o `ns:Distrito`.

