from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import (
    Count,
)
from django.db.models.expressions import RawSQL
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
from .utils import send_whatsapp


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
        send_whatsapp(comprobante.telefono, msg)
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
def ver_fecha_stats(request: HttpRequest, evento_id: int):
    fecha_tickets = []
    fecha_compras = []
    fecha_participantes = []
    fecha_comprobantes = (
        Comprobante.objects.filter(evento=evento_id)
        .values("fecha_creado")
        .annotate(
            num_tickets=Count("numerorifa"),
            num_compras=Count("id"),
            num_participantes=Count("telefono", distinct=True),
            fecha=RawSQL("TO_CHAR(fecha_creado, 'YYYY-MM-DD')", ()),
        )
        .order_by("-fecha_creado")
    )
    for comprobante in fecha_comprobantes:
        fecha_tickets.append((comprobante["fecha"], comprobante["num_tickets"]))
        fecha_compras.append((comprobante["fecha"], comprobante["num_compras"]))
        fecha_participantes.append(
            (comprobante["fecha"], comprobante["num_participantes"])
        )

    data = {
        "tickets": fecha_tickets,
        "compras": fecha_compras,
        "participantes": fecha_participantes,
    }
    return JsonResponse(data)


def ver_fecha_compras_stats(request: HttpRequest, evento_id: int):
    """
    No se puede juntar con ver_fecha_tickets_stats, ya que el inner join numerorifa
    distorsiona los resultados
    """
