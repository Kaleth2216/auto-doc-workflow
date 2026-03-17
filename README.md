### auto-doc-workflow
#### Documentación automática con n8n + Ollama

---
#### Servicio de clima usando OpenWeatherMap

| Función | Descripción | Parámetros |
| --- | --- | --- |
| `obtener_clima` | Obtiene el clima actual de una ciudad | - `ciudad`: La ciudad para la que se desea obtener el clima. |
|           |                   | - `api_key`: La clave API para OpenWeatherMap. |
|           |                   | - `datos`: La respuesta JSON con los datos del clima (formateado). |
| `obtener_pronostico` | Obtiene el pronóstico del clima para los próximos días | - `ciudad`: La ciudad para la que se desea obtener el pronóstico del clima. |
|               |                  | - `api_key`: La clave API para OpenWeatherMap. |
|               |                  | - `dias` (opcional): El número de días para obtener el pronóstico. (Por defecto: 5). |
| `formatear_clima` | Formatea los datos del clima en un string legible | - `datos`: La respuesta JSON con los datos del clima. |
| `obtener_resumen` | Obtiene y formatea el clima actual en una sola llamada | - `ciudad`: La ciudad para la que se desea obtener el clima actual. |
|               |                  | - `api_key`: La clave API para OpenWeatherMap. |

---
#### Módulo Ollama

| Función | Descripción | Parámetros |
| --- | --- | --- |
| `método_1` | Descripción del método 1 | - `parametro_1`: El primer parámetro. |
|           |                   | - `parametro_2`: El segundo parámetro. |

---
#### Servicio de clima usando OpenWeatherMap

| Función | Descripción | Parámetros |
| --- | --- | --- |
| `obtener_clima` | Obtiene el clima actual de una ciudad | - `ciudad`: La ciudad para la que se desea obtener el clima. |
|           |                   | - `api_key`: La clave API para OpenWeatherMap. |
| `formatear_clima` | Formatea los datos del clima en un string legible | - `datos`: La respuesta JSON con los datos del clima. |
| `obtener_pronostico` | Obtiene el pronóstico del clima para los próximos días | - `ciudad`: La ciudad para la que se desea obtener el pronóstico del clima. |
|               |                  | - `api_key`: La clave API para OpenWeatherMap. |
|               |                  | - `dias` (opcional): El número de días para obtener el pronóstico. (Por defecto: 5). |
| `obtener_resumen` | Obtiene y formatea el clima actual en una sola llamada | - `ciudad`: La ciudad para la que se desea obtener el clima actual. |
|               |                  | - `api_key`: La clave API para OpenWeatherMap. |