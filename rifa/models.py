import logging

import pytz
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class Dolar(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True)
    valor_bs = models.FloatField()

    @classmethod
    def obtener_dolar(cls):
        ultimo = cls.objects.last()
        if not ultimo:
            ultimo = cls.actualizar()
            return round(ultimo.valor_bs, 2)
        # Hacemos los cálculos en horario Venezolano
        vnzla_tz = pytz.timezone("America/Caracas")
        ultima_fecha = ultimo.fecha_hora.astimezone(vnzla_tz)
        hoy = timezone.now().astimezone(vnzla_tz)
        # Dolar actualizado 9:40AM - Hora Venezuela
        corte_1 = hoy.replace(hour=9, minute=40)
        # Dolar actualizado 1:40PM - Hora Venezuela
        corte_2 = hoy.replace(hour=13, minute=40)
        if ultima_fecha < corte_1 and hoy > corte_1:
            try:
                ultimo = cls.actualizar()
            except Exception:
                logger.warning("No se pudo actualizar el dolar")
        if ultima_fecha < corte_2 and hoy > corte_2:
            try:
                ultimo = cls.actualizar()
            except Exception:
                logger.warning("No se pudo actualizar el dolar")
        return round(ultimo.valor_bs, 2)

    @classmethod
    def dolar_actual(cls):
        cls.obtener_dolar()
        return cls.objects.last()

    @classmethod
    def actualizar(cls):
        from pyBCV import Currency

        currency = Currency()
        precio = currency.get_rate("EUR")
        if isinstance(precio, str):
            precio = round(float(precio), 2)
            dolar = cls.objects.create(fecha_hora=timezone.now(), valor_bs=precio)
            return dolar
        raise ValueError("Error al obtener el dolar")

    def __str__(self):
        return str(self.valor_bs)
