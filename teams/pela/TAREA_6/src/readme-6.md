# Tarea 6: Explotación del Knowledge Graph

Uso de streamlit para la exploración, visualización y consulta semántica del Knowledge Graph (KG) de centros deportivos y partidos en Madrid.

## Características Principales

### 1. Dashboard Interactivo (Streamlit)
- **Mapa Geoespacial `folium`**:  
  - **Filtrado**: Por nombre, distrito y tipo de deporte.
  - **Localización**: Identificación de centros por coordenadas exactas (soluciona solapamientos en pabellones multiusos).
  - **Datos adicionales**: Información sobre la población de distritos e imágenes representativas de los deportes practicados sacadas de Wikidata.
  - **Historial de Partidos**: Listado completo de encuentros registrados en cada centro.

- **Consultas Inteligentes con LLMs `ollama`**:
    - **Generación de SPARQL**: Traducción de lenguaje natural a consultas técnicas sobre el KG.   
    - **Modo Comparativa**: Comparación de consultas generadas por IA frente a consultas ya escritas. Se pueden ejecutar ambas y comparar los resultados.

## Requisitos

- `rdflib`, `pandas`, `folium`, `streamlit`, `streamlit-folium`, `ollama`, `pyproj`.
- **Ollama** ejecutándose localmente (`http://localhost:11434`).

## Instalación y Ejecución

1. **Instalar dependencias**:
   ```bash
   pip install rdflib pandas folium streamlit streamlit-folium ollama pyproj
   ```

2. **Pre-procesamiento (Obligatorio)**:
   Extrae los datos del grafo (`.nt`) y añadimos información extra de Wikidata en archivos CSV:
   ```bash
   python3 TAREA_6/src/preprocess.py
   ```

3. **Lanzar la Aplicación**:
   ```bash
   streamlit run TAREA_6/src/app.py
   ```

## Configuración de Ollama (Hardware Optimizado)

- **Recomendado**: 
```bash
ollama pull phi3:mini` 
```
- **Ultra-rápido**: 
```bash
ollama pull qwen2.5:3b` 
```
- **Más potente**: 
```bash
ollama pull llama3:8b` 
```

### Iniciar el servicio de Ollama (en otra terminal)

```bash
ollama serve
```

## Estructura de Archivos
- `TAREA_6/src/app.py`: Aplicación principal de Streamlit.
- `TAREA_6/src/preprocess.py`: Script de extracción y enriquecimiento (Wikidata API).
- `TAREA_6/src/llm_query_gen.py`: Lógica de prompt engineering y limpieza de SPARQL.
- `TAREA_6/data/processed/`: Almacenamiento de datos optimizados en CSV.
