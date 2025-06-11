from typing import Optional

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import ArrayAgg  # Import this!
from django.db.models import BooleanField, Case, CharField, Count, Q, Sum, Value, When
from django.db.models.functions import Concat, ExtractWeekDay, Round
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import View
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from .forms import (
    ClienteForm,
    CompraForm,
    FormComprobante,
    FormEvento,
    MetodoForm,
    RifaForm,
)
from .models import (
    Cliente,
    Comprobante,
    Evento,
    MetodoPago,
    MetodosChoices,
    NumeroRifa,
    Promocion,
    StatusChoices,
    Visualizacion,
)
from .utils import (
    calcular_monto,
    calcular_tickets_frecuentes,
    list2values,
    send_whatsapp,
)


@login_required
def inicioView(request: HttpRequest):
    return render(request, "admin/compras.html")


@login_required
def participantesView(request: HttpRequest):
    evento = Evento.obtener_actual()
    participantes = (
        Comprobante.objects.filter(evento=evento)
        .values("telefono", "nombre")
        .annotate(
            num_tickets=Count("numerorifa"),
            total=Round(Sum("monto"), 2),
            boletos=ArrayAgg("numerorifa__numero"),
        )
        .order_by("-num_tickets")
    )
    return render(request, "admin/participantes.html", {"participantes": participantes})


class RifasListView(LoginRequiredMixin, ListView):
    template_name = "admin/rifas.html"
    model = Evento
    context_object_name = "rifas"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by("-id")
        return queryset


class RifasCreateView(LoginRequiredMixin, CreateView):
    template_name = "admin/rifa_form.html"
    form_class = RifaForm
    success_url = "/admin/rifas"


class ClienteCreateView(LoginRequiredMixin, CreateView):
    template_name = "admin/cliente_form.html"
    form_class = ClienteForm
    success_url = "/admin/cliente"


class RifasUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "admin/rifa_form.html"
    form_class = RifaForm
    success_url = "/admin/rifas"
    model = Evento


class ClientesListView(LoginRequiredMixin, ListView):
    template_name = "admin/clientes.html"
    model = Cliente
    context_object_name = "clientes"


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "admin/cliente_form.html"
    form_class = ClienteForm
    success_url = "/admin/clientes"
    model = Cliente


class MetodosListView(LoginRequiredMixin, ListView):
    template_name = "admin/metodos.html"
    model = MetodoPago
    context_object_name = "metodos"


class MetodoCreateView(LoginRequiredMixin, CreateView):
    template_name = "admin/metodo_form.html"
    form_class = MetodoForm
    success_url = "/admin/metodos"
    model = MetodoPago


class MetodoUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "admin/metodo_form.html"
    form_class = MetodoForm
    success_url = "/admin/metodos"
    model = MetodoPago


