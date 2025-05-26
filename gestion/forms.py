from .models import Comprobante, Evento
from django import forms


class FormComprobante(forms.ModelForm):
    class Meta:
        model = Comprobante
        fields = ["nombre", "telefono", "foto", "fecha", "metodo", "status","referencia"]


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
