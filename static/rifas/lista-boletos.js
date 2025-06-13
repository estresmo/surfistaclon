const ticketQty = document.querySelector("#ticketQty");
const btnMinus = document.querySelector("#btnMinus");
let tickets_seleccionados = [];
const minimo = parseInt(document.getElementById("minimo-tickets-js").value);
let promociones = [];
const precio_unidad = parseFloat(
  document.getElementById("precio-unidad-js").value
);

function obtenerPromociones() {
  fetch("/obtener_promociones/")
    .then((response) => response.json())
    .then((data) => {
      promociones = data.promociones;
      actualizarPrecios();
    });
}
obtenerPromociones();

function addTicket() {
  const ticketQty = document.querySelector("#ticketQty");
  /* @type {HTMLInputElement} */
  ticketQty.value = parseInt(ticketQty.value) + 1;
  actualizarPrecios();
}

function removeTicket() {
  const ticketQty = document.querySelector("#ticketQty");
  /* @type {HTMLInputElement} */
  ticketQty.value = parseInt(ticketQty.value) - 1;
  actualizarPrecios();
}

function actualizarPrecios() {
  const ticketQty = document.querySelector("#ticketQty");
  const btnMinus = document.querySelector("#btnMinus");
  const minimo = parseInt(document.getElementById("minimo-tickets-js").value);
  if (ticketQty.value > minimo) {
    btnMinus.disabled = false;
  } else {
    btnMinus.disabled = true;
  }
  document.querySelectorAll(".cantidad-boleto").forEach((elem) => {
    elem.innerHTML = ticketQty.value;
  });
  document.querySelectorAll(".total-boleto").forEach((elem) => {
    elem.innerHTML = calcularPrecio(ticketQty.value) + "$";
  });
  document.querySelectorAll(".total-boleto-euro").forEach((elem) => {
    elem.innerHTML = calcularPrecio(ticketQty.value) + "€";
  });

  actualizarBs(ticketQty.value);
}

function calcularPrecio(boletos, index = promociones.length - 1, total = 0) {
  const precio_unidad = parseFloat(
    document.getElementById("precio-unidad-js").value
  );
  if (index < 0) {
    return total + boletos * precio_unidad;
  }
  const promocion = promociones[index];
  if (promocion.cantidad_tickets <= boletos) {
    boletos -= promocion.cantidad_tickets;
    total += promocion.precio;
  } else if (index > 0) {
    index -= 1;
  } else {
    total += boletos * precio_unidad;
    boletos = 0;
  }

  if (boletos == 0) {
    return total;
  } else {
    return calcularPrecio(boletos, index, total);
  }
}

let dolar;
async function obtenerDolar() {
  const crsf_token = document.querySelector("[name=csrfmiddlewaretoken]").value;
  const ticketQty = document.querySelector("#ticketQty");
  const response = await fetch("/obtener_dolar/", {
    method: "POST",
    headers: {
      "X-CSRFToken": crsf_token,
    },
  });
  const data = await response.json();
  dolar = data.dolar;
  let total = dolar * calcularPrecio(ticketQty.value);
  total = total.toFixed(2);
  document
    .querySelectorAll(".precio-bs")
    .forEach((element) => (element.innerHTML = total + "bs"));
  actualizarPrecios();
}

function actualizarBs(cantidad) {
  const dolares = calcularPrecio(cantidad);
  const calculo = parseFloat(dolar * dolares, 2).toFixed(2);
  document
    .querySelectorAll(".precio-bs")
    .forEach((element) => (element.innerHTML = calculo + "bs"));
}
obtenerDolar();

// Métodos de pago

function cambiarPago(elemento) {
  document
    .querySelector(".type.option-payment.selected")
    .classList.remove("selected");
  elemento.classList.add("selected");
  if (elemento.dataset.id != 6) {
    document.querySelector("#referencia-div").style.display = "none";
    document.querySelector("#referencia").required = false;
  } else {
    document.querySelector("#referencia-div").style.display = "block";
    document.querySelector("#referencia").required = true;
  }
}
document.querySelectorAll(".type.option-payment").forEach(function (elemento) {
  elemento.onclick = function () {
    cambiarPago(elemento);
    document.querySelector("#metodo-value").value = elemento.dataset.id;
    document.querySelector("#metodo-titulo").innerHTML =
      elemento.querySelector(".text").innerHTML;
    document.querySelector("#contenido-pago").innerHTML =
      elemento.querySelector(".content").innerHTML;
  };
});

/** @param {HTMLButtonElement} btn */
function seleccionarTicket(btn) {
  let ticket = btn.dataset.ticket;
  const ticketQty = document.querySelector("#ticketQty");
  if (tickets_seleccionados.includes(ticket)) {
    btn.classList.remove("seleccionado");
    tickets_seleccionados = tickets_seleccionados.filter(
      (item) => item !== ticket
    );
  } else {
    if (tickets_seleccionados.length < parseInt(ticketQty.value)) {
      btn.classList.add("seleccionado");
      tickets_seleccionados.push(ticket);
    }
  }
  document.querySelector(".cantidad-seleccionado").innerHTML =
    tickets_seleccionados.length;
}

