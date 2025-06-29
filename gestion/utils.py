import logging
import re
from typing import Protocol, TypedDict, cast
from urllib.parse import urljoin

import requests
from django.contrib.postgres.aggregates import ArrayAgg  # Import this!
from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Sum
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.core.paginator import Paginator, Page
from gestion.models import Comprobante, Evento, Promocion, StatusChoices

logger = logging.getLogger(__name__)

WHATSAPP_URL = "http://localhost:3002/"


def send_whatsapp(num: str, msg: str):
    number = "".join(re.findall(r"\d+", num))
    try:
        link = urljoin(WHATSAPP_URL, "api/sendText")
        data = {
            "chatId": number,
            "reply_to": None,
            "text": msg,
            "linkPreview": False,
            "linkPreviewHighQuality": False,
            "session": "default",
        }
        response = requests.post(link, json=data)
        if response.status_code == 422:
            activate_session()
            response = requests.post(link, json=data)
        if response.status_code != 201:
            print(f"{response.status_code} Error al enviar whatsapp")
    except Exception:
        print("ERROR al enviar whatsapp")


def activate_session():
    link = urljoin(WHATSAPP_URL, "api/sessions/default/restart")
    requests.post(link)
    link = urljoin(WHATSAPP_URL, "api/default/presence")
    data = {"presence": "offline"}
    requests.post(link, json=data)


class PromocionDict(TypedDict):
    """Representa una promoción de boletos con cantidad y precio en descuento.

    Attributes:
        cantidad_tickets: Número de boletos requeridos para aplicar esta promoción
        precio: Precio total en descuento para esta cantidad de boletos
    """

    cantidad_tickets: int
    precio: int


def calcular_monto(evento: Evento, cant_boletos: int):
    evento = evento
    precio_unidad = evento.precio_unidad
    promociones = cast(
        list[PromocionDict],
        list(
            Promocion.objects.filter(evento=evento).values("cantidad_tickets", "precio")
        ),
    )
    index = len(promociones) - 1
    total = 0
    return calcular_precio(cant_boletos, precio_unidad, promociones, index, total)


def calcular_precio(
    boletos: int,
    precio_unidad: float,
    promociones: list[PromocionDict],
    index: int,
    total: float,
) -> float:
    """Calcula el precio total de los boletos aplicando promociones disponibles.

    Args:
        boletos: Cantidad de boletos a comprar
        precio_unidad: Precio por boleto sin promoción
        promociones: Lista de promociones disponibles, ordenadas de mayor a menor
        index: Índice de la promoción actual a evaluar (para recursión)
        total: Acumulador del precio total (para recursión)

    Returns:
        El precio total después de aplicar las mejores promociones posibles
    """
    # Caso base: no hay más promociones que chequear
    if index < 0:
        return total + boletos * precio_unidad

    promocion = promociones[index]

    # Caso 1: Promocion actual puede ser aplicada
    if promocion["cantidad_tickets"] <= boletos:
        boletos -= promocion["cantidad_tickets"]
        total += promocion["precio"]

    # Caso 2: Intentar siguiente promocion
    elif index > 0:
        index -= 1

    # Caso 3: No hay más promociones aplicables
    else:
        total += boletos * precio_unidad
        boletos = 0

    # Devuelve la función o sigue la recursividad
    if boletos == 0:
        return total
    else:
        return calcular_precio(boletos, precio_unidad, promociones, index, total)


