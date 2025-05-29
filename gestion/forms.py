from .models import Comprobante, Evento, Clientes, Compras, Panel, Pagos, Participantes, Premios, Rifas, User       
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

class FormClientes(forms.ModelForm):
    class Meta:
        model = Clientes
        fields = [
            "foto",
            "nombre",
            "ubicacion",
        ]

class FormCompras(forms.ModelForm):
    class Meta:
        model = Compras
        fields = [
            "participante",
            "fecha",
            "status",
            "cuenta",
            "monto",
            "numeros"
            "extras",
            "notas",
        ]

class FormPanel(forms.ModelForm):
    class Meta:
        model = Panel
        fields = [
            "totalparticipantes",
            "totalticketsregistrados",
            "totalporconfirmados",
            "totalconfirmados",
            "ticketsregistrados",
            "participantesycompras",
            "pagosporconfirmar",
            "pagosconfirmados",
            "mediosdepago",
            "statusdelascompras",
            "participantesmastickets",
            "diasconmasventas",
            "numerosdeticketsfrecuentes",
        ]

class FormPagos(forms.ModelForm):
    class Meta:
        model = Pagos
        fields = [
            "foto",
            "banco",
            "alias",
            "titular",
            "icono",
            "tipo",
            "contenido",
            "visible",
        ]

class FormParticipantes(forms.ModelForm):
    class Meta:
        model = Participantes
        fields = [
            "todos",
            "rifasactivas",
            "rifasinactivas",
            "nombre",
            "celular",
            "email",
            "ubicacion",
            "direccion",
            "campoextra",
            "vendedore",
            "pagototal",
            "total",
        ]

class FormPremios(forms.ModelForm):
    class Meta:
        model = Premios
        fields = [
            "todos",
            "rifaactiva",
            "rifainactiva",
            "nopremios",
        ]

class FormRifas(forms.ModelForm):
    class Meta:
        model = Rifas
        fields = [
            "foto",
            "nombre",
            "precio",
            "fecha",
            "tickets",
            "cantidadonline",
            "oportun",
            "vendido",
            "listado",
            "exportar",
            "activo",
            "participantes",
        ]

class FormUser(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "nombre",
            "email",
            "cargo",
            "celular",
            "rol",
            "activo",
        ]