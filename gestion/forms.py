# Clientes, Compras, Panel, Pagos, Participantes, Premios, Rifas, User
from django import forms

from .models import Cliente, Comprobante, Evento, MetodoPago


class FormComprobante(forms.ModelForm):
    class Meta:
        model = Comprobante
        fields = [
            "nombre",
            "telefono",
            "foto",
            "fecha",
            "metodo",
            "status",
            "referencia",
        ]


class FormEvento(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            "fecha_inicio",
            "fecha_fin",
            "nombre",
            "foto",
            "precio_unidad",
            "total_tickets",
            "minimo",
        ]


class RifaForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = "__all__"


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = "__all__"


class MetodoForm(forms.ModelForm):
    class Meta:
        model = MetodoPago
        fields = "__all__"