def generar_estadisticas(evento: Evento):
    comprobantes = list(
        Comprobante.objects.filter(evento=evento)
        .select_related("numerorifa", "metodo")
        .prefetch_related("numerorifa__numero", "metodo__banco")
        .annotate(
            tickets=ArrayAgg("numerorifa__numero"),
        )
        .values(
            "nombre",
            "telefono",
            "tickets",
            "fecha_creado",
            "monto",
            "metodo__banco",
            "status",
        )
    )
    participantes = obtener_participantes(evento)
    total_comprobantes = len(comprobantes)
    total_participantes = participantes.count()
    top_participantes = participantes[:10]
    por_confirmar = {"monto": 0, "cantidad": 0, "tickets": 0}
    verificados = {"monto": 0, "cantidad": 0, "tickets": 0}
    tickets_fecha_d = {}
    tickets_metodo_d = {}
    total_numeros = 0
    for c in comprobantes:
        c_numeros = len(c["tickets"])
        total_numeros += c_numeros
        participante = f"{c['telefono']} {c['nombre']}"
        fecha = c["fecha_creado"].strftime("%Y-%m-%d")
        metodo = c["metodo__banco"]
        if c["status"] == StatusChoices.NO_VERIFICADO:
            por_confirmar["monto"] += c["monto"]
            por_confirmar["cantidad"] += 1
            por_confirmar["tickets"] += c_numeros
        elif c["status"] == StatusChoices.VERIFICADO:
            verificados["monto"] += c["monto"]
            verificados["cantidad"] += 1
            verificados["tickets"] += c_numeros
        if fecha not in tickets_fecha_d:
            tickets_fecha_d[fecha] = {
                "tickets": c_numeros,
                "cantidad": 1,
                "monto": c["monto"],
                "participantes": set(participante),
            }
        else:
            tickets_fecha_d[fecha]["tickets"] += c_numeros
            tickets_fecha_d[fecha]["cantidad"] += 1
            tickets_fecha_d[fecha]["monto"] += c["monto"]
            tickets_fecha_d[fecha]["participantes"].add(participante)
        if metodo not in tickets_metodo_d:
            tickets_metodo_d[metodo] = {
                "tickets": c_numeros,
                "cantidad": 1,
                "monto": c["monto"],
            }
        else:
            tickets_metodo_d[metodo]["tickets"] += c_numeros
            tickets_metodo_d[metodo]["cantidad"] += 1
            tickets_metodo_d[metodo]["monto"] += c["monto"]
    progreso = round(total_numeros / evento.total_tickets, 4) * 100
    return {
        "total_participantes": total_participantes,
        "total_comprobantes": total_comprobantes,
        "total_numeros": total_numeros,
        "participantes": top_participantes,
        "por_cofirmar": por_confirmar,
        "verificados": verificados,
        "progreso": round(progreso, 2),
        "tickets_fecha": tickets_fecha_d,
        "tickets_metodo": tickets_metodo_d,
    }


def obtener_participantes(evento: Evento):
    return (
        Comprobante.objects.filter(evento=evento)
        .select_related("numerorifa")
        .prefetch_related(
            "numerorifa__numero",
        )
        .values("telefono", "nombre")
        .annotate(
            num_tickets=Count("numerorifa"),
            total=Sum("monto"),
            boletos=ArrayAgg("numerorifa__numero"),
        )
        .order_by("-num_tickets")
    )


def list2values(list_v: list):
    str_list = []
    for element in list_v:
        element: dict
        values = [str(v) for v in element.values()]
        str_list.append(";".join(values))
    return ",".join(str_list)


def calcular_tickets_frecuentes(evento_id: int):
    """
    Devuelve la cantidad de tickets que más se compran en este formato
    (cant_tickets, frecuencia)
    Ejemplo si hay 7 comprobantes, 3 de ellos tienen 2 boletos y 4 tienen 1 boleto el resultado
    sería
    ((1,4), (2,3))
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                subquery.compras  || ' tickets' AS "count_value",
                COUNT(*) AS "frequency"
            FROM (
                SELECT
                    COUNT("gestion_numerorifa"."comprobante_id") AS "compras"
                FROM "gestion_numerorifa"
                INNER JOIN "gestion_comprobante"
                    ON ("gestion_numerorifa"."comprobante_id" = "gestion_comprobante"."id")
                WHERE "gestion_comprobante"."evento_id" = %s
                GROUP BY "gestion_numerorifa"."comprobante_id"
            ) AS subquery
            GROUP BY subquery.compras ORDER BY frequency DESC;
        """,
            [evento_id],
        )
        return cursor.fetchall()


class HasFormValid(Protocol):
    def form_valid(self, form: BaseModelForm) -> HttpResponse: ...


class CacheInvalidationMixin:
    def form_valid(self: HasFormValid, form: BaseModelForm) -> HttpResponse:
        response = super().form_valid(form)
        cache.clear()
        return response


class CachedPaginator(Paginator):
    objects_count = None
    def __init__(
        self, object_list, per_page, cache_key, orphans=0, allow_empty_first_page=True
    ):
        super().__init__(
            object_list,
            per_page,
            orphans=orphans,
            allow_empty_first_page=allow_empty_first_page,
        )
        self.cache_key = cache_key

    @property
    def count(self):
        if self.objects_count is not None:
            return self.objects_count
        if self.cache_key is None:
            count = super().count
            self.objects_count = count
            return self.objects_count
        cached_count = cache.get(self.cache_key)
        if cached_count is None:
            actual_count = super().count
            cache.set(self.cache_key, actual_count)
            self.objects_count = actual_count
            return self.objects_count
        self.objects_count = cached_count
        return self.objects_count


def updateCompraCache(evento_id: str):
    cache_evento = cache.get(f"compras-{evento_id}")
    if cache_evento is not None:
        cache.set(f"compras-{evento_id}", int(cache_evento) + 1)
    cache_evento = cache.get("compras-actual")
    if cache_evento is not None:
        cache.set("compras-actual", int(cache_evento) + 1)
    