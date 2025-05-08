from django.db import models
from django.utils import timezone
import pytz


class Dolar(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True)
    valor_bs = models.FloatField()

    @classmethod
    def obtener_dolar(self):
        ultimo = self.objects.last()
        if not ultimo:
            return self.actualizar()
        # Hacemos los cálculos en horario Venezolano
        vnzla_tz = pytz.timezone("America/Caracas")
        ultima_fecha = ultimo.fecha_hora.astimezone(vnzla_tz)
        hoy = timezone.now().astimezone(vnzla_tz)
        # Dolar actualizado 9:40AM - Hora Venezuela
        corte_1 = hoy.replace(hour=9, minute=40)
        # Dolar actualizado 1:40PM - Hora Venezuela
        corte_2 = hoy.replace(hour=13, minute=40)
        print("Dolar actualizado", corte_2)
        if ultima_fecha < corte_1 and hoy > corte_1:
            return self.actualizar()
        if ultima_fecha < corte_2 and hoy > corte_2:
            return self.actualizar()
        return ultimo.valor_bs

    @classmethod
    def actualizar(self):
        from pyDolarVenezuela.pages import AlCambio
        from pyDolarVenezuela import Monitor

        monitor = Monitor(AlCambio, "USD")
        paralelo = monitor.get_value_monitors("enparalelovzla")
        precio = paralelo.price
        self.objects.create(fecha_hora=timezone.now(), valor_bs=precio)
        return precio

    def __str__(self):
        return str(self.valor_bs)
