from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import (
    Case,
    CharField,
    Count,
    Min,
    Sum,
    Value,
    F,
    When,
)
from django.db.models.expressions import RawSQL
from django.db.models.functions import Concat, ExtractWeekDay, Round
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Comprobante,
    Evento,
    MetodoPago,
    NumeroRifa,
    StatusChoices,
)
from .utils import calcular_tickets_frecuentes
from .tasks import send_whatsapp

@require_POST
@login_required
def verificar_comprobante(request: HttpRequest, pk: int):
    comprobante = Comprobante.objects.select_related("evento").get(pk=pk)
    if comprobante.status != StatusChoices.VERIFICADO:
        comprobante.status = StatusChoices.VERIFICADO
        fecha_actual = timezone.now()
        comprobante.fecha_verificacion = fecha_actual
        comprobante.save(update_fields=("status", "fecha_verificacion"))
        url = comprobante.get_full_url(request)
        msg = f"Hola {comprobante.nombre}, gracias por completar tu pago de tus números de {comprobante.evento.nombre} y los puedes verificar en {url}"
        send_whatsapp.delay(comprobante.telefono, msg)
        hora = fecha_actual.strftime("%I:%M %p")
        fecha = fecha_actual.strftime("%d %B %Y")
        return JsonResponse({"result": "ok", "fecha": fecha, "hora": hora})
    return JsonResponse({"result": "verificado"})


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
    try:
        evento.delete()
        cache.clear()
        return JsonResponse({"result": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)})


@login_required
@require_POST
def eliminar_metodo(request: HttpRequest, pk: int):
    metodo_pago = get_object_or_404(MetodoPago, pk=pk)
    try:
        metodo_pago.delete()
        cache.clear()
        return JsonResponse({"result": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)})


@login_required
def ver_fecha_compra_stats(request: HttpRequest, evento_id: int):
    fecha_participantes = []
    fecha_compra = []
    fecha_comprobantes = (
        Comprobante.objects.filter(evento=evento_id)
        .values("fecha_creado")
        .annotate(
            num_compras=Count("id"),
            num_participantes=Count("telefono", distinct=True),
            fecha=RawSQL("TO_CHAR(fecha_creado, 'YYYY-MM-DD')", ()),
        )
        .order_by("-fecha_creado")
    )
    for comprobante in fecha_comprobantes:
        fecha_compra.append((comprobante["fecha"], comprobante["num_compras"]))
        fecha_participantes.append(
            (comprobante["fecha"], comprobante["num_participantes"])
        )
    data = {"participantes": fecha_participantes, "compras": fecha_compra}
    return JsonResponse(data)


@login_required
def ver_fecha_tickets_stats(request: HttpRequest, evento_id: int):
    """
    No se puede juntar con ver_fecha_compra_stats, ya que el inner join numerorifa
    distorsiona los resultados
    """
    fecha_tickets = list(
        Comprobante.objects.filter(evento=evento_id)
        .values("fecha_creado")
        .annotate(
            fecha=RawSQL("TO_CHAR(fecha_creado, 'YYYY-MM-DD')", ()),
            num_tickets=Count("numerorifa"),
        )
        .order_by("-fecha_creado")
        .values_list("fecha", "num_tickets")
    )
    data = {"tickets": fecha_tickets}
    return JsonResponse(data)


@login_required
def ver_metodos_status_stats(request: HttpRequest, evento_id: int):
    metodos_aprobados = list(
        Comprobante.objects.filter(evento=evento_id)
        .filter(status=StatusChoices.VERIFICADO)
        .values("metodo__banco")
        .annotate(
            monto=Concat(Round(Sum("monto"), 2), Value("$"), output_field=CharField()),
            banco=Concat(
                F("metodo__banco"), Value(" - "), F("monto"), output_field=CharField()
            ),
        )
        .values_list("banco", "monto")
    )
    metodos_confirmar = list(
        Comprobante.objects.filter(evento=evento_id)
        .filter(status=StatusChoices.NO_VERIFICADO)
        .values("metodo__banco")
        .annotate(
            monto=Concat(Round(Sum("monto"), 2), Value("$"), output_field=CharField()),
            banco=Concat(
                F("metodo__banco"), Value(" - "), F("monto"), output_field=CharField()
            ),
        )
        .values_list("banco", "monto")
    )
    tickets_metodo = list(
        Comprobante.objects.filter(evento=evento_id)
        .values("metodo__banco")
        .annotate(
            compras=Count("id"),
        )
        .values_list("metodo__banco", "compras")
    )
    data = {
        "aprobados": metodos_aprobados,
        "por_confirmar": metodos_confirmar,
        "tickets_metodo": tickets_metodo,
    }
    return JsonResponse(data)


@login_required
def ver_top_participante_stats(request: HttpRequest, evento_id: int):
    participantes = list(
        Comprobante.objects.filter(evento=evento_id)
        .values("telefono")
        .annotate(
            num_tickets=Count("numerorifa"),
            nombre=Min("nombre"),
        )
        .order_by("-num_tickets")
        .values_list("nombre", "num_tickets")[:10]
    )
    data = {"participantes": participantes}
    return JsonResponse(data)


@login_required
def ver_dias_ventas_stats(request: HttpRequest, evento_id: int):
    dias_ventas = list(
        Comprobante.objects.filter(evento=evento_id)
        .annotate(
            weekday=ExtractWeekDay("fecha_creado"),
            dia_semana=Case(
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
        .values("dia_semana")
        .annotate(cantidad=Count("numerorifa__id"))
        .values_list("dia_semana", "cantidad")
    )
    data = {"dias_ventas": dias_ventas}
    return JsonResponse(data)


@login_required
def ver_tickets_frecuentes_stats(request: HttpRequest, evento_id: int):
    tickets_frecuentes = calcular_tickets_frecuentes(evento_id)
    return JsonResponse({"tickets_frecuentes": tickets_frecuentes})
