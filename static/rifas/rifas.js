$("#buttfixed").on("click", function () {
  $("#linksfixed").toggle();
});
$(window).scroll(function () {
  if ($(this).scrollTop() > 20) {
    $("#navbar").addClass("header-scrolled");
  } else {
    $("#navbar").removeClass("header-scrolled");
  }
});

$("#navbarNav").on("click", "a", function () {
  $(".navbar-toggle").click();
});
$(".nav-item").on("click", "a", function () {
  $("#navbarNav").removeClass("show");
});
$(document).ready(function () {
  $("#owl-carousel-clients").owlCarousel({
    items: 3,
    loop: false,
    nav: true,
    autoplay: true,
    autoplayTimeout: 3000,
    autoplayHoverPause: true,
    responsiveClass: true,
    responsive: {
      0: {
        items: 1,
      },
      600: {
        items: 2,
      },
      1000: {
        items: 3,
      },
    },
  });
});
$(document).ready(function () {
  $("#owl-carousel-raffles").owlCarousel({
    items: 3,
    loop: false,
    nav: false,
    autoplay: false,
    autoplayTimeout: 3000,
    autoplayHoverPause: true,
    responsiveClass: true,
    responsive: {
      0: {
        items: 1,
      },
      600: {
        items: 2,
      },
      1000: {
        items: 3,
      },
    },
  });
});

function actionButtonAccounts(action_type, elemnt, text) {
  if (action_type == "copy") {
    $(elemnt).addClass("copied");
    setTimeout(function () {
      $(elemnt).removeClass("copied");
    }, 1200);
    var sampleTextarea = document.createElement("textarea");
    document.body.appendChild(sampleTextarea);
    sampleTextarea.value = text;
    // sampleTextarea.value = text.replace(/ /g,'');
    sampleTextarea.select();
    document.execCommand("copy");
    document.body.removeChild(sampleTextarea);
  } else if (action_type == "link") {
    window.open(text, "_blank").focus();
  }
}
document.addEventListener("DOMContentLoaded", function () {
  document.querySelector("#container-payments").firstElementChild.click();
});
document.addEventListener("DOMContentLoaded", () => {
  const firstElement =
    document.getElementById("container-payments").firstElementChild;
  firstElement.classList.add("selected");
  cambiarPago(firstElement);
});
