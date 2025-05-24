from django.urls import path
from . import views


urlpatterns = [
    path("", views.inicioView, name="inicio_admin"),
    path("comprobantes/", views.ComprobanteView.as_view(), name="comprobantes_admin"),
    path("comprobantes/<int:pk>/", views.ComprobanteView.as_view(), name="edit_comprobantes_admin"),
    path('estadisticas/', views.ventas_y_participantes, name='estadisticas'),
    path("eventos/", views.EventoView.as_view(), name="eventos_admin"),
    path("eventos/<int:pk>/", views.EventoView.as_view(), name="edit_eventos_admin"),
    path("pdf/<int:pk>/", views.ComprobantePDF.as_view(), name="operador_pdf"),
]
