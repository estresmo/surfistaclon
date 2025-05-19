from django.db import models
from django.utils import timezone
import pytz
import logging

logger = logging.getLogger(__name__)

class Dolar(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True)
    valor_bs = models.FloatField()

    @classmethod
    def obtener_dolar(cls):
        ultimo = cls.objects.last()
        if not ultimo:
            return cls.actualizar()
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
                return cls.actualizar()
            except Exception:
                logger.warning("No se pudo actualizar el dolar")
                return None
        if ultima_fecha < corte_2 and hoy > corte_2:
            try:
                return cls.actualizar()
            except Exception:
                logger.warning("No se pudo actualizar el dolar")
                return None
        return ultimo.valor_bs

    @classmethod
    def actualizar(cls):
        from pyDolarVenezuela.pages import AlCambio
        from pyDolarVenezuela import Monitor

        monitor = Monitor(AlCambio, "USD")
        paralelo = monitor.get_value_monitors("enparalelovzla")
        precio = paralelo.price
        cls.objects.create(fecha_hora=timezone.now(), valor_bs=precio)
        return precio

    def __str__(self):
        return str(self.valor_bs)
