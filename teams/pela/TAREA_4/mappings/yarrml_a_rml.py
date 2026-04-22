import yatter
from ruamel.yaml import YAML

# Configurar YAML para leer el origen
yaml = YAML(typ='safe', pure=True)

# Cargar el YARRRML y traducirlo a RML (str)
mapping_file = "TAREA_4/mappings/mapping.yarrrml.yaml"
rml_content = yatter.translate(yaml.load(open(mapping_file, "r")))

# Guardar
with open("TAREA_4/mappings/mapping.rml.ttl", "w") as f:
    f.write(rml_content) # <--- Usa .write() en lugar de yaml.dump()
