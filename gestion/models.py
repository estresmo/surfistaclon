import random
from typing import Optional

from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class StatusChoices(models.TextChoices):
    NO_VERIFICADO = "No verificado"
    VERIFICADO = "Verificado"
    RECHAZADO = "Rechazado"


class MetodosChoices(models.IntegerChoices):
    BANCOLOMBIA = 1
    PAGO_MOVIL = 2
    BINANCE = 3


class Evento(models.Model):
    nombre = models.CharField(max_length=500, unique=True)
    url = models.CharField(max_length=500, unique=True)
    descripcion = models.TextField()
    precio_unidad = models.FloatField()
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    direccion = models.CharField(max_length=500)
    foto = models.ImageField(upload_to="eventos/")
    total_tickets = models.IntegerField()
    minimo = models.IntegerField(default=0)
    valor_dolar = models.FloatField()
    color_principal = models.CharField(max_length=50)
    color_secundario = models.CharField(max_length=50)
    color_oscuro = models.CharField(max_length=50)
    color_texto = models.CharField(max_length=50)
    color_hover = models.CharField(max_length=50)
    color_fondo = models.CharField(max_length=50)
    color_header = models.CharField(max_length=50)
    hora_espera = models.CharField(max_length=50)
    eliminar_tickets = models.BooleanField()
    mostrar_ocupados = models.BooleanField()
    permitir_eleccion = models.BooleanField()
    permitir_parcial = models.BooleanField()
    permitir_sin_comprobante = models.BooleanField()

    @property
    def promociones(self):
        return Promocion.objects.filter(evento=self)

    @classmethod
    def obtener_actual(cls, evento_id: Optional[str] = None):
        if evento_id is not None:
            return Evento.objects.get(id=evento_id)
        hoy = timezone.now()
        return Evento.objects.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy).first()

    @property
    def es_actual(self):
        hoy = timezone.now()
        return bool(self.fecha_inicio <= hoy and self.fecha_fin >= hoy)

    @property
    def vendidos(self):
        return NumeroRifa.objects.filter(comprobante__evento=self).count()

    @property
    def digitos(self):
        return "0" + str(len(str(self.total_tickets - 1))) + "d"

    def __str__(self):
        return self.nombre


class MetodoPago(models.Model):
    banco = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to="metodos/")
    titular = models.CharField(max_length=300)
    posicion = models.IntegerField()
    activo = models.BooleanField()
    fecha_creado = models.DateField(auto_now_add=True)
    fecha_editado = models.DateField(auto_now=True)
    titulo_1 = models.CharField(max_length=100, blank=True)
    contenido_1 = models.CharField(max_length=100, blank=True)
    titulo_2 = models.CharField(max_length=100, blank=True)
    contenido_2 = models.CharField(max_length=100, blank=True)
    titulo_3 = models.CharField(max_length=100, blank=True)
    contenido_3 = models.CharField(max_length=100, blank=True)
    nota = models.CharField(max_length=100, blank=True)

    @property
    def contenidos(self):
        return [
            (self.titulo_1, self.contenido_1),
            (self.titulo_2, self.contenido_2),
            (self.titulo_3, self.contenido_3),
        ]

    @property
    def mostrar_contenido(self):
        contenidos = (
            self.titulo_1,
            self.contenido_1,
            self.titulo_2,
            self.contenido_2,
            self.titulo_3,
            self.contenido_3,
        )
        con_contenido: list[str] = []
        for c in contenidos:
            if c:
                con_contenido.append(c)
        return con_contenido

    def __str__(self):
        return self.banco


# Create your models here.
class Comprobante(models.Model):
    nombre = models.CharField(max_length=500)
    telefono = models.CharField(max_length=500)
    referencia = models.CharField(max_length=100, blank=True, unique=True)
    fecha = models.DateTimeField(default=timezone.now)
    foto = models.ImageField(upload_to="comprobantes/")
    status = models.CharField(
        max_length=500,
        choices=StatusChoices.choices,
        default=StatusChoices.NO_VERIFICADO,
    )
    metodo = models.ForeignKey(MetodoPago, models.RESTRICT, null=True)
    dolar = models.FloatField(default=0, blank=True)
    historial = HistoricalRecords()
    evento = models.ForeignKey(Evento, models.RESTRICT, null=False)
    monto = models.FloatField(default=0)
    fecha_verificacion = models.DateTimeField(null=True, blank=True)
    nota = models.TextField(null=True, blank=True)
    fecha_creado = models.DateField(auto_now_add=True)

    @property
    def boletos(self):
        return NumeroRifa.objects.filter(comprobante=self)

    @property
    def verificado(self):
        return self.status == StatusChoices.VERIFICADO

    def __str__(self):
        return self.nombre


class NumeroRifa(models.Model):
    numero = models.IntegerField()
    evento = models.ForeignKey(Evento, models.RESTRICT, null=True)
    comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["numero"]),
        ]

    def __str__(self):
        digitos = ""
        if self.comprobante:
            if self.comprobante.evento:
                digitos = self.comprobante.evento.digitos
        return format(self.numero, digitos)

    @classmethod
    def obtener_random(cls, evento: Evento):
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
        nombre = "Ninguno"
        if self.evento:
            nombre = self.evento.nombre
        return f"Visualización de {nombre} en {self.fecha}"


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    telefono = models.CharField(max_length=500)
    logo = models.ImageField(upload_to="cliente/")
    ubicacion = models.CharField(max_length=255)
    portada = models.ImageField(upload_to="cliente/")
    tiktok = models.CharField(max_length=500, blank=True)
    facebook = models.CharField(max_length=500, blank=True)
    twitter = models.CharField(max_length=500, blank=True)
    youtube = models.CharField(max_length=500, blank=True)
    instagram = models.CharField(max_length=500, blank=True)
    linkedin = models.CharField(max_length=500, blank=True)
