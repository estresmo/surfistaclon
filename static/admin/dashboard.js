const tickets_fecha = "{{ tickets_fecha }}".split(",");
const TICKETS_FECHA = tickets_fecha.map((i) => i.split(";"));
const tickets_chart = TICKETS_FECHA.map((i) => [i[0], i[1]]);
const compras_chart = TICKETS_FECHA.map((i) => [i[0], i[3]]);
const buyers_chart = TICKETS_FECHA.map((i) => [i[0], i[3]]);

/**
 * @typedef {Object} fechaTicketsData
 * @property {string[][]} tickets
 * @property {string[][]} compras
 * @property {string[][]} participantes
 */

/** @param {string} evento_id */
async function fechaTicketsChart(evento_id) {
  const fechaResponse = await fetch(`/admin/stats/${evento_id}/fechas`);
  /** @type fechaTicketsData */
  const fechaData = await fechaResponse.json();

  new Chartkick["AreaChart"]("tickets_fecha_chart", fechaData.tickets, {
    colors: ["#4f1616", "#5ea3d3"],
  });
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

async function renderCharts() {
  /** @type string */
  const evento_id = document.getElementById("evento_id").value;
  await fechaTicketsChart(evento_id);
}

window.addEventListener("chartkick:load", renderCharts, true);
