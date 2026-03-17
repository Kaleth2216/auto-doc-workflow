### auto-doc-workflow
#### Documentación automática con n8n + Ollama

#### Cambios en la documentación

*   **Servicio de clima usando OpenWeatherMap**
    *   `BASE_URL`: URL base para las solicitudes a OpenWeatherMap.
    *   `obtener_clima(ciudad: str, api_key: str) -> dict`
        +   Obtiene el clima actual de una ciudad.
        +   Parámetros:
            -   `ciudad`: La ciudad para la que se desea obtener el clima.
            -   `api_key`: La clave API para OpenWeatherMap.
        +   Retorno: Una respuesta JSON con los datos del clima.
    *   `formatear_clima(datos: dict) -> str`
        +   Formatea los datos del clima en un string legible.
        +   Parámetros:
            -   `datos`: La respuesta JSON con los datos del clima.
        +   Retorno: Un string con la información del clima.
    *   `obtener_pronostico(ciudad: str, api_key: str, dias: int = 5) -> dict`
        +   Obtiene el pronóstico del clima para los próximos días.
        +   Parámetros:
            -   `ciudad`: La ciudad para la que se desea obtener el pronóstico del clima.
            -   `api_key`: La clave API para OpenWeatherMap.
            -   `dias` (opcional): El número de días para obtener el pronóstico. (Por defecto: 5).
        +   Retorno: Una respuesta JSON con los datos del pronóstico del clima.
    *   `obtener_resumen(ciudad: str, api_key: str) -> str`
        +   Obtiene y formatea el clima actual en una sola llamada.
        +   Parámetros:
            -   `ciudad`: La ciudad para la que se desea obtener el clima actual.
            -   `api_key`: La clave API para OpenWeatherMap.
        +   Retorno: Un string con la información del clima actual.