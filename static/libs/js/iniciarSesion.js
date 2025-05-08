/* -------------- Iniciar sesion ------------------ */



if(iniciar_sesion = document.getElementById("iniciar_sesion")){
    iniciar_sesion.addEventListener("click", iniciarSesion, false);

function iniciarSesion(e)
{
    e.preventDefault();

    let usuario         = document.getElementById("usuario").value;
    let contrasena      = document.getElementById("contrasena").value;
   

    $.ajax({
        url: "index.php?page=loginUsuario",
        type: 'post',
        dataType: 'json',
        data: {
                usuario       : usuario,
                contrasena    : contrasena
        }
    })
    .done(function(response) {
        if (response.data.success == true) 
        {
            

            Swal.fire({
                icon: 'success',
                confirmButtonColor: '#3085d6',
                title: response.data.message,
                text:  response.data.info
            });

            location.replace('http://localhost/corpesca/index.php?page=inicio');
            
        }
        else
        {
            Swal.fire({
                icon: 'warning',
                confirmButtonColor: '#3085d6',
                title: response.data.message,
                text:  response.data.info
            });
        }
    })
    .fail(function() {
        console.log("error");
    });
}
}
