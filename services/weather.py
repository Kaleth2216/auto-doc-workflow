import requests

BASE_URL = 'https://api.openweathermap.org/data/2.5'

def obtener_clima(ciudad: str, api_key: str) -> dict:
    """Obtiene el clima actual de una ciudad."""
    params = {'q': ciudad, 'appid': api_key, 'units': 'metric', 'lang': 'es'}
    response = requests.get(f'{BASE_URL}/weather', params=params)
    response.raise_for_status()
    return response.json()

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
    params = {'q': ciudad, 'appid': api_key, 'units': 'metric', 'lang': 'es', 'cnt': dias}
    response = requests.get(f'{BASE_URL}/forecast', params=params)
    response.raise_for_status()
    return response.json()

def obtener_resumen(ciudad: str, api_key: str) -> str:
    """Obtiene y formatea el clima actual en una sola llamada."""
    datos = obtener_clima(ciudad, api_key)
    return formatear_clima(datos)