from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractUser 
from django.utils import timezone
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
    def obtener_actual(cls):
        hoy = timezone.now()
        return Evento.objects.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy).first()

    @property
    def vendidos(self):
        return NumeroRifa.objects.filter(comprobante__evento=self).count()
    
    @property
    def digitos(self):
        return "0" + str(len(str(self.total_tickets - 1))) + "d"

    def __str__(self):
        return self.nombre


# Create your models here.
class Comprobante(models.Model):
    nombre = models.CharField(max_length=500)
    apellido = models.CharField(max_length=500)
    telefono = models.CharField(max_length=500)
    referencia = models.CharField(
    max_length=500, 
    unique=True,  # Asegura que cada referencia sea única
    verbose_name='Referencia Bancaria',
    help_text='Ingrese el número de referencia del comprobante de pago',
    null=False,  # No permite valores nulos
    blank=False  # No permite campos en blanco
)
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
    evento = models.ForeignKey(Evento, models.RESTRICT, null=False)
    monto = models.FloatField(default=0)

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

class Clientes(models.Model):
    foto = models.ImageField(upload_to='clientes_fotos/', null=True, blank=True)
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=255)
                                 
class Compras(models.Model):
    # Relates to a participant, assuming you have a 'Participante' model
    participante = models.ForeignKey(
        'Participante', # Replace 'Participante' with the actual name of your participant model
        on_delete=models.CASCADE,
        related_name='compras'
    )
    fecha = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('completado', 'Completado'),
            ('cancelado', 'Cancelado'),
        ],
        default='pendiente',
    )
    cuenta = models.CharField(max_length=100) # Or ForeignKey if 'cuenta' refers to another model
    monto = models.DecimalField(max_digits=10, decimal_places=2) # For monetary values
    numeros = models.CharField(max_length=255, blank=True, null=True) # Could be a list of numbers, or a ManyToManyField if linked to a 'Numero' model
    extras = models.TextField(blank=True, null=True) # For additional, potentially longer text
    notas = models.TextField(blank=True, null=True) # For general notes about the purchase 

 class Panel(models.Model):
    # Overall statistics
    total_participantes = models.IntegerField(
        default=0,
        help_text="Número total de participantes registrados."
    )
    total_tickets_registrados = models.IntegerField(
        default=0,
        help_text="Número total de tickets registrados en todas las compras."
    )
    total_por_confirmar = models.IntegerField(
        default=0,
        help_text="Número total de compras/pagos pendientes de confirmación."
    )
    total_confirmados = models.IntegerField(
        default=0,
        help_text="Número total de compras/pagos confirmados."
    )

    # Detailed data (often stored as JSON or text due to variable structure)
    tickets_registrados = models.JSONField(
        blank=True,
        null=True,
        help_text="Detalle de tickets registrados (e.g., por tipo, por rango)."
    )
    participantes_y_compras = models.JSONField(
        blank=True,
        null=True,
        help_text="Relación detallada de participantes y sus compras."
    )
    pagos_por_confirmar = models.JSONField(
        blank=True,
        null=True,
        help_text="Detalle de pagos que requieren confirmación."
    )
    pagos_confirmados = models.JSONField(
        blank=True,
        null=True,
        help_text="Detalle de pagos ya confirmados."
    )
    medios_de_pago = models.JSONField(
        blank=True,
        null=True,
        help_text="Estadísticas de medios de pago utilizados (e.g., Tasa, Zelle)."
    )
    status_de_las_compras = models.JSONField(
        blank=True,
        null=True,
        help_text="Conteo o desglose del estado de las compras (pendientes, completadas, etc.)."
    )
    participantes_mas_tickets = models.JSONField(
        blank=True,
        null=True,
        help_text="Top participantes con más tickets o compras."
    )
    dias_con_mas_ventas = models.JSONField(
        blank=True,
        null=True,
        help_text="Días con el mayor volumen de ventas o registros."
    )
    numeros_de_tickets_frecuentes = models.JSONField(
        blank=True,
        null=True,
        help_text="Análisis de patrones o números de tickets más frecuentes."
    )

    # You might want to add a field to track when this panel data was last updated
    ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última actualización de los datos del panel."
    )   

  class Pagos(models.Model):
    # Choices for the 'tipo' field
    TIPO_PAGO_CHOICES = [
        ('BANCO', 'Transferencia Bancaria'),
        ('PAGO_MOVIL', 'Pago Móvil'),
        ('ZELLE', 'Zelle'),
        ('OTRO', 'Otro'),
    ]

    foto = models.ImageField(
        upload_to='pagos_fotos/',
        null=True,
        blank=True,
        help_text="Imagen del método de pago (ej. logo del banco, QR)."
    )
    banco = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre del banco asociado a la cuenta."
    )
    alias = models.CharField(
        max_length=50,
        unique=True, # Ensure aliases are unique
        help_text="Un alias o nombre corto para identificar este método de pago."
    )
    titular = models.CharField(
        max_length=150,
        blank=True,
        help_text="Nombre del titular de la cuenta o método de pago."
    )
    icono = models.CharField(
        max_length=50,
        blank=True,
        help_text="Clase de icono (ej. FontAwesome) o URL a un icono pequeño."
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_PAGO_CHOICES,
        default='OTRO',
        help_text="Tipo de método de pago (Banco, Pago Móvil, Zelle, etc.)."
    )
    contenido = models.TextField(
        blank=True,
        help_text="Detalles específicos de la cuenta/método (ej. número de cuenta, CI, teléfono)."
    )
    visible = models.BooleanField(
        default=True,
        help_text="Indica si este método de pago debe ser visible públicamente."
    )

 class Participantes(models.Model):
    # Fields for general participant details
    nombre = models.CharField(
        max_length=150,
        help_text="Nombre completo del participante."
    )
    celular = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Número de celular del participante."
    )
    email = models.EmailField(
        unique=True, # Ensure email is unique for each participant
        blank=True,
        null=True,
        help_text="Dirección de correo electrónico del participante."
    )
    ubicacion = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ubicación general (ej. ciudad, estado)."
    )
    direccion = models.TextField(
        blank=True,
        help_text="Dirección detallada del participante."
    )
    campo_extra = models.TextField(
        blank=True,
        help_text="Campo extra para información adicional no estructurada."
    )

    vendedor = models.ForeignKey(
        'Vendedor', # Replace 'Vendedor' with your actual Vendedor model name if different
        on_delete=models.SET_NULL, # Or models.CASCADE, models.PROTECT depending on desired behavior
        null=True,
        blank=True,
        related_name='participantes_referidos',
        help_text="Vendedor que refirió o gestionó a este participante."
    )

    pagototal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Monto total pagado por el participante (acumulado)."
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Monto total de tickets/compras asociadas al participante (acumulado)."
    )

 
