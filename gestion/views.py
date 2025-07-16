from datetime import timedelta
from typing import Optional
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    BooleanField,
    Case,
    Count,
    F,
    Min,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Round
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import render
from django.utils import timezone
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from .forms import (
    ClienteForm,
    CompraForm,
    MetodoForm,
    RifaForm,
)
from .models import (
    Cliente,
    Comprobante,
    Evento,
    MetodoPago,
    MonedasChoices,
    NumeroRifa,
    StatusChoices,
)
from .utils import (
    CachedPaginator,
    CacheInvalidationMixin,
    calcular_monto,
    send_whatsapp,
    updateCompraCache,
)


@login_required
def participantesView(request: HttpRequest):
    evento = Evento.obtener_actual(fields=["id"])

    participantes = (
        Comprobante.objects.filter(evento=evento)
        .values("telefono")
        .annotate(
            num_tickets=Count("numerorifa"),
            boletos=ArrayAgg("numerorifa__numero"),
        )
        .order_by("-num_tickets")
        .values("telefono", "num_tickets", "boletos")
    )

    paginator = CachedPaginator(participantes, 10, "participantes")
    page_obj = paginator.page(request.GET.get("page", "1"))
    telefonos = [p["telefono"] for p in page_obj.object_list]
    participantes_info = list(
        Comprobante.objects.filter(telefono__in=telefonos, evento=evento)
        .values("telefono")
        .annotate(total=Sum("monto"), nombre=Min("nombre"))
    )
    for p in page_obj.object_list:
        item = list(
            filter(lambda x: x["telefono"] == p["telefono"], participantes_info)
        )[0]
        p["total"] = item["total"]
        p["nombre"] = item["nombre"]
    return render(request, "admin/participantes.html", {"participantes": page_obj})


class RifasListView(LoginRequiredMixin, ListView):
    template_name = "admin/rifas.html"
    model = Evento
    context_object_name = "rifas"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(total_vendidos=Count("numerorifa")).order_by("-id")
        return queryset


class RifasCreateView(LoginRequiredMixin, CacheInvalidationMixin, CreateView):
    template_name = "admin/rifa_form.html"
    form_class = RifaForm
    success_url = "/admin/rifas"


class ClienteCreateView(LoginRequiredMixin, CacheInvalidationMixin, CreateView):
    template_name = "admin/cliente_form.html"
    form_class = ClienteForm
    success_url = "/admin/cliente"


class RifasUpdateView(LoginRequiredMixin, CacheInvalidationMixin, UpdateView):
    template_name = "admin/rifa_form.html"
    form_class = RifaForm
    success_url = "/admin/rifas"
    model = Evento


class ClientesListView(LoginRequiredMixin, ListView):
    template_name = "admin/clientes.html"
    model = Cliente
    context_object_name = "clientes"


class ClienteUpdateView(LoginRequiredMixin, CacheInvalidationMixin, UpdateView):
    template_name = "admin/cliente_form.html"
    form_class = ClienteForm
    success_url = "/admin/clientes"
    model = Cliente


class MetodosListView(LoginRequiredMixin, ListView):
    template_name = "admin/metodos.html"
    model = MetodoPago
    context_object_name = "metodos"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by("posicion")
        return queryset


class MetodoCreateView(LoginRequiredMixin, CacheInvalidationMixin, CreateView):
    template_name = "admin/metodo_form.html"
    form_class = MetodoForm
    success_url = "/admin/metodos"
    model = MetodoPago

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["monedas"] = MonedasChoices.choices
        return context


class MetodoUpdateView(LoginRequiredMixin, CacheInvalidationMixin, UpdateView):
    template_name = "admin/metodo_form.html"
    form_class = MetodoForm
    success_url = "/admin/metodos"
    model = MetodoPago

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["monedas"] = MonedasChoices.choices
        return context


