# NUEVO (Jonathan, 2026-10-18): API de solo lectura para el Front. Lee la tabla rendimientos_estimados
# (modelo ParcelaApp) y devuelve JSON. Reemplaza los datos de demostración de frontend/src/pages/Parcelas.tsx.
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import ParcelaApp

CAMPOS = ['id_poligono', 'estado', 'municipio', 'conjunto', 'superficie_ha', 'latitud', 'longitud',
          'rendimiento_estimado_t_ha', 'origen', 'modelo']


def _a_dict(parcela):
    datos = {campo: getattr(parcela, campo) for campo in CAMPOS}
    # DecimalField llega como Decimal y JSON no lo acepta; se manda como número.
    datos['rendimiento_estimado_t_ha'] = float(parcela.rendimiento_estimado_t_ha)
    return datos


@require_GET
def lista_parcelas(request):
    """GET /api/parcelas/  Filtros opcionales: ?estado=Hidalgo  ?origen=modelo|observado"""
    parcelas = ParcelaApp.objects.order_by('id_poligono')
    if request.GET.get('estado'):
        parcelas = parcelas.filter(estado=request.GET['estado'])
    if request.GET.get('origen'):
        parcelas = parcelas.filter(origen=request.GET['origen'])
    datos = [_a_dict(p) for p in parcelas]
    return JsonResponse({'total': len(datos), 'parcelas': datos})


@require_GET
def detalle_parcela(request, id_poligono):
    """GET /api/parcelas/AGC_003/"""
    try:
        parcela = ParcelaApp.objects.get(id_poligono=id_poligono)
    except ParcelaApp.DoesNotExist:
        return JsonResponse({'error': f'No existe la parcela {id_poligono}'}, status=404)
    return JsonResponse(_a_dict(parcela))
