am4core.ready(function () {

    // // Themes begin
    // am4core.useTheme(am4themes_animated);
    // am4core.useTheme(am4themes_dark)
    // // Themes end

    // // Create chart instance
    // var chart = am4core.create("grafica", am4charts.PieChart);

    // // Add data

    // let url = 'index.php?page=graficaEspeciesInventario';
    // fetch(url)
    //     .then(response => response.json() )
    //     .then( datos => mostrar(datos))
    //     .catch( e => console.log(e))

    // const mostrar = (articulos)=> {
    //     articulos.forEach(element => {
    //           chart.data.push(element.nombre_especialidad)  
    //     });
    //     chart.data = articulos
    //     console.log(chart.data)

    // }

    // chart.innerRadius = am4core.percent(50);

    // // Add and configure Series
    // var pieSeries = chart.series.push(new am4charts.PieSeries());
    // pieSeries.dataFields.value = "kilos";
    // pieSeries.dataFields.category = "especie_presentacion";
    // pieSeries.slices.template.stroke = am4core.color("#fff");
    // pieSeries.slices.template.strokeOpacity = 1;

    // // This creates initial animation
    // pieSeries.hiddenState.properties.opacity = 1;
    // pieSeries.hiddenState.properties.endAngle = -90;
    // pieSeries.hiddenState.properties.startAngle = -90;

    // chart.hiddenState.properties.radius = am4core.percent(0);

    // // Add a legend
    // chart.legend = new am4charts.Legend();

    // Create chart instance
    var chart = am4core.create("grafica", am4charts.PieChart);

    // Add data

    let url = 'index.php?page=graficaEspeciesInventario';
    fetch(url)
        .then(response => response.json())
        .then(datos => mostrar(datos))
        .catch(e => console.log(e))

    const mostrar = (articulos) => {
        articulos.forEach(element => {
            chart.data.push(element.nombre_especialidad)
        });
        chart.data = articulos
        console.log(chart.data)

    }

    // Add and configure Series
    var pieSeries = chart.series.push(new am4charts.PieSeries());
    pieSeries.dataFields.value = "kilos";
    pieSeries.dataFields.category = "especie_presentacion";

    // This creates initial animation
    pieSeries.hiddenState.properties.opacity = 1;
    pieSeries.hiddenState.properties.endAngle = -90;
    pieSeries.hiddenState.properties.startAngle = -90;

    // Let's cut a hole in our Pie chart the size of 40% the radius
    chart.innerRadius = am4core.percent(40);

    // Put a thick white border around each Slice
    pieSeries.slices.template.stroke = am4core.color("#4a2abb");
    pieSeries.slices.template.strokeWidth = 2;
    pieSeries.slices.template.strokeOpacity = 1;


    // Add a legend
    chart.legend = new am4charts.Legend();


}); // end am4core.ready()