from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST

from gestion.models import (
    Cliente,
    Comprobante,
    Evento,
    MetodoPago,
    NumeroRifa,
)
from gestion.utils import calcular_monto

HOURS24 = 60 * 60 * 24


@cache_page(HOURS24)
def home(request: HttpRequest):
    cliente = Cliente.objects.first()
    evento = Evento.obtener_actual()
    eventos = Evento.objects.only(
        "nombre", "fecha_fin", "foto", "url", "total_tickets"
    ).all()
    dolar = 0
    if evento:
        eventos = eventos.exclude(pk=evento.pk)
        dolar = evento.valor_dolar
    metodos = MetodoPago.objects.all().order_by("posicion")
    context = {
        "dolar": dolar,
        "evento": evento,
        "eventos": eventos,
        "cliente": cliente,
        "metodos": metodos,
    }
    if evento:
        if evento.total_tickets <= 200:
            agarrados = NumeroRifa.objects.filter(evento=evento).values_list(
                "numero", flat=True
            )
            total_tickets = evento.total_tickets
            context["agarrados"] = [format(a, evento.digitos) for a in agarrados]
            context["tickets"] = [
                format(t, evento.digitos) for t in range(total_tickets)
            ]
    return render(request, "rifa/home.html", context)


@cache_page(HOURS24)
def detalle_evento(request: HttpRequest, link: str):
    evento = Evento.objects.get(url=link)
    cliente = Cliente.objects.first()
    context = {
        "evento": evento,
        "cliente": cliente,
    }
    if evento.es_actual:
        context["metodos"] = MetodoPago.objects.all().order_by("posicion")
        context["dolar"] = evento.valor_dolar
        if evento.total_tickets <= 200:
            agarrados = NumeroRifa.objects.filter(evento=evento).values_list(
                "numero", flat=True
            )
            context["agarrados"] = [format(a, evento.digitos) for a in agarrados]
            tickets = [format(t, evento.digitos) for t in range(evento.total_tickets)]
            context["tickets"] = tickets
    return render(request, "rifa_detalle/home.html", context)


@require_POST
def verificar(request: HttpRequest):
    celular = request.POST["celular"]
    country_code = request.POST["country_code"]
    evento_id = request.POST["evento_id"]
    if country_code == "+58" and celular.startswith("0"):
        celular = celular[1:]
    telefono = country_code + celular
    evento = Evento.objects.only("total_tickets").get(id=evento_id)
    queryset = Comprobante.objects.filter(
        telefono=telefono, evento_id=evento_id
    ).annotate(
        numeros=ArrayAgg(
            "numerorifa__numero", default=[], filter=~Q(numerorifa__numero__isnull=True)
        )
    )
    comprobantes = list(queryset.values())

    for c in comprobantes:
        numeros = c["numeros"]
        c["boletos"] = [format(n, evento.digitos) for n in numeros]
        c["fecha"] = c["fecha"].strftime("%Y-%m-%d %I:%M %p")
    return JsonResponse({"result": comprobantes})


@cache_page(HOURS24)
def obtener_dolar(request):
    evento = Evento.obtener_actual(fields=["valor_dolar"])
    if evento is None:
        dolar = 0
    else:
        dolar = evento.valor_dolar
    return JsonResponse({"dolar": dolar})


@cache_page(HOURS24)
def obtener_promociones(request):
    evento = Evento.obtener_actual(fields=["id"])
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
    evento = Evento.obtener_actual(fields=["id", "valor_dolar", "total_tickets"])
    if evento is None:
        return JsonResponse({"error": "No hay ninguna rifa disponible"})
    nombre = request.POST["nombre"].upper().strip()
    country_code = request.POST["country_code"]
    celular = request.POST["celular"].replace(" ", "")
    foto = request.FILES["foto"]
    boletos = set(request.POST.getlist("boletos"))
    metodo = request.POST["metodo"]
    cantidad_tickets = request.POST["productQty"]
    referencia = request.POST["referencia"]
    if country_code == "+58" and celular.startswith("0"):
        celular = celular[1:]
    telefono = country_code + celular
    dolar = evento.valor_dolar
    if evento.total_tickets > 200:
        tickets = NumeroRifa.get_random_nums(evento, int(cantidad_tickets))
        if tickets is None:
            error_msg = "No hay boletos suficientes para vender"
            return JsonResponse({"error": error_msg})
        boletos = tickets
    monto = calcular_monto(evento, len(boletos))
    comprobante = Comprobante.objects.create(
        nombre=nombre,
        telefono=telefono,
        foto=foto,
        metodo_id=metodo,
        dolar=dolar,
        evento=evento,
        referencia=referencia,
        monto=monto,
    )
    if evento.total_tickets <= 200:
        numeros_tomados = list(
            NumeroRifa.objects.filter(evento=evento).values_list("numero", flat=True)
        )
        error_msg = "Ya el boleto ha sido comprado por alguien más, escoja otro número"
        if set(boletos) & set(numeros_tomados):
            return JsonResponse({"error": error_msg})
    numeros_comprados = []
    for boleto in boletos:
        numeroRifa = NumeroRifa(numero=boleto, comprobante=comprobante, evento=evento)
        numeros_comprados.append(numeroRifa)
    NumeroRifa.objects.bulk_create(numeros_comprados)
    boletos = [format(int(boleto), evento.digitos) for boleto in boletos]
    return JsonResponse({"ok": "ok", "boletos": list(boletos)})
