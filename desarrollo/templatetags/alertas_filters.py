from django import template
import re

register = template.Library()

MESES_ES = [
    '', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
]

@register.filter
def agrupa_alertas(alertas):
    """
    Filtro de ejemplo: simplemente retorna la lista tal cual.
    Puedes personalizar la lógica de agrupación aquí.
    """
    return alertas

@register.filter
def ejemplo_alerta(value):
    """Filtro de ejemplo para alertas (no hace nada)."""
    return value

@register.filter
def date_es(value):
    """
    Convierte una fecha tipo 'F Y' (ej: 'November 2025') a 'noviembre 2025'.
    Si el valor no es válido, lo retorna igual.
    """
    match = re.match(r'([A-Za-z]+)\s+(\d{4})', str(value))
    if not match:
        return value
    mes_en = match.group(1).lower()
    year = match.group(2)
    meses_en = [
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december'
    ]
    try:
        idx = meses_en.index(mes_en) + 1
        mes_es = MESES_ES[idx]
        return f"{mes_es} {year}"
    except ValueError:
        return value
