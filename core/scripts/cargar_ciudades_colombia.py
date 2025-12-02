# Script para poblar la tabla Ciudad con ciudades principales asociadas a cada regional
from core.models import Regional, Ciudad

# Diccionario: Regional -> Lista de ciudades principales
CIUDADES_POR_REGIONAL = {
    "Amazonas": ["Leticia"],
    "Antioquia": ["Medellín", "Bello", "Itagüí"],
    "Arauca": ["Arauca"],
    "Atlantico": ["Barranquilla", "Soledad"],
    "BogotaDC": ["Bogotá D.C."],
    "Bolivar": ["Cartagena", "Magangué"],
    "Boyaca": ["Tunja", "Duitama"],
    "Caldas": ["Manizales"],
    "Caqueta": ["Florencia"],
    "Casanare": ["Yopal"],
    "Cauca": ["Popayán"],
    "Cesar": ["Valledupar"],
    "Choco": ["Quibdó"],
    "Cordoba": ["Montería"],
    "Cundinamarca": ["Soacha", "Fusagasugá"],
    "Guainia": ["Inírida"],
    "Guaviare": ["San José del Guaviare"],
    "Huila": ["Neiva"],
    "La Guajira": ["Riohacha"],
    "Magdalena": ["Santa Marta"],
    "Meta": ["Villavicencio"],
    "Nariño": ["Pasto"],
    "Norte de Santander": ["Cúcuta"],
    "Putumayo": ["Mocoa"],
    "Quindio": ["Armenia"],
    "Risaralda": ["Pereira"],
    "San Andres y Providencia": ["San Andrés"],
    "Santander": ["Bucaramanga"],
    "Sucre": ["Sincelejo"],
    "Tolima": ["Ibagué"],
    "Valle del Cauca": ["Cali", "Palmira"],
    "Vaupes": ["Mitú"],
    "Vichada": ["Puerto Carreño"]
}

def run():
    total = 0
    for nombre_regional, ciudades in CIUDADES_POR_REGIONAL.items():
        regional = Regional.objects.filter(nombre=nombre_regional).first()
        if not regional:
            print(f"❌ Regional no encontrada: {nombre_regional}")
            continue
        for nombre_ciudad in ciudades:
            obj, created = Ciudad.objects.get_or_create(nombre=nombre_ciudad, regional=regional)
            if created:
                print(f"✅ Ciudad creada: {nombre_ciudad} ({nombre_regional})")
                total += 1
    print(f"Carga finalizada. Total de ciudades creadas: {total}")

# Ejecutar automáticamente al usar exec()
run()
