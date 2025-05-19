import requests
import re
from typing import TypedDict, cast

from gestion.models import Comprobante, Evento, Promocion
import logging

logger = logging.getLogger(__name__)

WHATSAPP_URL = "http://localhost:5008/send"
WHATSAPP_AUTH = ("user", "secret")


def send_whatsapp(num: str, msg: str):
    number = "".join(re.findall(r"\d+", num))
    try:
        data = {
            "number": number,
            "message": msg,
        }
        r = requests.post(WHATSAPP_URL, auth=WHATSAPP_AUTH, json=data)
        if r.status_code == 503:
            logger.warning("No se pudo mandar el Whatsapp")
    except Exception as e:
        logger.warning("No se pudo mandar el Whatsapp")


class PromocionDict(TypedDict):
    """Representa una promoción de boletos con cantidad y precio en descuento.

    Attributes:
        cantidad_tickets: Número de boletos requeridos para aplicar esta promoción
        precio: Precio total en descuento para esta cantidad de boletos
    """

    cantidad_tickets: int
    precio: int


def calcular_monto(comprobante: Comprobante):
    if comprobante.evento is None:
        raise ValueError("Comprobante necesita estar asociado a un evento")
    evento = Evento.objects.get(pk=comprobante.evento.pk)
    precio_unidad = evento.precio_unidad
    boletos = comprobante.boletos.count()
    promociones = cast(
        list[PromocionDict],
        list(
            Promocion.objects.filter(evento=evento).values("cantidad_tickets", "precio")
        ),
    )
    index = len(promociones) - 1
    total = 0
    return calcular_precio(boletos, precio_unidad, promociones, index, total)


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
