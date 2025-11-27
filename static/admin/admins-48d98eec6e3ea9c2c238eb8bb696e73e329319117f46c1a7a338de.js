function refreshDataRaffle(){
  // alert( $('#selectRaffle').val() )
  let idRaffle = $('#selectRaffle').val()
  window.open("?raffle_id=" + idRaffle, '_self');

  // chart.destroy()

  // chart.updateData(newData)
  // chart.refreshData()
}

// var chart = Chartkick.charts["main_graphic"]
// $( document ).ready(function() {
//   const chart = Chartkick.charts["graphic"]
// });
let chart = ""



document.head.innerHTML += '<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">';
$( document ).ready(function() {
  // const queryString = window.location.search;
  // const urlParams = new URLSearchParams(queryString);
  // const raffleId = urlParams.get('raffle_id')
  // alert(  "hola" )
  // if idRaffle
  $("#selectRaffle").val($("#idRaffle").html());
  // chart = Chartkick.charts["graphic"]
  $( "#selectRaffle" ).change(function() {
    // let idRaffle = $('#selectRaffle').val()
    // window.open("?raffle_id=" + idRaffle);
  });
  $( "#raffle_start_number_on" ).change(function() { calculateStartEndRaffle()});
  $( "#raffle_end_number_on" ).change(function() { calculateStartEndRaffle()});
  $( "#raffle_start_number_off" ).change(function() { calculateStartEndRaffle()});
  $( "#raffle_end_number_off" ).change(function() { calculateStartEndRaffle()});

  // $('input[type=text], textarea').css({width: '90%'});


  // $('#buyer_purchases_attributes_0_tickets_raw').keypress(function(e) {
  setTextAreaDigits();
  // changeModeRaffles();
  changeModeRafflePurchase();
  calculateStartEndRaffle();
  
  $(".button.has_many_add").click(function () {
    setTimeout(function () {
      setTextAreaDigits(); // only type digits
      // changeModeRaffles();
    }, 100);
  });
  $("#raffle_discounts").click(function () {
    this.blur()
    setDiscountValues()
    $('#containerDivFormDiscount').modal();
  });

  Coloris({
    el: '.coloris',
    swatches: [
      '#264653',
      '#2a9d8f',
      '#e9c46a',
      '#f4a261',
      '#e76f51',
      '#fff021',
      '#023e8a',
      '#0077b6',
      '#0096c7',
      '#00b4d8',
      '#48cae4'
    ]
  });
});

function updateColorConfig(){
  if ($("#raffle_colors_one")[0] == null) return;
  let json_value = `{
    "dark"=>"${$("#raffle_colors_three")[0].value}",
    "primary"=>"${$("#raffle_colors_one")[0].value}",
    "secondary"=>"${$("#raffle_colors_two")[0].value}",
    "text_normal"=>"${$("#raffle_colors_four")[0].value}",
    "text_hover"=>"${$("#raffle_colors_five")[0].value}",
    "bg_header"=>"${$("#raffle_colors_six")[0].value}",
    "text_header"=>"${$("#raffle_colors_seven")[0].value}"
  }`
  $("#raffle_colors_raw").html(json_value)
}
function calculateStartEndRaffle(){
  if ($("#raffle_start_number_on")[0] == null) return;
  
  on_start_quantity = $("#raffle_start_number_on")[0].value
  on_end_quantity = $("#raffle_end_number_on")[0].value
  off_start_quantity = $("#raffle_start_number_off")[0].value
  off_end_quantity = $("#raffle_end_number_off")[0].value
  count_on = on_end_quantity - on_start_quantity
  count_off = off_end_quantity - off_start_quantity
  if (on_end_quantity > 0) {
    $("#raffle_on_quantity").val(count_on + 1)
  }
  if (off_end_quantity > 0) {
    // if (count_off < 0) return;
    $("#raffle_off_quantity").val(count_off + 1)
  }
  if (count_on == 0) $("#raffle_on_quantity").val(0);
  if (count_off == 0) $("#raffle_off_quantity").val(0);

}

function setTextAreaDigits(){
  $('textarea.tickets').keypress(function(e) {
    var a = [];
    var k = e.which;

    for (i = 32; i < 58; i++)
        a.push(i);

    if (!(a.indexOf(k)>=0))
        e.preventDefault();
  });
}

// function changeModeRaffles() {
//   let count_items = $(".has_many_container.purchases fieldset").length
//   let txt_tickets_online = ""
//   let txt_tickets_offline = ""
//   let id_select = 0
//   let mode = ""
//   for (i = 0; i <= count_items; i++) {
//     id_select = `#buyer_purchases_attributes_${i}_mode`
//     if ($(id_select)[0] == null) continue;
//     mode = $(id_select)[0].value
//     txt_tickets_online = `#buyer_purchases_attributes_${i}_available_tickets_online_input`
//     txt_tickets_offline = `#buyer_purchases_attributes_${i}_available_tickets_offline_input`
//     if (mode == "online") {
//       $(txt_tickets_online).show();
//       $(txt_tickets_offline).hide();
//     } else if (mode == "offline") {
//       $(txt_tickets_online).hide();
//       $(txt_tickets_offline).show();
//     }
//   }
// }

