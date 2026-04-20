import rdflib

g = rdflib.Graph()
print("Leyendo y limpiando el archivo...")

with open('kg/output_final.nq', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            # Solo procesamos la línea si tiene contenido real
            if line.strip():
                g.parse(data=line, format='nquads')
        except Exception:
            # Si una línea está mal, la saltamos silenciosamente
            continue

print(f"Conversión terminada. Se han rescatado {len(g)} tripletas.")
g.serialize(destination='kg/output_final.ttl', format='turtle')
print("Archivo 'kg/output_final.ttl' generado con éxito. ¡Ya puedes abrirlo en Protégé!")