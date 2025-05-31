from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("rifa/<str:link>/", views.detalle_evento, name="detalle_evento"),
    path("obtener_dolar/", views.obtener_dolar, name="obtener_dolar"),
    path("comprobantes/", views.comprobantes, name="comprobantes"),
    path("verificar/", views.verificar, name="verificar"),
    path("obtener_promociones/", views.obtener_promociones, name="obtener_promociones"),
]