class Premios(models.Model):
    # These fields appear to be counters or status indicators.
    # They will likely be populated programmatically or via aggregation.
    todos = models.IntegerField(
        default=0,
        help_text="Número total de todos los premios disponibles."
    )
    rifa_activa = models.IntegerField(
        default=0,
        help_text="Número de premios asociados a rifas activas."
    )
    rifa_inactiva = models.IntegerField(
        default=0,
        help_text="Número de premios asociados a rifas inactivas."
    )
    no_premios = models.IntegerField(
        default=0,
        help_text="Contador para alguna categoría de 'no premios' o categorías especiales."
    )

    # You might want to add a field to track when this prize data was last updated
    ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última actualización de los datos de premios."
    )     

  class Rifas(models.Model):
    foto = models.ImageField(
        upload_to='rifas_fotos/',
        null=True,
        blank=True,
        help_text="Imagen representativa de la rifa."
    )
    nombre = models.CharField(
        max_length=200,
        help_text="Nombre o título de la rifa."
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio por ticket o participación."
    )
    fecha = models.DateField(
        default=timezone.now, # Sets the current date as default
        help_text="Fecha de inicio o de sorteo de la rifa."
    )
    tickets = models.IntegerField(
        help_text="Cantidad total de tickets disponibles para la rifa."
    )
    cantidad_online = models.IntegerField(
        default=0,
        help_text="Cantidad de tickets disponibles para venta online."
    )
    oportun = models.CharField( # This field name is a bit ambiguous, assuming a string for 'opportunity' type
        max_length=100,
        blank=True,
        help_text="Tipo de oportunidad o característica especial de la rifa."
    )
    vendido = models.IntegerField(
        default=0,
        help_text="Número de tickets vendidos hasta la fecha."
    )
    listado = models.TextField(
        blank=True,
        help_text="Descripción o listado de premios asociados a la rifa."
    )

    activo = models.BooleanField(
        default=True,
        help_text="Indica si la rifa está activa y disponible para venta."
    )

    total_participantes = models.IntegerField(
        default=0,
        help_text="Número total de participantes en esta rifa."
    )  

class User(AbstractUser): # Inherit from AbstractUser for full user features
    # If you choose not to inherit from AbstractUser, you'd define 'username', 'password', etc.
    # But inheriting is usually best practice.

    # User's full name
    nombre = models.CharField(
        max_length=150,
        blank=True, # Allow blank name if not required
        verbose_name="Nombre Completo",
        help_text="Nombre completo del usuario."
    )
    CARGO_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('SUPERVISOR', 'Supervisor'),
        ('VENDEDOR', 'Vendedor'),
        ('CLIENTE', 'Cliente'),
        ('OTRO', 'Otro'),
    ]
    cargo = models.CharField(
        max_length=20,
        choices=CARGO_CHOICES,
        default='CLIENTE',
        help_text="Cargo o posición del usuario dentro del sistema."
    )

    # User's phone number
    celular = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Número de Celular",
        help_text="Número de teléfono celular del usuario."
    )

    ROL_CHOICES = [
        ('FULL_ACCESS', 'Acceso Total'),
        ('LIMITED_ACCESS', 'Acceso Limitado'),
        ('VIEW_ONLY', 'Solo Lectura'),
    ]
    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default='LIMITED_ACCESS',
        help_text="Rol de acceso y permisos del usuario."
    )

