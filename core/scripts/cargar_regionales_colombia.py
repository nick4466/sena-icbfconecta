# Script para poblar la tabla Regional con las regionales oficiales de Colombia
from core.models import Regional

REGIONALES = [
    "Amazonas", "Antioquia", "Arauca", "Atlantico", "BogotaDC", "Bolivar", "Boyaca", "Caldas",
    "Caqueta", "Casanare", "Cauca", "Cesar", "Choco", "Cordoba", "Cundinamarca", "Guainia", "Guaviare",
    "Huila", "La Guajira", "Magdalena", "Meta", "Nariño", "Norte de Santander", "Putumayo", "Quindio",
    "Risaralda", "San Andres y Providencia", "Santander", "Sucre", "Tolima", "Valle del Cauca", "Vaupes", "Vichada"
]

def run():
    for nombre in REGIONALES:
        Regional.objects.get_or_create(nombre=nombre)
    print("✅ Regionales de Colombia cargadas correctamente.")

# Ejecutar automáticamente al usar exec()
run()