class ComprasListView(LoginRequiredMixin, ListView):
    template_name = "admin/compras.html"
    model = Comprobante
    context_object_name = "compras"

    def get_queryset(self):
        evento_actual = Evento.obtener_actual()
        comprobantes = (
            Comprobante.objects.filter(evento=evento_actual)
            .select_related("numerorifa")
            .prefetch_related("numerorifa__numero")
            .annotate(
                boletos=ArrayAgg("numerorifa__numero"),
                cantidad=Count("numerorifa"),
                verificado=Case(
                    When(status=StatusChoices.VERIFICADO, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
            .values(
                "id",
                "nombre",
                "telefono",
                "referencia",
                "boletos",
                "status",
                "fecha",
                "fecha_verificacion",
                "foto",
                "monto",
                "metodo__banco",
                "nota",
                "cantidad",
                "verificado",
            )
        )
        # filtro
        nombre = self.request.GET.get("nombre")
        telefono = self.request.GET.get("telefono")
        referencia = self.request.GET.get("referencia")
        status = self.request.GET.get("status")
        fecha = self.request.GET.get("fecha")
        creados_hace_mas_de = self.request.GET.get("creados_hace_mas_de")
        metodo_pago = self.request.GET.get("metodo_pago")

        if nombre:
            comprobantes = comprobantes.filter(nombre__icontains=nombre)
        if telefono:
            comprobantes = comprobantes.filter(telefono__icontains=telefono)
        if referencia:
            comprobantes = comprobantes.filter(referencia__icontains=referencia)
        if status:
            comprobantes = comprobantes.filter(status__icontains=status)
        if fecha:
            comprobantes = comprobantes.filter(fecha=fecha)
        if creados_hace_mas_de:
            from datetime import timedelta

            from django.utils import timezone

            date_threshold = timezone.now() - timedelta(days=int(creados_hace_mas_de))
            comprobantes = comprobantes.filter(fecha__lt=date_threshold)
        if metodo_pago:
            comprobantes = comprobantes.filter(metodo__banco__icontains=metodo_pago)

        return comprobantes


class ComprasCreateView(LoginRequiredMixin, CreateView):
    template_name = "admin/compra_form.html"
    form_class = CompraForm
    success_url = "/admin/compras"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evento = Evento.obtener_actual()
        if evento is None:
            return context
        agarrados = NumeroRifa.objects.filter(
            comprobante__evento=evento
        ).prefetch_related("comprobante__evento")
        tickets = (format(t, evento.digitos) for t in range(evento.total_tickets))
        context["tickets"] = tickets
        context["agarrados"] = [str(a) for a in agarrados]
        context["disponibles"] = [
            n for n in range(evento.total_tickets) if n not in agarrados
        ]
        context["status_choices"] = StatusChoices.choices
        context["metodos"] = MetodoPago.objects.all()
        context["evento"] = evento
        context["dolar"] = evento.valor_dolar
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        boletos = self.request.POST.getlist("tickets")
        NumeroRifa.objects.filter(comprobante=form.instance).delete()
        if form.instance.status != StatusChoices.RECHAZADO:
            numeros = []
            for boleto in boletos:
                numero = NumeroRifa(
                    numero=boleto,
                    comprobante=form.instance,
                    evento=form.instance.evento,
                )
                numeros.append(numero)
            NumeroRifa.objects.bulk_create(numeros)
        form.instance.monto = calcular_monto(form.instance)
        form.instance.save(update_fields=["monto"])
        return response


class ComprasUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "admin/compra_form.html"
    form_class = CompraForm
    success_url = "/admin/compras"
    model = Comprobante

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evento = Evento.objects.get(pk=self.object.evento.pk)
        agarrados = NumeroRifa.objects.filter(
            comprobante__evento=evento
        ).prefetch_related("comprobante__evento")
        tickets = list(format(t, evento.digitos) for t in range(evento.total_tickets))
        seleccionados = list(
            format(b.numero, evento.digitos) for b in self.object.boletos
        )
        context["tickets"] = tickets
        context["agarrados"] = [str(a) for a in agarrados]
        context["disponibles"] = [
            n for n in range(evento.total_tickets) if n not in agarrados
        ]
        context["status_choices"] = StatusChoices.choices
        context["metodos"] = MetodoPago.objects.all()
        context["evento"] = evento
        context["seleccionados"] = seleccionados
        return context

    def form_valid(self, form):
        ultimo_status = Comprobante.objects.get(id=form.instance.id).status
        response = super().form_valid(form)
        boletos = self.request.POST.getlist("tickets")
        eliminados = self.request.POST.getlist("eliminados")
        boletos = [b for b in boletos if b not in eliminados]
        NumeroRifa.objects.filter(comprobante=form.instance).delete()
        msg = (
            "Su comprobante ha sido "
            + form.instance.get_status_display()
            + ". Los boletos verificados son "
            + " ,".join(boletos)
        )
        if ultimo_status != form.instance.status:
            send_whatsapp(form.instance.telefono, msg)
        if form.instance.status != StatusChoices.RECHAZADO:
            numeros = []
            for boleto in boletos:
                numero = NumeroRifa(
                    numero=boleto,
                    comprobante=form.instance,
                    evento=form.instance.evento,
                )
                numeros.append(numero)
            NumeroRifa.objects.bulk_create(numeros)
        form.instance.monto = calcular_monto(form.instance)
        form.instance.save(update_fields=["monto"])
        return response


@login_required
@require_POST
def eliminar_compra(request: HttpRequest, pk: int):
    comprobante = get_object_or_404(Comprobante, pk=pk)
    NumeroRifa.objects.filter(comprobante=comprobante).delete()
    comprobante.delete()
    return JsonResponse({"result": "ok"})


@login_required
@require_POST
def eliminar_rifa(request: HttpRequest, pk: int):
    evento = get_object_or_404(Evento, pk=pk)
    evento.delete()
    return JsonResponse({"result": "ok"})


@login_required
@require_POST
def eliminar_metodo(request: HttpRequest, pk: int):
    metodo_pago = get_object_or_404(MetodoPago, pk=pk)
    metodo_pago.delete()
    return JsonResponse({"result": "ok"})


@login_required
def verificar_comprobante(request: HttpRequest, pk: int):
    if request.method == "POST":
        comprobante = Comprobante.objects.get(pk=pk)
        if comprobante.status != StatusChoices.VERIFICADO:
            comprobante.status = StatusChoices.VERIFICADO
            fecha_actual = timezone.now()
            comprobante.fecha_verificacion = fecha_actual
            comprobante.save(update_fields=("status", "fecha_verificacion"))
            queryset = comprobante.boletos.values_list("numero", flat=True)
            boletos = (str(item) for item in queryset)
            msg = (
                "Su comprobante ha sido "
                + comprobante.get_status_display()  # type: ignore
                + ". Los boletos verificados son "
                + " ,".join(boletos)
            )
            send_whatsapp(comprobante.telefono, msg)
            hora = fecha_actual.strftime("%I:%M %p")
            fecha = fecha_actual.strftime("%d %B %Y")
            return JsonResponse({"result": "ok", "fecha": fecha, "hora": hora})
        return JsonResponse({"result": "verificado"})
    return render(request, "admin/verificar.html")


@login_required
def dashboardView(request: HttpRequest):
    eventos = Evento.objects.only("id", "nombre", "fecha_fin").all()
    evento_id = request.GET.get("rifa")
    evento_actual = Evento.obtener_actual(evento_id)
    if evento_actual is None:
        return render(request, "admin/dashboard.html", {"eventos": eventos})
    comprobantes = (
        Comprobante.objects.filter(evento=evento_actual)
        .select_related("numerorifa")
        .prefetch_related("numerorifa__numero")
    )

    participantes = (
        comprobantes.values("telefono", "nombre")
        .annotate(
            num_tickets=Count("numerorifa"),
        )
        .order_by("-num_tickets")
    )
    total_comprobantes = comprobantes.count()
    total_numeros = NumeroRifa.objects.filter(evento=evento_actual).count()
    total_disponibles = evento_actual.total_tickets - total_numeros
    total_participantes = participantes.count()
    por_cofirmar = (
        comprobantes.filter(status=StatusChoices.NO_VERIFICADO)
        .values("id", "monto")
        .annotate(boletos=Count("numerorifa"))
        .aggregate(
            monto=Round(Sum("monto"), 2),
            cantidad=Count("id"),
            tickets=Sum("boletos"),
        )
    )
    verificados = (
        comprobantes.filter(status=StatusChoices.VERIFICADO)
        .values("id", "monto")
        .annotate(boletos=Count("numerorifa"))
        .aggregate(
            monto=Round(Sum("monto"), 2),
            cantidad=Count("id"),
            tickets=Sum("boletos"),
        )
    )
    progreso = (total_numeros / evento_actual.total_tickets) * 100
    tickets_fecha = list(
        comprobantes.annotate(
            participante=Concat(
                "nombre", Value("|"), "telefono", output_field=CharField()
            )
        )
        .values("fecha_creado")
        .annotate(
            num_tickets=Count("numerorifa"),
            num_compras=Count("id"),
            num_participantes=Count("participante", distinct=True),
        )
        .order_by("-fecha_creado")
    )
    tickets_fecha_str = []
    for t_f in tickets_fecha:
        t_f["fecha_creado"] = t_f["fecha_creado"].strftime("%Y-%m-%d")
        tickets_fecha_str.append(
            f"{t_f['fecha_creado']};{t_f['num_tickets']};{t_f['num_compras']};{t_f['num_participantes']}"
        )
    tickets_metodo = list(
        comprobantes.select_related("metodo")
        .prefetch_related("metodo__banco")
        .values("metodo__banco")
        .annotate(
            compras=Count("id"),
        )
    )
    tickets_metodo_str = list2values(tickets_metodo)
    metodos_aprobados = list(
        comprobantes.filter(status=StatusChoices.VERIFICADO)
        .select_related("metodo")
        .prefetch_related("metodo__banco")
        .values("metodo__banco")
        .annotate(
            monto=Round(Sum("monto"), 2),
        )
    )
    metodos_confirmar = list(
        comprobantes.select_related("metodo")
        .filter(status=StatusChoices.NO_VERIFICADO)
        .prefetch_related("metodo__banco")
        .values("metodo__banco")
        .annotate(
            monto=Round(Sum("monto"), 2),
        )
    )
    metodos_aprobados_str = list2values(metodos_aprobados)
    metodos_confirmar_str = list2values(metodos_confirmar)
    participantes = list(participantes[:10].values("nombre", "num_tickets"))
    participantes_str = list2values(participantes)

    tickets_frecuentes = calcular_tickets_frecuentes(evento_actual.pk)
    tickets_frecuentes = [f"{t[0]} tickets;{t[1]}" for t in tickets_frecuentes]
    tickets_frecuentes = ",".join(tickets_frecuentes)
    dias_ventas = list(
        comprobantes.annotate(
            weekday=ExtractWeekDay("fecha_creado"),
            weekday_string=Case(
                When(weekday=1, then=Value("Domingo")),
                When(weekday=2, then=Value("Lunes")),
                When(weekday=3, then=Value("Martes")),
                When(weekday=4, then=Value("Miércoles")),
                When(weekday=5, then=Value("Jueves")),
                When(weekday=6, then=Value("Viernes")),
                When(weekday=7, then=Value("Sábado")),
                output_field=CharField(),
            ),
        )
        .values("weekday_string")
        .annotate(cantidad=Count("numerorifa__id"))
    )
    dias_ventas_str = list2values(dias_ventas)

    context = {
        "eventos": eventos,
        "evento_actual": evento_actual,
        "total_participantes": total_participantes,
        "total_comprobantes": total_comprobantes,
        "total_numeros": total_numeros,
        "participantes": participantes_str,
        "por_cofirmar": por_cofirmar,
        "verificados": verificados,
        "progreso": round(progreso, 2),
        "tickets_fecha": ",".join(tickets_fecha_str),
        "tickets_metodo": tickets_metodo_str,
        "metodos_aprobados": metodos_aprobados_str,
        "metodos_confirmar": metodos_confirmar_str,
        "tickets_frecuentes": tickets_frecuentes,
        "total_disponibles": total_disponibles,
        "dias_ventas": dias_ventas_str,
    }
    return render(request, "admin/dashboard.html", context)


def obtener_grafiicas(request: HttpRequest, evento_id: int):
    evento = Evento.objects.get(pk=evento_id)
    return JsonResponse({"result": "ok"})


@login_required
def usuariosView(request: HttpRequest):
    return render(request, "admin/usuarios.html")


@login_required
def ojoView(request: HttpRequest):
    return render(request, "admin/ojo.html")


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
            comprobante.telefono = (
                comprobante.telefono.replace(" ", "")
                .replace("+", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )
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
            total=Round(Sum("monto"), 2),
            pagado=Round(Sum("monto", filter=Q(status=StatusChoices.VERIFICADO))),
            cantidad_pagado=Count("metodo", filter=Q(status=StatusChoices.VERIFICADO)),
            cantidad_faltante=Count(
                "metodo", filter=Q(status=StatusChoices.NO_VERIFICADO)
            ),
            faltante=Round(
                Sum("monto", filter=Q(status=StatusChoices.NO_VERIFICADO)), 2
            ),
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
