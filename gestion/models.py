import random
from typing import List, Optional
from urllib.parse import quote_plus

from django.db import models
from django.http import HttpRequest
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


class MonedasChoices(models.TextChoices):
    DOLAR = "$"
    EURO = "€"
    BOLIVAR = "Bs"


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

    class Meta:
        indexes = [
            models.Index(
                fields=["fecha_inicio", "fecha_fin"], name="evento_fechas_idx"
            ),
        ]

    @property
    def promociones(self):
        return Promocion.objects.filter(evento=self)

    @classmethod
    def obtener_actual(
        cls, evento_id: Optional[str] = None, fields: Optional[List[str]] = None
    ):
        evento = Evento.objects.all()
        if fields:
            evento = evento.only(*fields)
        if evento_id:
            instance = evento.get(id=evento_id)
        else:
            hoy = timezone.now()
            instance = evento.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy).first()
        return instance

    @property
    def es_actual(self):
        hoy = timezone.now()
        return bool(self.fecha_inicio <= hoy and self.fecha_fin >= hoy)

    @property
    def vendidos(self):
        return NumeroRifa.objects.filter(evento=self).count()

    @property
    def digitos(self):
        return "0" + str(len(str(self.total_tickets - 1))) + "d"

    @property
    def disponibles(self):
        return self.total_tickets - self.vendidos

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
    moneda = models.CharField(max_length=10, choices=MonedasChoices.choices)

    class Meta:
        indexes = [
            models.Index(fields=["posicion"], name="metodopago_posicion_idx"),
        ]

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
    referencia = models.CharField(max_length=100, blank=True)
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

    def get_full_url(self, request: HttpRequest):
        evento_url = self.evento.url
        telefono_url = self.telefono.replace("+", "%2B")
        return request.build_absolute_uri(f"/rifa/{evento_url}/?phone={telefono_url}")

    def __str__(self):
        return self.nombre

    @property
    def whatsapp_url(self):
        telefono = quote_plus(self.telefono)
        nombre = quote_plus(self.nombre)
        evento = quote_plus(self.evento.nombre)
        url = quote_plus(self.evento.url)
        if self.verificado:
            return f"https://api.whatsapp.com/send?phone=\
            {telefono}&amp;text=Hola+{nombre}+%2C+tus+boletos\
            +han+sido+verificados+con+tus+n%C3%BAmeros+elegidos+en+\
            {evento}%2C+puedes+consultar+tus+numeros+en+el+siguiente+enlace.\
            +https%3A%2F%2Fwww.chipibikelifee.com%2Frifa%2F{url}%3Fphone%3D\
            {telefono}"
        else:
            return f"https://api.whatsapp.com/send?phone=\
            {telefono}&amp;text=Hola+{nombre}+%2C+no+pierdas\
            +tu+oportunidad+de+ganar+con+tus+n%C3%BAmeros+elegidos+en+\
            {evento}%2C+completa+el+pago+por+favor%2C+no+dejes+ir+tu+suerte.\
            +https%3A%2F%2Fwww.chipibikelifee.com%2Frifa%2F{url}%3Fphone%3D\
            {telefono}"

    class Meta:
        indexes = [
            models.Index(fields=["telefono"]),
        ]


class NumeroRifa(models.Model):
    comprobante_id: int
    numero = models.IntegerField()
    evento = models.ForeignKey(Evento, models.RESTRICT)
    comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE)

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

    @classmethod
    def get_random_nums(cls, evento: Evento, cantidad: int):
        agarrados = set(
            NumeroRifa.objects.filter(evento=evento).values_list("numero", flat=True)
        )
        if len(agarrados) + cantidad > evento.total_tickets:
            return None
        porc = (len(agarrados) + cantidad) / evento.total_tickets
        if porc > 0.9:
            disponibles = set(range(evento.total_tickets)) - agarrados
            return random.sample(list(disponibles), cantidad)
        seleccionados: set[int] = set()
        while True:
            numero = random.randint(0, evento.total_tickets - 1)
            if numero not in agarrados and numero not in seleccionados:
                seleccionados.add(numero)
            if len(seleccionados) >= cantidad:
                break
        return list(seleccionados)


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
