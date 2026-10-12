from django.db import models

class ParcelaApp(models.Model):
    id_poligono = models.CharField(max_length=20, primary_key=True)
    estado = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    latitud = models.FloatField()
    longitud = models.FloatField()
    superficie_ha = models.FloatField()
    conjunto = models.CharField(max_length=20)
    rendimiento_t_ha = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'v_parcelas_app'
    def __str__(self):
        return self.id_poligono