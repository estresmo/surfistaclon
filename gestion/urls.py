from django.shortcuts import redirect
from django.urls import path

from . import views

urlpatterns = [
    path("", lambda request: redirect("/admin/rifas"), name="inicio_admin"),
    path("rifas/", views.RifasListView.as_view(), name="rifas_admin"),
    path("rifas/crear", views.RifasCreateView.as_view(), name="rifas_crear_admin"),
    path("rifas/<int:pk>/", views.RifasUpdateView.as_view(), name="rifas_editar_admin"),
    path("metodos/", views.MetodosListView.as_view(), name="metodos_admin"),
    path("metodos/crear", views.MetodoCreateView.as_view(), name="metodos_crear_admin"),
    path(
        "metodos/<int:pk>/",
        views.MetodoUpdateView.as_view(),
        name="metodos_editar_admin",
    ),
    path("participantes/", views.participantesView, name="participantes_admin"),
    path("dashboard/", views.dashboardView, name="dashboard_admin"),
    path("premios/", views.premiosView, name="premios_admin"),
    path("clientes/", views.ClientesListView.as_view(), name="clientes_admin"),
    path(
        "cliente/<int:pk>/",
        views.ClienteUpdateView.as_view(),
        name="clientes_editar_admin",
    ),
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
    path("ojo/", views.ojoView, name="ojo_admin"),
    path("purchases/", views.purchasesView, name="purchases_admin"),
    path("cliente/crear", views.ClienteCreateView.as_view(), name="cliente_crear_admin"),
    
     
]
