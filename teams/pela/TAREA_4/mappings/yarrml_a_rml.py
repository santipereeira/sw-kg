import yatter
from ruamel.yaml import YAML

# 1. Configurar YAML para leer el origen
yaml = YAML(typ='safe', pure=True)

# 2. Cargar el YARRRML y traducirlo a RML (esto devuelve un STRING)
mapping_file = "TAREA_4/mappings/mapping.yarrrml.yaml"
rml_content = yatter.translate(yaml.load(open(mapping_file, "r")))

# 3. GUARDAR CORRECTAMENTE (como texto plano, no como YAML)
with open("TAREA_4/mappings/mapping.rml.ttl", "w") as f:
    f.write(rml_content) # <--- Usa .write() en lugar de yaml.dump()