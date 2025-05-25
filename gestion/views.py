from django.shortcuts import render
from .models import (
    Comprobante,
    MetodosChoices,
    NumeroRifa,
    StatusChoices,
    Evento,
    Promocion,
    Visualizacion,
)
from django.views.generic import View
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpRequest
import base64
from .forms import FormComprobante, FormEvento
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .utils import send_whatsapp, calcular_monto
from django.db.models import Sum, Q
from typing import Optional


@login_required
def inicioView(request: HttpRequest):
    return render(request, "admin/compras.html")

@login_required
def comprasView(request: HttpRequest):
    return render(request, "admin/compras.html")

@login_required
def participantesView(request: HttpRequest):
    return render(request, "admin/participantes.html")

@login_required
def rifasView(request: HttpRequest):
    return render(request, "admin/rifas.html")

@login_required
def dashboardView(request: HttpRequest):
    return render(request, "admin/dashboard.html")

@login_required
def premiosView(request: HttpRequest):
    return render(request, "admin/premios.html")

@login_required
def clienteView(request: HttpRequest):
    return render(request, "admin/cliente.html")

@login_required
def pagosView(request: HttpRequest):
    return render(request, "admin/pagos.html")

@login_required
def usuariosView(request: HttpRequest): 
    return render(request, "admin/usuarios.html")




class EventoView(LoginRequiredMixin, View):
    template_name = "gestion/eventos.html"
    form_class = FormEvento

    def get(self, request: HttpRequest, pk: Optional[int] = None):
        queryset = Evento.objects.all()
        form = self.form_class()
        edit_form = None
        edit_id = None
        if pk:
            evento = get_object_or_404(Evento, pk=pk)
            edit_form = self.form_class(instance=evento)
            edit_id = evento.pk
        context = {  # type: ignore
            "object_list": queryset,
            "form": form,
            "edit_form": edit_form,
            "edit_id": edit_id,
        }

        return render(
            request,
            self.template_name,
            context,  # type: ignore
        )

    def post(self, request: HttpRequest, pk: Optional[int] = None):
        evento = None
        if pk:
            evento = get_object_or_404(Evento, pk=pk)
            form = self.form_class(request.POST, request.FILES, instance=evento)
            print(form.errors)
        else:
            form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            if evento:
                Promocion.objects.filter(evento=evento).delete()
            promociones = request.POST.getlist("promocionCantidad")
            precios = request.POST.getlist("promocionPrecio")
            for i in range(len(promociones)):
                Promocion.objects.create(
                    cantidad_tickets=promociones[i],
                    precio=precios[i],
                    evento=form.instance,
                )
            return redirect("eventos_admin")
        else:
            print(form.errors)

        queryset = Evento.objects.all()
        return render(
            request,
            self.template_name,
            {
                "object_list": queryset,
                "form": form,
                "edit_form": form if pk else None,
                "edit_id": pk,
            },
        )

    def delete(self, request: HttpRequest, pk: Optional[int] = None):
        evento = get_object_or_404(Evento, pk=pk)
        evento.delete()
        return HttpResponse("ok")


