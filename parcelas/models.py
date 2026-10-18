from django.db import models

# MODIFICADO (Jonathan, 2026-10-18): el modelo apuntaba a 'v_parcelas_app', pero esa vista no tiene
# superficie_ha, así que cualquier consulta fallaba. Ahora apunta a 'rendimientos_estimados', la tabla
# del Front que carga el ETL (AgroCebada_Datos, sql/005). Trae exactamente estas columnas.
class ParcelaApp(models.Model):
    id_poligono = models.CharField(max_length=20, primary_key=True)
    estado = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    latitud = models.FloatField()
    longitud = models.FloatField()
    superficie_ha = models.FloatField()
    conjunto = models.CharField(max_length=20)
    # MODIFICADO (Jonathan, 2026-10-18): antes rendimiento_t_ha (nulo en PREDICCION). Ahora siempre trae
    # valor: observado en ENTRENAMIENTO y predicho por el modelo en PREDICCION.
    rendimiento_estimado_t_ha = models.DecimalField(max_digits=5, decimal_places=2)
    origen = models.CharField(max_length=10)  # NUEVO (Jonathan, 2026-10-18): 'observado' o 'modelo'
    modelo = models.CharField(max_length=30, null=True, blank=True)  # NUEVO (Jonathan, 2026-10-18): p. ej. 'svr_12vars'

    class Meta:
        managed = False
        db_table = 'rendimientos_estimados'  # MODIFICADO (Jonathan, 2026-10-18): antes 'v_parcelas_app'
    def __str__(self):
        return self.id_poligono