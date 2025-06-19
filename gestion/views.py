from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import ArrayAgg  # Import this!
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Count,
    F,
    Min,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Concat, ExtractWeekDay, Round
from django.db.models.query import QuerySet
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST
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
    evento = Evento.obtener_actual(fields=("id",))
    participantes = (
        Comprobante.objects.filter(evento=evento)
        .values("telefono")
        .annotate(
            num_tickets=Count("numerorifa"),
            total=Round(Sum("monto"), 2),
            boletos=ArrayAgg("numerorifa__numero"),
            nombre=Min("nombre"),
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

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by("posicion")
        return queryset


class MetodoCreateView(LoginRequiredMixin, CreateView):
    template_name = "admin/metodo_form.html"
    form_class = MetodoForm
    success_url = "/admin/metodos"
    model = MetodoPago

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["monedas"] = MonedasChoices.choices
        return context


class MetodoUpdateView(LoginRequiredMixin, UpdateView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["eventos"] = Evento.objects.values("id", "nombre")
        context["statuses"] = StatusChoices.choices
        context["metodos"] = MetodoPago.objects.values("id", "banco")
        return context

    def get_queryset(self) -> QuerySet:
        evento_id = self.request.GET.get("evento_id")
        evento_actual = Evento.obtener_actual(fields=("id",))
        comprobantes = Comprobante.objects.all()
        if evento_id and evento_id != "todos" and evento_id != "inactivas":
            comprobantes = Comprobante.objects.filter(evento__id=evento_id)
        elif evento_id == "inactivas":
            if evento_actual:
                comprobantes = Comprobante.objects.exclude(evento_id=evento_actual.pk)
            evento_id = None
        else:
            if evento_actual:
                comprobantes = Comprobante.objects.filter(evento_id=evento_actual.pk)
            evento_id = None

        filtros = {}
        # filtro
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

        if ticket:
            numero = NumeroRifa.objects.filter(numero=ticket)
            if evento_id:
                numero = numero.filter(evento_id=evento_id)
            filtros["id__in"] = numero.values_list("comprobante_id", flat=True)
        if nombre:
            filtros["nombre__icontains"] = nombre
        if telefono:
            filtros["telefono__icontains"] = telefono
        if referencia:
            filtros["referencia__icontains"] = referencia
        if fecha_desde and fecha_hasta:
            filtros["fecha_creado__range"] = (fecha_desde, fecha_hasta)
        if creados_hace_mas_de:
            current_time = timezone.now()
            time_result = current_time - timedelta(hours=4)
            filtros["fecha_creado__lte"] = time_result
        if status:
            filtros["status"] = status
        if metodo_pago:
            filtros["metodo"] = metodo_pago
        if nota and tipo_nota:
            filtros[tipo_nota] = nota
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
                "metodo__moneda",
                "monto_bs",
            )
            .order_by("-id")
        )
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
        context["metodos"] = MetodoPago.objects.all().order_by("posicion")
        context["evento"] = evento
        context["dolar"] = evento.valor_dolar
        return context

    def form_valid(self, form):
        boletos = self.request.POST.getlist("tickets")
        numeros_existentes = NumeroRifa.objects.exclude(
            comprobante=form.instance
        ).filter(numero__in=boletos)
        if numeros_existentes.exists():
            form.add_error(
                "Boletos",
                "Ya existe un boleto con estos números"
                + " ".join(numeros_existentes.values_list("numero", flat=True)),
            )
            return self.form_invalid(form)
        response = super().form_valid(form)
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
    object: model

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
        context["tickets"] = tickets
        context["agarrados"] = agarrados
        context["disponibles"] = disponibles
        context["status_choices"] = StatusChoices.choices
        context["metodos"] = MetodoPago.objects.all().order_by("posicion")
        context["evento"] = evento
        context["seleccionados"] = seleccionados
        return context

    def form_valid(self, form):
        ultimo_status = Comprobante.objects.get(id=form.instance.id).status
        boletos = self.request.POST.getlist("tickets")
        numeros_existentes = NumeroRifa.objects.exclude(
            comprobante=form.instance
        ).filter(numero__in=boletos)
        if numeros_existentes.exists():
            values = numeros_existentes.values_list("numero", flat=True)
            values = [f"{v}" for v in values]
            form.add_error(
                None, "Ya existe un boleto con estos números" + " ".join(values)
            )
            return self.form_invalid(form)
        response = super().form_valid(form)
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
            telefono_url = comprobante.telefono.replace("+", "%2B")
            url = f"https://www.chipibikelifee.com/rifa/comboexclusivo/?phone={telefono_url}"
            msg = f"Hola {comprobante.nombre}, gracias por completar tu pago de tus números de {comprobante.evento.nombre} y los puedes verificar en {url}"
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
    participantes_comprobantes = (
        comprobantes.values("fecha_creado")
        .annotate(
            num_compras=Count("id"),
            num_participantes=Count("telefono", distinct=True),
        )
        .order_by("-fecha_creado")
    )
    participantes_comprobantes_str = []
    for p_c in participantes_comprobantes:
        p_c["fecha_creado"] = p_c["fecha_creado"].strftime("%Y-%m-%d")
        participantes_comprobantes_str.append(
            f"{p_c['fecha_creado']};{p_c['num_compras']};{p_c['num_participantes']}"
        )

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
        "participantes_comprobantes": ",".join(participantes_comprobantes_str),
        "tickets_metodo": tickets_metodo_str,
        "metodos_aprobados": metodos_aprobados_str,
        "metodos_confirmar": metodos_confirmar_str,
        "tickets_frecuentes": tickets_frecuentes,
        "total_disponibles": total_disponibles,
        "dias_ventas": dias_ventas_str,
    }
    return render(request, "admin/dashboard.html", context)


@login_required
def usuariosView(request: HttpRequest):
    return render(request, "admin/usuarios.html")


@login_required
def ojoView(request: HttpRequest):
    return render(request, "admin/ojo.html")
