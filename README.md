# TrasportMapsGenerator
# 🗺️ Mapa de Calor de Tiempos de Viaje desde Nuevos Ministerios (Madrid)

Este proyecto permite calcular el tiempo de viaje en transporte público multimodal desde el intercambiador de **Nuevos Ministerios** hacia todos los puntos de la red de transportes de la Comunidad de Madrid a una hora específica (Hora punta: 08:00 AM). 

Utiliza **OpenTripPlanner (OTP)** como motor de enrutamiento basado en horarios reales, un script de **Python** optimizado con hilos concurrentes para la extracción masiva de datos y **QGIS** para la generación del mapa de calor final.

---

## 🛠️ Requisitos Previos

Antes de empezar, asegúrate de tener instalado en tu equipo:
* **Python 3.10 o superior**
* **Java SE Runtime Environment 8 (o superior)** -> Necesario para arrancar el servidor de OpenTripPlanner.
* **QGIS (versión 3.x)** -> Para la visualización espacial y la interpolación.

---

## 📂 Estructura de Carpetas del Proyecto

Para que el script y el servidor funcionen correctamente, organiza tus archivos en el directorio raíz de la siguiente manera:

```text
madrid-transit-heatmap/
├── metro_gtfs.zip
├── cercanias_gtfs.zip
├── emt_bus_gtfs.zip
├── interurbanos_bus_gtfs.zip
├── metro_ligero_gtfs.zip
├── madrid-latest.osm.pbf
├── opentripplanner-1.5.0-shaded.jar
├── router-config.json
├── generar_tiempos.py
└── requirements.txt
```

---

## 🚀 Pasos para el Despliegue

### Paso 1: Descarga de Datos de Entrada
1. **Archivos GTFS**: Descarga los 5 archivos programáticos oficiales desde el portal del **CRTM** y renómbralos exactamente como se muestra en la estructura de carpetas anterior (mantén el formato `.zip`, no los descomprimas).
2. **Mapa de Calles (OSM)**: Descarga el extracto de la Comunidad de Madrid en formato `.osm.pbf` desde [Geofabrik](https://geofabrik.de).
3. **Motor OTP**: Descarga el ejecutable `opentripplanner-1.5.0-shaded.jar` (versión estable 1.5.0, la 2.6.0 no es posible compilarla con la ultima versión de java).

### Paso 2: Crear el Archivo de Configuración de Rutas
Crea un archivo de texto llamado `router-config.json` para definir los parámetros de caminata urbana y transbordos de la red madrileña:
```json
{
  "routingDefaults": {
    "walkSpeed": 1.33,
    "transferSlack": 120
  }
}
```

### Paso 3: Construir y Arrancar el Servidor de Rutas (OTP)
Abre tu terminal o consola de comandos en la carpeta del proyecto y ejecuta los siguientes comandos aplicando 6GB de memoria RAM para soportar la alta concurrencia:

```bash
# A. Construir el grafo de red unificado (Este proceso lee los 5 GTFS + OSM y tarda unos minutos)
java -Xmx6G -jar opentripplanner-1.5.0-shaded.jar --build GTFS

# B. Levantar el servidor local de mapas
java -Xmx6G -jar opentripplanner-1.5.0-shaded.jar --graphs . --router GTFS --server
```
*Deja esta ventana de la terminal abierta.* El servidor estará listo cuando veas el mensaje `Grizzly server running on port 8080`.

### Paso 4: Ejecutar el Script de Python
Abre **otra ventana de la terminal** para instalar las dependencias de Python y lanzar la extracción multihilo:

```bash
# Instalar las librerías necesarias
pip install -r requirements.txt

# Ejecutar la consulta masiva de tiempos
python generar_tiempos.py
```
Al finalizar el script, se habrá generado el archivo `tiempos_madrid_completo_8am.csv` con la latitud, longitud y los minutos de viaje calculados para cada parada.

---

## 🎨 Generación del Heatmap en QGIS

1. Abre QGIS y arrastra el archivo `tiempos_madrid_completo_8am.csv` al panel de capas.
2. Configura la geometría usando la columna `lon` (X) y `lat` (Y) con el SRC **EPSG:4326**.
3. Haz clic derecho en la capa importada -> *Exportar -> Guardar objetos como...* y guárdala en formato GeoPackage utilizando el sistema métrico local de Madrid: **EPSG:25830 (ETRS89 / UTM zone 30N)**.
4. Abre la **Caja de herramientas de procesos** (Ctrl+Alt+T) y busca **Interpolación IDW**.
5. Configura la herramienta:
   * **Capa**: Tu capa guardada en metros (EPSG:25830).
   * **Atributo de interpolación**: `time_mins` (haz clic en el botón verde **"+"**).
   * **Tamaño del píxel de salida**: `50` (para obtener una resolución de celda de 50x50 metros).
6. Haz doble clic sobre el ráster generado, ve a **Simbología**, selecciona **Monobanda pseudocolor** y aplica una rampa de color invertida (ej. Verde para tiempos cortos, Rojo para tiempos largos).