class ComprasListView(LoginRequiredMixin, ListView):
    template_name = "admin/compras.html"
    model = Comprobante
    context_object_name = "compras"
    paginator_class = CachedPaginator
    paginate_by = 10

    def get_paginator(
        self, queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs
    ):
        if self.filtros:
            cache_key = None
        else:
            cache_key = f"compras-{self.request.GET.get('evento_id', 'actual')}"
        return self.paginator_class(
            queryset,
            per_page,
            cache_key=cache_key,
            orphans=orphans,
            allow_empty_first_page=allow_empty_first_page,
            **kwargs,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["eventos"] = Evento.objects.values("id", "nombre")
        context["statuses"] = StatusChoices.choices
        context["metodos"] = MetodoPago.objects.values("id", "banco")
        context["filtros"] = urlencode(self.filtros, doseq=True)
        return context

    def get_queryset(self) -> QuerySet:
        evento_id = self.request.GET.get("evento_id")
        evento_actual = Evento.obtener_actual(fields=["id"])

        if evento_id == "inactivas" or evento_id == "todos":
            comprobantes = Comprobante.objects.all()
            if evento_actual and evento_id == "inactivas":
                comprobantes = Comprobante.objects.exclude(evento_id=evento_actual.pk)
            evento_id = None
        elif evento_id is not None:
            comprobantes = Comprobante.objects.filter(evento__id=evento_id)
        elif evento_actual:
            comprobantes = Comprobante.objects.filter(evento_id=evento_actual.pk)
        else:
            return Comprobante.objects.filter(evento_id=None)
        filtros = self.filtros_queryset(evento_id)
        self.filtros = filtros
        comprobantes = (
            comprobantes.filter(**filtros)
            .annotate(
                boletos=ArrayAgg("numerorifa__numero"),
                cantidad=Count("numerorifa"),
                verificado=Case(
                    When(status=StatusChoices.VERIFICADO, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
                monto_bs=F("monto") * F("dolar"),
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
                "evento__url",
                "evento__nombre",
                "metodo__moneda",
                "monto_bs",
            )
            .order_by("-id")
        )
        return comprobantes

    def filtros_queryset(self, evento_id: Optional[str]):
        filtros = {}
        ticket = self.request.GET.get("ticket")
        nombre = self.request.GET.get("nombre")
        telefono = self.request.GET.get("telefono")

        referencia = self.request.GET.get("referencia")
        fecha_desde = self.request.GET.get("fecha_desde")
        fecha_hasta = self.request.GET.get("fecha_desde")
        creados_hace_mas_de = self.request.GET.get("creados_hace_mas_de")
        status = self.request.GET.get("status")
        metodo_pago = self.request.GET.get("metodo")
        nota = self.request.GET.get("nota")
        tipo_nota = self.request.GET.get("tipo_nota")
        evento_id = self.request.GET.get("evento_id", "")
        if evento_id.isdigit():
            filtros["evento_id"] = evento_id
        if ticket:
            ticket = ticket.strip()
            numero = NumeroRifa.objects.filter(numero=ticket)
            if evento_id:
                numero = numero.filter(evento_id=evento_id)
            filtros["id__in"] = numero.values_list("comprobante_id", flat=True)
        if nombre:
            nombre = nombre.strip()
            filtros["nombre__icontains"] = nombre
        if telefono:
            telefono = telefono.strip()
            if telefono.startswith("0"):
                telefono = telefono[1:]
            filtros["telefono__icontains"] = telefono
        if referencia:
            referencia = referencia.strip()
            filtros["referencia__icontains"] = referencia
        if fecha_desde and fecha_hasta:
            filtros["fecha_creado__range"] = (fecha_desde, fecha_hasta)
        if creados_hace_mas_de:
            current_time = timezone.now()
            horas = int(creados_hace_mas_de)
            time_result = current_time - timedelta(hours=horas)
            filtros["fecha_creado__lte"] = time_result
        if status:
            filtros["status"] = status
        if metodo_pago:
            filtros["metodo"] = metodo_pago
        if nota and tipo_nota:
            nota = nota.strip()
            filtros[tipo_nota] = nota
        return filtros


class ComprasCreateView(LoginRequiredMixin, CreateView):
    template_name = "admin/compra_form.html"
    form_class = CompraForm
    success_url = "/admin/compras"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evento = Evento.obtener_actual(
            fields=["id", "nombre", "total_tickets", "valor_dolar"]
        )
        if evento is None:
            return context
        agarrados = NumeroRifa.objects.filter(evento=evento).values_list(
            "numero", flat=True
        )
        tickets = [format(t, evento.digitos) for t in range(evento.total_tickets)]
        disponibles = [n for n in range(evento.total_tickets) if n not in agarrados]
        agarrados = [format(a, evento.digitos) for a in agarrados]
        metodos = MetodoPago.objects.values("id", "banco").order_by("posicion")
        context["tickets"] = tickets
        context["agarrados"] = agarrados
        context["disponibles"] = disponibles
        context["status_choices"] = StatusChoices.choices
        context["metodos"] = metodos
        context["evento"] = evento
        context["dolar"] = evento.valor_dolar
        return context

    def form_valid(self, form):
        boletos = self.request.POST.getlist("tickets")
        boletos = set(boletos)
        evento = Evento.obtener_actual(fields=["id", "total_tickets"])
        if not evento:
            txt_error = "No puede agregar una compra si no hay una rifa en curso"
            form.add_error(None, txt_error)
            return self.form_invalid(form)
        numeros_existentes = NumeroRifa.objects.filter(
            evento=evento, numero__in=boletos
        ).values_list("numero", flat=True)
        if len(numeros_existentes) > 0:
            nums_err = [format(n, evento.digitos) for n in numeros_existentes]
            txt_error = "Ya existe otra compra con estos números " + " ".join(nums_err)
            form.add_error(None, txt_error)
            return self.form_invalid(form)
        if len(boletos) == 0:
            form.add_error(None, "No ha agregado números a esta compra")
            return self.form_invalid(form)
        form.instance.monto = calcular_monto(evento, len(boletos))
        response = super().form_valid(form)
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

        form.instance.save(update_fields=["monto"])
        updateCompraCache(evento.id)
        return response


class ComprasUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "admin/compra_form.html"
    form_class = CompraForm
    model = Comprobante
    object: model

    def get_success_url(self) -> str:
        query_params = self.request.GET.urlencode()
        return f"/admin/compras/?{query_params}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evento = self.object.evento
        agarrados = NumeroRifa.objects.filter(evento=evento).values_list(
            "numero", flat=True
        )
        tickets = [format(t, evento.digitos) for t in range(evento.total_tickets)]
        seleccionados = self.object.boletos.values_list("numero", flat=True)
        seleccionados = [format(b, evento.digitos) for b in seleccionados]
        disponibles = [n for n in range(evento.total_tickets) if n not in agarrados]
        agarrados = [format(a, evento.digitos) for a in agarrados]
        metodos = MetodoPago.objects.values("id", "banco").order_by("posicion")
        context["tickets"] = tickets
        context["agarrados"] = agarrados
        context["disponibles"] = disponibles
        context["status_choices"] = StatusChoices.choices
        context["metodos"] = metodos
        context["evento"] = evento
        context["seleccionados"] = seleccionados
        return context

    def form_valid(self, form):
        boletos = set(self.request.POST.getlist("tickets"))
        evento = self.object.evento
        numeros_existentes = (
            NumeroRifa.objects.exclude(comprobante=form.instance)
            .filter(evento_id=evento.pk, numero__in=boletos)
            .values_list("numero", flat=True)
        )
        if len(numeros_existentes) > 0:
            nums_exist = [format(n, evento.digitos) for n in numeros_existentes]
            txt_err = "Ya existe otra compra con estos números " + " ".join(nums_exist)
            form.add_error(None, txt_err)
            return self.form_invalid(form)
        if form.initial["status"] != form.data["status"]:
            if form.data["status"] == StatusChoices.VERIFICADO:
                form.instance.fecha_verificacion = timezone.now()
            msg = (
                "Su comprobante ha sido "
                + form.instance.get_status_display()
                + ". Los boletos verificados son "
                + " ,".join(boletos)
            )
            send_whatsapp(form.instance.telefono, msg)
        form.instance.monto = calcular_monto(evento, len(boletos))
        response = super().form_valid(form)
        eliminados = self.request.POST.getlist("eliminados")
        boletos = [b for b in boletos if b not in eliminados]
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
        return response


@login_required
def dashboardView(request: HttpRequest):
    eventos = Evento.objects.only("id", "nombre", "fecha_fin").all().order_by("-id")
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
        comprobantes.values("telefono")
        .annotate(
            num_tickets=Count("numerorifa"),
            nombre=Min("nombre"),
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
    progreso = round(total_numeros / evento_actual.total_tickets, 4) * 100
    context = {
        "eventos": eventos,
        "evento_actual": evento_actual,
        "total_participantes": total_participantes,
        "total_comprobantes": total_comprobantes,
        "total_numeros": total_numeros,
        "por_cofirmar": por_cofirmar,
        "verificados": verificados,
        "progreso": progreso,
        "total_disponibles": total_disponibles,
    }
    return render(request, "admin/dashboard.html", context)


@login_required
def usuariosView(request: HttpRequest):
    return render(request, "admin/usuarios.html")


@login_required
def ojoView(request: HttpRequest):
    return render(request, "admin/ojo.html")
