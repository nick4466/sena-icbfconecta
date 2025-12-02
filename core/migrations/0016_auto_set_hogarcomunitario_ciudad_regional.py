from django.db import migrations

def set_default_ciudad_regional(apps, schema_editor):
    HogarComunitario = apps.get_model('core', 'HogarComunitario')
    Ciudad = apps.get_model('core', 'Ciudad')
    Regional = apps.get_model('core', 'Regional')

    ciudad = Ciudad.objects.first()
    regional = Regional.objects.first()

    if ciudad and regional:
        for hogar in HogarComunitario.objects.filter(ciudad__isnull=True):
            hogar.ciudad = ciudad
            hogar.save()
        for hogar in HogarComunitario.objects.filter(regional__isnull=True):
            hogar.regional = regional
            hogar.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_alter_hogarcomunitario_ciudad_and_more'),  # Ajusta según tu última migración
    ]

    operations = [
        migrations.RunPython(set_default_ciudad_regional),
    ]