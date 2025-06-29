const tickets_fecha = "{{ tickets_fecha }}".split(",");
const TICKETS_FECHA = tickets_fecha.map((i) => i.split(";"));
const tickets_chart = TICKETS_FECHA.map((i) => [i[0], i[1]]);
const compras_chart = TICKETS_FECHA.map((i) => [i[0], i[3]]);
const buyers_chart = TICKETS_FECHA.map((i) => [i[0], i[3]]);

/**
 * @typedef {Object} fechaTicketsData
 * @property {string[][]} tickets
 *
 * @typedef {Object} fechaComprasData
 * @property {string[][]} compras
 * @property {string[][]} participantes
 *
 * @typedef {Object} metodosData
 * @property {string[][]} aprobados
 * @property {string[][]} por_confirmar
 * @property {string[][]} tickets_metodo
 *
 * @typedef {Object} participantesData
 * @property {string[][]} participantes
 *
 * @typedef {Object} diasVentasData
 * @property {string[][]} dias_ventas
 *
 * @typedef {Object} ticketsFrecuenteData
 * @property {string[][]} tickets_frecuentes
 *  */

/** @param {string} evento_id */
async function fechaComprasChart(evento_id) {
  const response = await fetch(`/admin/stats/${evento_id}/fecha-tickets`);
  /** @type fechaTicketsData */
  const fechaData = await response.json();
  new Chartkick["AreaChart"]("tickets_fecha_chart", fechaData.tickets, {
    colors: ["#4f1616", "#5ea3d3"],
  });
}

/** @param {string} evento_id */
async function fechaTicketsChart(evento_id) {
  const response = await fetch(`/admin/stats/${evento_id}/fecha-compras`);
  /** @type fechaComprasData */
  const fechaData = await response.json();

  new Chartkick["LineChart"](
    "participantes_compras_chart",
    [
      {
        name: "Participantes",
        data: fechaData.participantes,
      },
      {
        name: "Compras",
        data: fechaData.compras,
      },
    ],
    { colors: ["#2C435D", "#5ea3d3"] }
  );
}

/** @param {string} evento_id */
async function metodosChart(evento_id) {
  const response = await fetch(`/admin/stats/${evento_id}/metodos-status`);
  /** @type metodosData */
  const data = await response.json();
  new Chartkick["BarChart"]("pagos_aprobados_chart", data.aprobados, {
    colors: ["#5ea3d3", "#343c46", "#aeb6c2", "#e6e9ee"],
    prefix: "$",
  });
  new Chartkick["BarChart"]("pagos_por_confirmar_chart", data.por_confirmar, {
    colors: ["#5ea3d3", "#343c46", "#aeb6c2", "#e6e9ee"],
    prefix: "$",
  });
  new Chartkick["PieChart"]("ticket_metodos_chart", data.tickets_metodo, {
    colors: ["#5ea3d3", "#343c46", "#aeb6c2", "#e6e9ee"],
  });
}

/** @param {string} evento_id */
async function topParticipantesChart(evento_id) {
  const response = await fetch(`/admin/stats/${evento_id}/top-participante`);
  /** @type participantesData */
  const data = await response.json();
  new Chartkick["BarChart"]("top_participantes_chart", data.participantes, {
    colors: ["#8995a7", "#5ea3d3"],
  });
}

/** @param {string} evento_id */
async function diasVentasChart(evento_id) {
  const response = await fetch(`/admin/stats/${evento_id}/dias-ventas`);
  /** @type diasVentasData */
  const data = await response.json();
  new Chartkick["ColumnChart"]("dias_ventas_chart", data.dias_ventas, {
    colors: ["#8995a7", "#5ea3d3"],
  });
}
/** @param {string} evento_id */
async function ticketsFrecuentesChart(evento_id) {
  const response = await fetch(`/admin/stats/${evento_id}/tickets-frecuentes`);
  /** @type ticketsFrecuenteData */
  const data = await response.json();
  new Chartkick["BarChart"]("tickets_frec_chart", data.tickets_frecuentes, {
    colors: ["#5ea3d3", "#343c46", "#aeb6c2", "#e6e9ee"],
  });
}

async function renderCharts() {
  /** @type string */
  const evento_id = document.getElementById("evento_id").value;
  fechaTicketsChart(evento_id);
  fechaComprasChart(evento_id);
  metodosChart(evento_id);
  topParticipantesChart(evento_id);
  diasVentasChart(evento_id);
  ticketsFrecuentesChart(evento_id);
}

window.addEventListener("chartkick:load", renderCharts, true);
