# Drumline — audio a MIDI

Prototipo web en español. Subí WAV, FLAC u OGG, ajustá sensibilidad y descargá un archivo MIDI General MIDI en canal 10: bombo (36), caja (38), hi-hat cerrado (42).

## Ejecutar

Requiere Python 3.10 o superior.

```sh
pip install -r requirements.txt
python server.py
```

Abrir http://localhost:8000.

## Alcance

Detección heurística de ataques por bandas de frecuencia con librosa. No es separación de fuentes ni una transcripción profesional con inteligencia artificial. Un golpe puede activar varias bandas. Funciona mejor con batería aislada; mezclas completas pueden generar falsos positivos. No distingue toms, platos abiertos ni articulaciones. El tempo automático puede detectar medio o doble tiempo: se puede corregir manualmente. La cuantización alinea a semicorcheas desde el inicio del archivo, no detecta el primer compás.

Máximo 45 MB y 3 minutos por archivo. El archivo se procesa en memoria en el servidor y no se guarda en disco. La interfaz permite escuchar el audio original, no sintetiza el MIDI. La primera operación puede demorar por la inicialización de las bibliotecas.

Servidor de desarrollo sin autenticación ni limitación de concurrencia: no exponer como servicio público de producción sin un servidor adecuado, controles de recursos y seguridad.

## Superior Drummer 3

El mapa de salida está definido explícitamente en `SD3_MAP` en `server.py`:

| Articulación compatible | Nota MIDI |
| --- | --- |
| Bombo | 36 |
| Caja, centro | 38 |
| Hi-hat cerrado | 42 |

Estas tres notas coinciden con General MIDI y con el mapa predeterminado de Superior Drummer. No se exportan las demás articulaciones de SD3 ni control continuo del hi-hat. Usá el mapa predeterminado en SD3; un preset personalizado o de batería electrónica puede reasignar notas.

Referencia de compatibilidad: https://onlinemidiremap.com/blog.html

## Windows: doble clic

Instalá Python 3.11 de 64 bits (con su lanzador `py`) y abrí `INICIAR.bat`.
La primera ejecución requiere Internet para instalar las dependencias. Las siguientes reutilizan el entorno local. Mantené abierta la consola mientras usás la web. Si el puerto 8000 ya está ocupado, cerrá la otra instancia antes de iniciar.

La aplicación requiere un backend Python: subirla a GitHub permite descargarla y versionarla, pero GitHub Pages por sí solo no ejecuta la transcripción.
