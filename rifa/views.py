from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from gestion.models import (
    Cliente,
    Comprobante,
    Evento,
    MetodoPago,
    NumeroRifa,
    Visualizacion,
)
from gestion.utils import calcular_monto


def home(request: HttpRequest):
    cliente = Cliente.objects.first()
    evento = Evento.obtener_actual()
    eventos = Evento.objects.only("nombre", "fecha_fin", "foto", "url").all()
    Visualizacion.objects.create(evento=evento)
    agarrados = NumeroRifa.objects.filter(comprobante__evento=evento).prefetch_related(
        "comprobante__evento"
    )
    if evento:
        agarrados = [str(a) for a in agarrados]
        eventos = eventos.exclude(pk=evento.pk)
    tickets = []
    if evento:
        total_tickets = evento.total_tickets
        tickets = [format(t, evento.digitos) for t in range(total_tickets)]
    dolar = evento.valor_dolar if evento else 0
    metodos = MetodoPago.objects.all()
    context = {
        "agarrados": agarrados,
        "tickets": tickets,
        "dolar": dolar,
        "evento": evento,
        "eventos": eventos,
        "cliente": cliente,
        "metodos": metodos,
    }
    return render(request, "rifa/home.html", context)


def detalle_evento(request: HttpRequest, link: str):
    evento = Evento.objects.get(url=link)
    cliente = Cliente.objects.first()
    context = {
        "evento": evento,
        "cliente": cliente,
    }
    return render(request, "rifa_detalle/home.html", context)


@require_POST
def verificar(request: HttpRequest):
    celular = request.POST["celular"]
    country_code = request.POST["country_code"]
    evento_id = request.POST["evento_id"]
    if country_code == "+58" and celular.startswith("0"):
        celular = celular[1:]
    telefono = country_code + celular
    queryset = Comprobante.objects.filter(telefono=telefono, evento_id=evento_id)
    comprobantes = list(queryset.values())
    for c in comprobantes:
        numeros = NumeroRifa.objects.filter(comprobante=c["id"]).prefetch_related(
            "comprobante__evento"
        )
        c["boletos"] = [str(n) for n in numeros]
    return JsonResponse({"result": comprobantes})


@require_POST
def obtener_dolar(request):
    evento = Evento.obtener_actual()
    if evento is None:
        dolar = 0
    else:
        dolar = evento.valor_dolar
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
    nombre = request.POST["nombre"].upper()
    country_code = request.POST["country_code"]
    celular = request.POST["celular"].replace(" ", "")
    foto = request.FILES["foto"]
    boletos = set(request.POST.getlist("boletos"))
    metodo = request.POST["metodo"]
    cantidad_tickets = request.POST["productQty"]
    referencia = request.POST["referencia"]
    if referencia:
        if Comprobante.objects.filter(referencia=referencia).exists():
            return JsonResponse({"error": "Ya existe un comprobante con esa referencia"})
    if country_code == "+58" and celular.startswith("0"):
        celular = celular[1:]
    telefono = country_code + celular
    dolar = evento.valor_dolar
    comprobante = Comprobante.objects.create(
        nombre=nombre,
        telefono=telefono,
        foto=foto,
        metodo_id=metodo,
        dolar=dolar,
        evento=evento,
        referencia=referencia,
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
    return JsonResponse({"ok": "ok", "boletos": list(boletos)})
