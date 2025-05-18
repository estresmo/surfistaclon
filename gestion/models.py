from django.db import models
from simple_history.models import HistoricalRecords
import random
from rifa.models import Dolar
from django.utils import timezone


class StatusChoices(models.TextChoices):
    NO_VERIFICADO = "No verificado"
    VERIFICADO = "Verificado"
    RECHAZADO = "Rechazado"


class MetodosChoices(models.IntegerChoices):
    BANCOLOMBIA = 1
    PAGO_MOVIL = 2
    BINANCE = 3


class Evento(models.Model):
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    nombre = models.CharField(max_length=500)
    foto = models.ImageField(upload_to="eventos/")
    precio_unidad = models.FloatField()
    total_tickets = models.IntegerField()
    minimo = models.IntegerField(default=0)

    @property
    def promociones(self):
        return Promocion.objects.filter(evento=self)

    @classmethod
    def obtener_actual(self):
        hoy = timezone.now()
        return Evento.objects.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy).first()

    @property
    def vendidos(self):
        return NumeroRifa.objects.filter(comprobante__evento=self).count()

    def __str__(self):
        return self.nombre


# Create your models here.
class Comprobante(models.Model):
    nombre = models.CharField(max_length=500)
    apellido = models.CharField(max_length=500)
    telefono = models.CharField(max_length=500)
    fecha = models.DateField(default=timezone.now)
    foto = models.ImageField()
    status = models.CharField(
        max_length=500,
        choices=StatusChoices.choices,
        default=StatusChoices.NO_VERIFICADO,
    )
    metodo = models.IntegerField(choices=MetodosChoices.choices, null=True)
    dolar = models.ForeignKey(Dolar, on_delete=models.CASCADE, null=True)
    historial = HistoricalRecords()
    evento = models.ForeignKey(Evento, models.RESTRICT, null=True)

    @property
    def boletos(self):
        return NumeroRifa.objects.filter(comprobante=self)

    def __str__(self):
        return self.nombre


class NumeroRifa(models.Model):
    numero = models.IntegerField(unique=True)
    evento = models.ForeignKey(Evento, models.RESTRICT, null=True)
    comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["numero"]),
        ]

    def __str__(self):
        return str(self.numero)

    @classmethod
    def obtener_random(self, evento: Evento):
        agarrados = list(
            NumeroRifa.objects.filter(evento=evento).values_list("numero", flat=True)
        )
        if len(agarrados) == evento.total_tickets:
            return None
        while True:
            numero = random.randint(0, evento.total_tickets - 1)
            if numero not in agarrados:
                return numero


class Promocion(models.Model):
    cantidad_tickets = models.IntegerField()
    precio = models.FloatField()
    evento = models.ForeignKey(Evento, models.RESTRICT)

    def __str__(self):
        if self.precio % 1 == 0:
            return f"{self.cantidad_tickets}x{self.precio:.0f}$"
        else:
            return f"{self.cantidad_tickets}x{self.precio:.2f}$"


class Visualizacion(models.Model):
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="visualizaciones", null=True
    )
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha y hora de la visualización

    def __str__(self):
        return f"Visualización de {self.evento.nombre} en {self.fecha}"