class ComprobanteView(LoginRequiredMixin, View):
    template_name = "gestion/comprobantes.html"
    form_class = FormComprobante

    def get(self, request: HttpRequest, pk: Optional[int] = None):
        evento = Evento.obtener_actual()
        filtro_evento = request.GET.get("evento")
        metodo_actual = request.GET.get("metodo")
        if not filtro_evento and evento:
            filtro_evento = evento.pk
        if filtro_evento == "0" or not filtro_evento:
            filtro_evento = None
        queryset = Comprobante.objects.filter(evento=filtro_evento).prefetch_related(
            "evento"
        )
        if metodo_actual:
            queryset = queryset.filter(metodo=metodo_actual)
        pendientes = queryset.filter(status=StatusChoices.NO_VERIFICADO).count()
        form = self.form_class()
        edit_form = None
        edit_id = None
        agarrados = NumeroRifa.objects.filter(
            comprobante__evento=evento
        ).prefetch_related("comprobante__evento")
        agarrados = [str(a) for a in agarrados]
        eventos = Evento.objects.all()
        tickets = []
        metodos = MetodosChoices.choices
        if evento:
            tickets = list(range(evento.total_tickets))
            tickets = [format(t, evento.digitos) for t in tickets]
        if pk:
            _Comprobante = get_object_or_404(Comprobante, pk=pk)
            edit_form = self.form_class(instance=_Comprobante)
            edit_id = _Comprobante.pk
        return render(
            request,
            self.template_name,
            {
                "object_list": queryset,
                "form": form,
                "edit_form": edit_form,
                "edit_id": edit_id,
                "agarrados": agarrados,
                "tickets": tickets,
                "eventos": eventos,
                "evento_actual": evento,
                "metodos": metodos,
                "metodo_actual": metodo_actual,
                "pendientes": pendientes,
            },
        )

    def post(self, request: HttpRequest, pk=None):
        ultimo_status = None
        if pk:
            _Comprobante = get_object_or_404(Comprobante, pk=pk)
            ultimo_status = _Comprobante.status
            form = self.form_class(request.POST, request.FILES, instance=_Comprobante)
            print(form.errors)
        else:
            form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            evento = Evento.obtener_actual()
            comprobante = form.save(commit=False)
            comprobante.evento = evento
            comprobante.telefono = comprobante.telefono.replace(" ", "")
            comprobante.save()
            boletos = request.POST["boletos"].strip(",").split(",")
            msg = (
                "Su comprobante ha sido "
                + comprobante.get_status_display()
                + ". Los boletos verificados son "
                + " ,".join(boletos)
            )
            if pk:
                if ultimo_status != comprobante.status:
                    send_whatsapp(comprobante.telefono, msg)
            NumeroRifa.objects.filter(evento=evento, comprobante=form.instance).delete()
            if form.instance.status != StatusChoices.RECHAZADO:
                numeros = []
                for boleto in boletos:
                    numero = NumeroRifa(
                        numero=boleto, comprobante=form.instance, evento=evento
                    )
                    numeros.append(numero)
                NumeroRifa.objects.bulk_create(numeros)
            comprobante.monto = calcular_monto(comprobante)
            comprobante.save(update_fields=["monto"])
            return redirect("comprobantes_admin")
        else:
            print(form.errors)

        queryset = Comprobante.objects.all()
        return render(
            request,
            self.template_name,
            {
                "object_list": queryset,
                "form": form,
                "edit_form": form if pk else None,
                "edit_id": pk,
            },
        )

    def delete(self, request, pk=None):
        comprobante = get_object_or_404(Comprobante, pk=pk)
        NumeroRifa.objects.filter(comprobante=comprobante).delete()
        comprobante.delete()
        return HttpResponse("ok")


class ComprobantePDF(LoginRequiredMixin, View):
    def get(self, request, pk):
        from xhtml2pdf import pisa

        comprobante = get_object_or_404(Comprobante, pk=pk)
        foto = ""
        logo = ""
        if comprobante.foto:
            foto = base64.b64encode(comprobante.foto.read()).decode("utf-8")
            logo = base64.b64encode(open("static/img/logo.png", "rb").read()).decode(
                "utf-8"
            )
        context = {
            "comprobante": comprobante,
            "foto": foto,
            "logo": logo,
        }

        html = render_to_string("operador_pdf.html", context)

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="Ficha de Operador.pdf"'

        # Genera el PDF
        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse("Error al generar el PDF")

        return response


@login_required
def ventas_y_participantes(request: HttpRequest):
    evento = Evento.obtener_actual()
    if not evento:
        return render(request, "gestion/inicio.html", {"evento": None})

    total_tickets = evento.total_tickets
    tickets_vendidos = NumeroRifa.objects.filter(evento=evento).count()
    tickets_restantes = total_tickets - tickets_vendidos

    if total_tickets > 0:
        porcentaje = (tickets_vendidos / total_tickets) * 100
    else:
        porcentaje = 0

    personas = (
        Comprobante.objects.filter(evento=evento)
        .values("telefono", "nombre")
        .annotate(num_tickets=Count("numerorifa"))
        .order_by("-num_tickets")[:10]
    )

    # Obtener el total de visualizaciones de la página
    total_visualizaciones = Visualizacion.objects.filter(evento=evento).count()

    comprobante_por_metodos = (
        Comprobante.objects.filter(evento=evento)
        .values("metodo")
        .annotate(
            cantidad=Count("metodo"),
            total=Sum("monto"),
            pagado=Sum("monto", filter=Q(status=StatusChoices.VERIFICADO)),
            cantidad_pagado=Count("metodo", filter=Q(status=StatusChoices.VERIFICADO)),
            cantidad_faltante=Count(
                "metodo", filter=Q(status=StatusChoices.NO_VERIFICADO)
            ),
            faltante=Sum("monto", filter=Q(status=StatusChoices.NO_VERIFICADO)),
        )
        .order_by("metodo")
    )
    for c in comprobante_por_metodos:
        c["nombre"] = MetodosChoices(c["metodo"]).label
    context = {
        "porcentaje": porcentaje,
        "evento": evento,
        "tickets_vendidos": tickets_vendidos,
        "metodos": dict(MetodosChoices.choices),
        "total_tickets": total_tickets,
        "tickets_restantes": tickets_restantes,
        "personas": personas,
        "total_visualizaciones": total_visualizaciones,
        "comprobante_por_metodos": comprobante_por_metodos,
    }

    return render(request, "gestion/estadisticas.html", context)
