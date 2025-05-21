from django.shortcuts import render
from django.http import JsonResponse
from .models import Dolar
from django.views.decorators.http import require_POST
from gestion.models import NumeroRifa, Comprobante, Evento, Visualizacion
from django.http import HttpRequest
from gestion.utils import send_whatsapp, calcular_monto
from django.conf import settings


def home(request: HttpRequest):
    evento = Evento.obtener_actual()
    Visualizacion.objects.create(evento=evento)
    agarrados = NumeroRifa.objects.values_list("numero", flat=True)
    total_tickets = 100
    if evento:
        total_tickets = evento.total_tickets
    tickets = list(range(total_tickets))
    dolar = Dolar.obtener_dolar()
    context = {
        "agarrados": agarrados,
        "tickets": tickets,
        "dolar": dolar,
        "evento": evento,
    }
    return render(request, "rifa/home.html", context)


@require_POST
def verificar(request: HttpRequest):
    celular = request.POST["celular"]
    country_code = request.POST["country_code"]
    telefono = country_code + celular
    comprobantes = list(Comprobante.objects.filter(telefono=telefono).values())
    for c in comprobantes:
        numeros = NumeroRifa.objects.filter(comprobante=c["id"]).prefetch_related(
            "comprobante__evento"
        )
        c["boletos"] = [str(n) for n in numeros]
    return JsonResponse({"result": comprobantes})


@require_POST
def obtener_dolar(request):
    dolar = Dolar.obtener_dolar()
    return JsonResponse({"dolar": dolar})


def obtener_promociones(request):
    evento = Evento.obtener_actual()
    if evento is None:
        return JsonResponse({"error": "No hay ninguna rifa disponible"})
    promociones = list(
        evento.promociones.order_by("cantidad_tickets").values(
            "cantidad_tickets", "precio"
        )
    )
    return JsonResponse({"promociones": promociones})


@require_POST
def comprobantes(request: HttpRequest):
    evento = Evento.obtener_actual()
    if evento is None:
        return JsonResponse({"error": "No hay ninguna rifa disponible"})
    nombre = request.POST["nombre"]
    country_code = request.POST["country_code"]
    celular = request.POST["celular"].replace(" ", "")
    if country_code == "+58" and celular.startswith("0"):
        celular = celular[1:]
    telefono = country_code + celular
    foto = request.FILES["foto"]
    boletos = set(request.POST.getlist("boletos"))
    metodo = request.POST["metodo"]
    cantidad_tickets = request.POST["productQty"]
    Dolar.obtener_dolar()
    dolar = Dolar.objects.last()
    comprobante = Comprobante.objects.create(
        nombre=nombre,
        telefono=telefono,
        foto=foto,
        metodo=metodo,
        dolar=dolar,
        evento=evento,
    )
    if evento.total_tickets > 200:
        for _ in range(int(cantidad_tickets)):
            ticket = NumeroRifa.obtener_random(evento)
            while ticket in boletos:
                ticket = NumeroRifa.obtener_random(evento)
            boletos.add(str(ticket))
    numeros_tomados = list(
        NumeroRifa.objects.filter(evento=evento).values_list("numero", flat=True)
    )
    numeros_comprados = []
    error_msg = "Ya el boleto ha sido comprado por alguien más, escoja otro número"
    for boleto in boletos:
        if boleto in numeros_tomados:
            return JsonResponse({"error": error_msg})
        numeroRifa = NumeroRifa(numero=boleto, comprobante=comprobante, evento=evento)
        numeros_comprados.append(numeroRifa)
    NumeroRifa.objects.bulk_create(numeros_comprados)
    comprobante.monto = calcular_monto(comprobante)
    comprobante.save(update_fields=["monto"])
    msg = (
        "Usted ha comprado los tickets: "
        + ", ".join(boletos)
        + ". Se le notificará cuando su pago sea aprobado"
    )
    send_whatsapp(telefono, msg)
    admin_msg = "Ha recibido un nuevo comprobante. \
        Verificar en https://www.mundobikelife-vzla.com/gestion/comprobantes/"
    send_whatsapp(settings.ADMIN_PHONE, admin_msg)
    return JsonResponse({"ok": "ok"})
