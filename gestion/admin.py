from django.contrib import admin
from .models import NumeroRifa,Comprobante,Evento
# Register your models here.

@admin.register(Comprobante)
class ComprobanteAdmin(admin.ModelAdmin):
    list_filter = ["fecha"]

admin.site.register(NumeroRifa)
admin.site.register(Evento)