// function changeModeRaffle(object) {
//   let block_id = $(object).attr("name").split("][")[1]
//   let txt_tickets_online = `#buyer_purchases_attributes_${block_id}_available_tickets_online_input`
//   let txt_tickets_offline = `#buyer_purchases_attributes_${block_id}_available_tickets_offline_input`
//   let mode = object.value
//   if (mode == "online") {
//     $(txt_tickets_online).show();
//     $(txt_tickets_offline).hide();
//   }
//   if (mode == "offline") {
//     $(txt_tickets_online).hide();
//     $(txt_tickets_offline).show();
//   }
// }

function changeModeRafflePurchase() {
  if ($("#purchase_mode")[0] == null) return;
  let txt_tickets_online = `#purchase_available_tickets_online_input`
  let txt_tickets_offline = `#purchase_available_tickets_offline_input`

  let mode = $("#purchase_mode")[0].value
  if (mode == "online") {
    $(txt_tickets_online).show();
    $(txt_tickets_offline).hide();
  }
  if (mode == "offline") {
    $(txt_tickets_online).hide();
    $(txt_tickets_offline).show();
  }
}

function pasteNumbers(textarea, precio_rifa){
  // console.log($(textarea).val());
  // console.log($(textarea).attr("name"));
  // console.log($(textarea).attr("name").split("][")[1]);
  let block_id = $(textarea).attr("name").split("][")[1]
  var addnumerosrifas = $(textarea).val();
  
  var arrynumr = addnumerosrifas.split(" ")
                  .map((a) => a.replace(/\s/g, ''));
  
  // console.log(arrynumr);
  if (arrynumr[arrynumr.length-1] == "") arrynumr.pop();

  let mode = "";
  let id_select = `#buyer_purchases_attributes_${block_id}_mode`
  let length_ticket = 0
  if ($(id_select)[0] != null) {
    mode = $(id_select)[0].value
    // Edit Purchase
    if (mode == "online") {
      // let buyer_box_online = `#buyer_purchases_attributes_${block_id}_available_tickets_online`
      let buyer_box_online = `#tickets_available_on`
      length_ticket = $(buyer_box_online).html().split(" ")[0].length
    }
    else if (mode == "offline") {
      // let buyer_box_offline = `#buyer_purchases_attributes_${block_id}_available_tickets_offline`
      let buyer_box_offline = `#tickets_available_off`
      length_ticket = $(buyer_box_offline).html().split(" ")[0].length      
      length_ticket = $(".tickets-available")[1].value.split(" ")[0].length
    }
  }
  // Edit Buyer Multiple 
  else if ($("#purchase_mode")[0] != null) {    
    mode = $("#purchase_mode")[0].value
    // let length_ticket = 0
    // Edit Purchase
    if (mode == "online") {
      length_ticket = $(".tickets-available")[0].value.split(" ")[0].length
    }
    else if (mode == "offline") {
      length_ticket = $(".tickets-available")[1].value.split(" ")[0].length
    }
  }

  // Edit Purchase
  // length_ticket = $(".tickets-available-online").html().split(" ")[0].length
  arrynumr.map( (a,i) => {
    if (a.length > length_ticket) {
      $.toast({
          heading: 'Error',
          text: `Ticket muy largo: ${a}`,
          icon: 'error'
      })
      return;
    }
    if (i != arrynumr.length - 1 && a.length < length_ticket) {
      $.toast({
          heading: 'Error',
          text: `Ticket muy corto: ${a}`,
          icon: 'error'
      })
      return;
    }
  });
  // asignation("addcantidadRifasEdit",arrynumr.length);
  // asignation("addmontoTotalEdit","S/"+arrynumr.length*precio_rifa);
  // console.log(block_id);
  // let buyer_box_amount = `#buyer_purchases_attributes_${block_id}_amount`
  let buyer_box_quantity = `#buyer_purchases_attributes_${block_id}_quantity`
  // $("#purchase_amount").val((arrynumr.length*precio_rifa));
  $("#purchase_quantity").val(arrynumr.length);
  // $(buyer_box_amount).val((arrynumr.length*precio_rifa));
  $(buyer_box_quantity).val(arrynumr.length);
}

function verifyPurchase(e, button, purchaseToken, purchaseId, userId) {
  e.preventDefault();
  $.toast("VERIFICANDO...")
  // let purchase_id = `#purchase_${purchaseToken}`
  // let purchase = $(purchase_id)
  // let find_btn = purchase.find("a")
  approvePurchase(purchaseToken, purchaseId, userId, button)
}

