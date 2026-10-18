# NUEVO (Jonathan, 2026-10-18): rutas de la API de parcelas (se montan en /api/parcelas/).
from django.urls import path

from . import views

urlpatterns = [
    path('', views.lista_parcelas, name='lista_parcelas'),
    path('<str:id_poligono>/', views.detalle_parcela, name='detalle_parcela'),
]
