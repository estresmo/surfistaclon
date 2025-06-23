from django.shortcuts import redirect
from django.urls import path

from . import apis, views

view_patterns = [
    path("", lambda request: redirect("/admin/rifas"), name="inicio_admin"),
    path("rifas/", views.RifasListView.as_view(), name="rifas_admin"),
    path("rifas/crear", views.RifasCreateView.as_view(), name="rifas_crear_admin"),
    path("rifas/<int:pk>/", views.RifasUpdateView.as_view(), name="rifas_editar_admin"),
    path("metodos/", views.MetodosListView.as_view(), name="metodos_admin"),
    path("metodos/crear", views.MetodoCreateView.as_view(), name="metodos_crear_admin"),
    path("metodos/<int:pk>/", views.MetodoUpdateView.as_view()),
    path("compras/", views.ComprasListView.as_view(), name="compras_admin"),
    path("compras/crear", views.ComprasCreateView.as_view()),
    path("compras/<int:pk>", views.ComprasUpdateView.as_view()),
    path("participantes/", views.participantesView, name="participantes_admin"),
    path("dashboard/", views.dashboardView, name="dashboard_admin"),
    path("clientes/", views.ClientesListView.as_view(), name="clientes_admin"),
    path("cliente/<int:pk>/", views.ClienteUpdateView.as_view()),
    path("usuarios/", views.usuariosView, name="usuarios_admin"),
    path("ojo/", views.ojoView, name="ojo_admin"),
    path(
        "cliente/crear", views.ClienteCreateView.as_view(), name="cliente_crear_admin"
    ),
]

apis_patterns = [
    path("compras/eliminar/<int:pk>", apis.eliminar_compra),
    path("rifas/eliminar/<int:pk>", apis.eliminar_rifa),
    path("metodos/eliminar/<int:pk>", apis.eliminar_metodo),
    path("verificar/<int:pk>", apis.verificar_comprobante, name="verificar_admin"),
    path("stats/<int:evento_id>/fechas", apis.ver_fecha_stats),
]

urlpatterns = [*view_patterns, *apis_patterns]
