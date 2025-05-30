from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicioView, name="inicio_admin"),
    path("rifas/", views.RifasListView.as_view(), name="rifas_admin"),
    path("rifas/crear", views.RifasFormView.as_view(), name="rifas_crear_admin"),
    path("participantes/", views.participantesView, name="participantes_admin"),
    path("dashboard/", views.dashboardView, name="dashboard_admin"),
    path("premios/", views.premiosView, name="premios_admin"),
    path("cliente/", views.clienteView, name="cliente_admin"),
    path("pagos/", views.pagosView, name="pagos_admin"),
    path("usuarios/", views.usuariosView, name="usuarios_admin"),
    path("compras/", views.comprasView, name="compras_admin"),
    # path("", views.inicioView, name="inicio_admin"),
    path("comprobantes/", views.ComprobanteView.as_view(), name="comprobantes_admin"),
    path(
        "comprobantes/<int:pk>/",
        views.ComprobanteView.as_view(),
        name="edit_comprobantes_admin",
    ),
    path("estadisticas/", views.ventas_y_participantes, name="estadisticas"),
    path("eventos/", views.EventoView.as_view(), name="eventos_admin"),
    path("eventos/<int:pk>/", views.EventoView.as_view(), name="edit_eventos_admin"),
]
