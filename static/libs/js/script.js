let contador = 0;

function mayus(e) {
  e.value = e.value.toUpperCase();
}

/* Loader */
$(document).ready(function () {
  setTimeout(() => {
    document
      .getElementById("cont-loader")
      .setAttribute("style", "display:none;");
  }, "1000");
});
