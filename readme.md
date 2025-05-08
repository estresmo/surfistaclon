# Sistema de Rifas en Django con PostgreSQL

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)

## Descripción del Proyecto

Sistema de gestión de rifas desarrollado con Django y PostgreSQL. Permite crear, gestionar y sortear rifas con funcionalidades para administradores y participantes.

## Características Principales

- 🎟️ Creación y gestión de múltiples rifas
- 👥 Registro de participantes
- 📊 Panel de administración integrado
- 🎰 Mecanismo de sorteo aleatorio
- 📱 Diseño responsive
- 🔐 Autenticación de usuarios

## Requisitos del Sistema

- Python 3.8+
- Django 4.0+
- PostgreSQL 12+
- pip
- Resizear imagenes

## Instalación

1. **Clonar repositorio**:

```bash
git clone https://github.com/Carlitos126/una_cosa_de_locos.git
cd una_cosa_de_locos
```

2. **Crear entorno virtual**:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Instalar dependencias**:

```bash
pip install -r requirements.txt
```

4. **Configurar PostgreSQL**:

- Crear una base de datos en PostgreSQL
- Configurar en `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nombre_db',
        'USER': 'usuario_db',
        'PASSWORD': 'contraseña_db',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

5. **Migraciones y superusuario**:

```bash
python manage.py migrate
python manage.py createsuperuser
```

6. **Ejecutar servidor**:

```bash
python manage.py runserver
```

## Estructura del Proyecto

```
sistema-rifas/
├── core/              # Configuración Django
├── gestion/           # Panel administrativo
├── rifa/              # Lógica de rifas
├── static/            # CSS, JS e imágenes
├── media/             # Imágenes subidadas (comprobantes y eventos)
├── templates/         # Plantillas
└── manage.py          # Script principal
```

## Uso del Sistema

1. **Administrador**:

- Acceder a `/gestion` con credenciales de superusuario

2. **Participantes**:

- Registrar comprobantes en `/`

## Mejoras pendientes

- Colocar mas bonitos los botones de copiar métodos de pago
- HECHO - Quitar todas las referencias de PHP del admin
- HECHO -Arreglar CSS del admin
- HECHO - Al eliminar en el admin no devuelve una respuesta correcta
- HECHO - Colocar que en el generar comprobante que cuando devuelva 403 recargue la página
- HECHO - Quitar todo el css externo del admin
- DESCARTADO - Que al eliminar en el admin no recargue la página
- Tratar de fusionar todo el CSS en el home
- HECHO - Limpiar del requirements los paquetes que no se usen
- HECHO -Colocar en comprobantes el total de boletos vendidos
- En comprobante del admin mejorar la selección de números
- DESCARTADO - Colocar una librería de alertas (sweet alert o toastjs)
- DESCARTADO - Colocar histórico eventos y fotos del ganador
- HECHO - Limpiar static
- Reducir tamaño de imágenes al subir
- HECHO - Al mandar WhatsApp mande el comprobante y el link para acceder al admin
- HECHO - Arreglar estadísticas
- HECHO - Arreglar enlaces del home
