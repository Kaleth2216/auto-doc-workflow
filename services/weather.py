import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

BASE_URL = 'https://api.openweathermap.org/data/2.5'
_cache = {}
CACHE_DURACION = timedelta(minutes=10)

class ClimaError(Exception):
    """Error personalizado para el servicio de clima."""
    pass

def _obtener_cache(clave: str) -> dict | None:
    """Retorna datos del caché si aún son válidos."""
    if clave in _cache:
        datos, timestamp = _cache[clave]
        if datetime.now() - timestamp < CACHE_DURACION:
            return datos
    return None

def _guardar_cache(clave: str, datos: dict) -> None:
    """Guarda datos en el caché con timestamp."""
    _cache[clave] = (datos, datetime.now())

def obtener_clima(ciudad: str, api_key: str) -> dict:
    """Obtiene el clima actual de una ciudad."""
    clave = f"clima_{ciudad}"
    cached = _obtener_cache(clave)
    if cached:
        return cached
    params = {'q': ciudad, 'appid': api_key, 'units': 'metric', 'lang': 'es'}
    try:
        response = requests.get(f'{BASE_URL}/weather', params=params)
        response.raise_for_status()
    except requests.HTTPError as e:
        raise ClimaError(f'Error al obtener clima de {ciudad}: {e}')
    datos = response.json()
    _guardar_cache(clave, datos)
    return datos

def formatear_clima(datos: dict) -> str:
    """Formatea los datos del clima en un string legible."""
    return (
        f"{datos['name']}: "
        f"{datos['main']['temp']}°C, "
        f"{datos['weather'][0]['description']}, "
        f"humedad {datos['main']['humidity']}%"
    )

def obtener_pronostico(ciudad: str, api_key: str, dias: int = 5) -> dict:
    """Obtiene el pronóstico del clima para los próximos días."""
    clave = f"pronostico_{ciudad}_{dias}"
    cached = _obtener_cache(clave)
    if cached:
        return cached
    params = {'q': ciudad, 'appid': api_key, 'units': 'metric', 'lang': 'es', 'cnt': dias}
    try:
        response = requests.get(f'{BASE_URL}/forecast', params=params)
        response.raise_for_status()
    except requests.HTTPError as e:
        raise ClimaError(f'Error al obtener pronóstico de {ciudad}: {e}')
    datos = response.json()
    _guardar_cache(clave, datos)
    return datos

def obtener_resumen(ciudad: str, api_key: str) -> str:
    """Obtiene y formatea el clima actual en una sola llamada."""
    datos = obtener_clima(ciudad, api_key)
    return formatear_clima(datos)

def obtener_clima_multiple(ciudades: list[str], api_key: str) -> dict[str, dict]:
    """Obtiene el clima de múltiples ciudades en paralelo."""
    def _fetch(ciudad):
        try:
            return ciudad, obtener_clima(ciudad, api_key)
        except ClimaError as e:
            return ciudad, {'error': str(e)}

    with ThreadPoolExecutor(max_workers=5) as executor:
        resultados = executor.map(_fetch, ciudades)

    return dict(resultados)

def resumen_multiple(ciudades: list[str], api_key: str) -> list[str]:
    """Retorna resúmenes formateados de múltiples ciudades."""
    climas = obtener_clima_multiple(ciudades, api_key)
    return [
        formatear_clima(datos) if 'error' not in datos else f"{ciudad}: error al obtener clima"
        for ciudad, datos in climas.items()
    ]

def limpiar_cache() -> None:
    """Limpia todo el caché manualmente."""
    _cache.clear()