function randomTickets() {
  const old_selected = document.querySelectorAll(".ticket-opcion.seleccionado");
  const ticketQty = document.querySelector("#ticketQty");
  old_selected.forEach((ticket) => {
    ticket.classList.remove("seleccionado");
  });
  const disponibles = Array.from(
    document.querySelectorAll(".ticket-opcion:not([disabled])")
  );
  const tickets_disponibles = disponibles.map(
    (ticket) => ticket.dataset.ticket
  );

  tickets_seleccionados = [];
  for (let i = 0; i < ticketQty.value; i++) {
    while (true) {
      const num = get_random(tickets_disponibles);
      if (!tickets_seleccionados.includes(num)) {
        tickets_seleccionados.push(num);
        document
          .querySelector(`[data-ticket="${num}"]`)
          .classList.add("seleccionado");
        break;
      }
    }
  }
  document.querySelector(".cantidad-seleccionado").innerHTML =
    tickets_seleccionados.length;
}

/** @param {Array} list */
function get_random(list) {
  return list[Math.floor(Math.random() * list.length)];
}

/**
 * @param {HTMLFormElement} form
 * @param {SubmitEvent} event
 */
async function confirmarTickets(form, event) {
  event.preventDefault();
  const formData = new FormData(form);
  const btnConfirm = document.getElementById("confirmTickets");
  const ticketQty = document.querySelector("#ticketQty");
  btnConfirm.disabled = true;
  btnConfirm.innerText = "Cargando....";
  const total_tickets = parseInt(
    document.getElementById("total_tickets").value
  );

  if (tickets_seleccionados.length < ticketQty.value && total_tickets < 201) {
    alert("Debes seleccionar los boletos que quieres comprar");
    return;
  }
  tickets_seleccionados.forEach((ticket) => {
    formData.append("boletos", ticket);
  });

  const response = await fetch("/comprobantes/", {
    method: "POST",
    body: formData,
  });
  if (response.ok) {
    const result = await response.json();
    if (result.error) {
      alert(result.error);
      return;
    }
    const txt = getWhatsappText(result.boletos);
    const url = "https://wa.me/584242558344?text=" + txt;
    document.getElementById("whatsapp-link").href = url;
    document.getElementById("countdown").innerText = "5";
    whatsappTimer(url, 5);
    const modal = new bootstrap.Modal(
      document.getElementById("confirmationModal"),
      {}
    );

    modal.show();
    form.reset();
  } else if (response.status == 403) {
    alert("Error al ordenar los boletos. Por favor intente nuevamente");
    location.reload();
  } else {
    alert("Error al ordenar los boletos. Por favor intente nuevamente");
    location.reload();
  }

  btnConfirm.disabled = false;
  btnConfirm.innerText = "Confirmar";
}

function whatsappTimer(url, countdown) {
  setTimeout(() => {
    let seconds = countdown - 1;
    document.getElementById("countdown").innerText = seconds;
    if (seconds == 0) {
      location.href = url;
    } else {
      whatsappTimer(url, seconds);
    }
  }, 1000);
}

function getWhatsappText(boletos) {
  const nombre = document.getElementById("nombre").value;
  const celular = document.getElementById("celular").value;
  const cod_t = document.querySelector("#lista_boletos #country_code").value;
  const telefono = cod_t + celular;
  const tickets = boletos.join(", ");
  const rifa = document.getElementById("nombre-rifa").innerText;
  const verificar_url =
    "https://www.chipibikelifee.com/rifa/comboexclusivo/?phone=" +
    telefono.replace("+", "%2B");
  const txt = `Hola, soy ${nombre}. Con mi celular ${telefono} registre estos números ${tickets}. En  ${rifa} ${verificar_url}`;
  return encodeURIComponent(txt);
}

function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        alert("¡Copiado al portapapeles!");
      })
      .catch((err) => {
        console.error("Error al copiar al portapapeles: ", err);
      });
  } else {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand("copy");
    document.body.removeChild(textArea);
    alert("¡Copiado al portapapeles!");
  }
}
/**
 * @param {HTMLElement} copyElement
 * @param {string} id */
async function copiarTodo(copyElement, id) {
  const parentElement = document.querySelector(`[data-id='${id}']`);
  const contenidos = parentElement.querySelectorAll(".metodo-contenido");
  let txt = "";
  contenidos.forEach((element) => {
    txt += element.innerText.replaceAll("\n", "").replaceAll(" ", "") + " ";
  });
  txt += parentElement
    .querySelector(".monto-metodo")
    .innerText.replaceAll(" ", "")
    .relace("Bs", "");
  if (navigator.clipboard && navigator.clipboard.writeText) {
    copyElement.classList.add("copiado");
    navigator.clipboard
      .writeText(txt)
      .then(() => {
        setTimeout(() => {
          copyElement.classList.remove("copiado");
        }, 3000);
      })
      .catch(() => alert("No se puede copiar"));
  } else {
    alert("No se puede copiar");
  }
}
