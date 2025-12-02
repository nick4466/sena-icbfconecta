"""
Script de ejemplo para poblar algunas ciudades por regional.
No es exhaustivo — sirve para pruebas y para que el select de ciudades funcione.
Ejecutar con:
    python manage.py shell -c "from core.scripts.cargar_ciudades_ejemplo import run; run()"
"""
from core.models import Regional, Ciudad

CIUDADES_POR_REGIONAL = {
    'BogotaDC': ['Bogotá'],
    'Antioquia': ['Medellín', 'Bello', 'Envigado', 'Itagüí'],
    'Valle del Cauca': ['Cali', 'Palmira', 'Buenaventura'],
    'Cundinamarca': ['Soacha', 'Zipaquirá', 'Facatativá'],
    'Santander': ['Bucaramanga', 'Floridablanca'],
    'Atlantico': ['Barranquilla', 'Soledad'],
    'Bolivar': ['Cartagena'],
    'Nariño': ['Pasto'],
    'Huila': ['Neiva'],
    'Tolima': ['Ibagué'],
    'Meta': ['Villavicencio'],
    'Magdalena': ['Santa Marta'],
    'Cesar': ['Valledupar'],
    'Cauca': ['Popayán'],
    'Risaralda': ['Pereira'],
    'Quindio': ['Armenia'],
    'Caldas': ['Manizales'],
    'Boyaca': ['Tunja'],
    'Choco': ['Quibdó'],
    'La Guajira': ['Riohacha'],
    'Sucre': ['Sincelejo'],
    'Cordoba': ['Montería'],
    'Arauca': ['Arauca'],
    'Casanare': ['Yopal'],
    'Putumayo': ['Mocoa'],
    'San Andres y Providencia': ['San Andrés'],
    'Amazonas': ['Leticia'],
    'Vichada': ['Puerto Carreño'],
    'Vaupes': ['Mitú'],
    'Guaviare': ['San José del Guaviare'],
    'Guainia': ['Inírida'],
}

def run():
    created = 0
    for regional_nombre, ciudades in CIUDADES_POR_REGIONAL.items():
        regional = Regional.objects.filter(nombre__iexact=regional_nombre).first()
        if not regional:
            # Intentar buscar por nombre parcialmente (ej. 'BogotaDC' vs 'Bogotá D.C.')
            regional = Regional.objects.filter(nombre__icontains=regional_nombre).first()
        if not regional:
            print(f"⚠️ Regional no encontrada en DB: {regional_nombre}")
            continue
        for ciudad_nombre in ciudades:
            obj, created_flag = Ciudad.objects.get_or_create(nombre=ciudad_nombre, regional=regional)
            if created_flag:
                created += 1
                print(f"Creada ciudad: {ciudad_nombre} (Regional: {regional.nombre})")
    print(f"✅ Ciudades creadas: {created}")

if __name__ == '__main__':
    run()