function approvePurchase(purchaseToken, purchaseId, userId, button) {
  let formVoucherData = new FormData();
  formVoucherData.append('purchase_token', purchaseToken);
  formVoucherData.append('purchase[status]', 'verified');
  formVoucherData.append('purchase[verifier_user_id]', userId);
  $.ajax({
    url: `/api/v1/approve_purchase`,
    type: 'PATCH',
    data: formVoucherData,
    contentType: false,
    processData: false,
    success: function (purchase) {
      let id_amount_span = `#purchase_${purchaseId} span` 
      let cell_amount = $(id_amount_span)
      if (cell_amount) cell_amount.hide()
      button.classList.remove("pending");
      button.classList.add("verified");
      window.location.reload();
    },
    error: function (request, message, error) {
      $.toast({
        heading: 'Error',
        text: request.responseJSON.errors.filter((v, i, a) => a.indexOf(v) === i).join(", "),
        icon: 'error'
      })
    }
  });
}

function loadImageModal(image_url){
  $("#img-voucher").attr("src", image_url);
}

function setDiscountValues(){
  let val1 = $("#raffle_discount_rate")[0].value
  let val2 = $("#raffle_discount_rate_increase")[0].value
  let val3 = $("#raffle_discount_max_tickets")[0].value
  $("#percent_discount").val(val1)
  $("#label_percent_discount").html((+val1).toFixed(2) + "%")

  $("#percent_increase").val(val2)
  $("#label_percent_increase").html((+val2).toFixed(2) + "%")

  $("#discount_max_tickets").val(val3)
  $("#label_discount_max_tickets").html(val3)
  setJsonDiscounts()
}
function setJsonDiscounts(){
  let val11 = $("#raffle_discount_rate")[0].value
  let val22 = $("#raffle_discount_rate_increase")[0].value
  let val33 = $("#raffle_discount_max_tickets")[0].value
  let jsonvalues = {rate: val11, increase: val22, max_tickets: val33}
  $("#raffle_discounts").val(JSON.stringify(jsonvalues))
  generateDiscounts();
}

function calcPercentDiscount(){
  let percent_discount = $("#percent_discount")[0].value
  $("#raffle_discount_rate").val(percent_discount)
  $("#label_percent_discount").html((+percent_discount).toFixed(2) + "%")
  setJsonDiscounts()
}
function calcPercentIncrease(){
  let percent_increase = $("#percent_increase")[0].value
  $("#raffle_discount_rate_increase").val(percent_increase)
  $("#label_percent_increase").html((+percent_increase).toFixed(2) + "%")
  setJsonDiscounts()
}
function calcDiscountMaxTicket(){
  let discount_max_tickets = $("#discount_max_tickets")[0].value
  $("#raffle_discount_max_tickets").val(discount_max_tickets)
  $("#label_discount_max_tickets").html(discount_max_tickets)
  setJsonDiscounts()
}

function generateDiscounts(){
  let country_code = $("#raffle_country_code")[0].value
  let currency_code = $("#raffle_currency_code")[0].value
  let percent_discount = +$("#percent_discount")[0].value
  let percent_increase = +$("#percent_increase")[0].value
  let discount_max_tickets = +$("#discount_max_tickets")[0].value

  let price_ticket = +$("#raffle_price_unit")[0].value
  let quantity_tickets = [1, 2, 3, 4, 5, 10, 20, 50, 100]
  let rows = ``
  
  $.each(quantity_tickets, function (index, ticket_qty) {
    let priceTotal = ticket_qty * price_ticket
    let cant_rifas_one_less = ticket_qty - 1
    let discount_by_ticket = cant_rifas_one_less * percent_discount
    let discount_increment = cant_rifas_one_less * percent_increase
    if (cant_rifas_one_less > discount_max_tickets) {
      discount_increment = (discount_max_tickets + 1) * percent_increase
    }
    let finalPriceTotal = priceTotal - (discount_by_ticket * discount_increment * 100 / price_ticket).toFixed(0)
    let costByTicket = (finalPriceTotal / ticket_qty).toFixed(2)

    rows += `
      <tr>
        <td>${ticket_qty}</td>
        <td>${parsePriceCountry(country_code, currency_code, priceTotal)}</td>
        <td><strong>${parsePriceCountry(country_code, currency_code, finalPriceTotal)}</strong></td>
        <td>${parsePriceCountry(country_code, currency_code, (priceTotal - finalPriceTotal))}</td>
        <td>${parsePriceCountry(country_code, currency_code, costByTicket)}</td>
      </tr>
    `
    // $("#numbersContain").append('<div class="chip misticketsson">'+ticket+'</div>');
    // $("#ticketsContain").append(drawTicket(purchase, ticket));
  });

  $("#table_prices_discount").html(rows)
}

function parsePriceCountry(country_code, currency_code, price) {
  let languageCountryCode = `es-${country_code}`
  return new Intl.NumberFormat(languageCountryCode, { style: 'currency', currency: currency_code }).format(price);
}




// $("#urlimgup").bind("paste", function(e){

// });
