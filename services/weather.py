import requests

# Servicio de clima usando OpenWeatherMap aaa
def obtener_clima(ciudad: str, api_key: str) -> dict:
    url = f'https://api.openweathermap.org/data/2.5/weather'
    params = {'q': ciudad, 'appid': api_key, 'units': 'metric', 'lang': 'es'}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f'Error al obtener clima: {response.status_code}')
    return response.json()

def formatear_clima(datos: dict) -> str:
    nombre = datos['name']
    temp = datos['main']['temp']
    descripcion = datos['weather'][0]['description']
    humedad = datos['main']['humidity']
    return f'{nombre}: {temp}°C, {descripcion}, humedad {humedad}%'S