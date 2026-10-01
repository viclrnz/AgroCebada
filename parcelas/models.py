from django.db import models

class Parcela(models.Model):
    # Identificador o nombre de la parcela
    nombre = models.CharField(max_length=100)
    
    # Coordenadas geográficas
    latitud = models.FloatField()
    longitud = models.FloatField()
    
    # Datos climáticos o de vegetación (puedes ajustar estos nombres luego)
    temperatura = models.FloatField(null=True, blank=True)
    precipitacion = models.FloatField(null=True, blank=True)
    indice_vegetacion = models.FloatField(null=True, blank=True)
    
    # El rendimiento predicho por el modelo (puede estar vacío al principio)
    rendimiento_predicho = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.nombre