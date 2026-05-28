import pandas as pd
import requests
import zipfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 1. Definir los nombres de tus 5 archivos GTFS descargados del CRTM
# Asegúrate de que los nombres coincidan exactamente con tus archivos .zip en la carpeta
gtfs_files = {
    'metro': 'metro_gtfs.zip',
    'cercanias': 'cercanias_gtfs.zip',
    'emt': 'emt_bus_gtfs.zip',
    'interurbanos': 'interurbanos_bus_gtfs.zip',
    'metro_ligero': 'metro_ligero_gtfs.zip'
}

all_stops = []

# 2. Leer y fusionar los 'stops.txt' de todos los archivos
print("Leyendo y uniendo las paradas de toda la red de Madrid (incluyendo Metro Ligero)...")
for mode, file_name in gtfs_files.items():
    if os.path.exists(file_name):
        with zipfile.ZipFile(file_name) as z:
            with z.open('stops.txt') as f:
                df_stops = pd.read_csv(f)
                df_stops = df_stops[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']].copy()
                df_stops['mode'] = mode
                all_stops.append(df_stops)
    else:
        print(f"Advertencia: No se encontró el archivo {file_name}, se ignorará.")

# Consolidar en un solo DataFrame
df_all_stops = pd.concat(all_stops, ignore_index=True)

# Eliminar duplicados geográficos aproximados (redondeo a 4 decimales ~11 metros)
df_all_stops['lat_round'] = df_all_stops['stop_lat'].round(4)
df_all_stops['lon_round'] = df_all_stops['stop_lon'].round(4)
df_unique_destinations = df_all_stops.drop_duplicates(subset=['lat_round', 'lon_round']).reset_index(drop=True)

total_paradas = len(df_unique_destinations)
print(f"Total de paradas únicas a analizar en Madrid: {total_paradas}")

# 3. Configurar punto de inicio (Nuevos Ministerios) y parámetros globales
start_lat = 40.4466
start_lon = -3.6922
url = "http://localhost:8080/otp/routers/default/plan"
date = "2026-06-02"  # Martes laborable
time = "08:00:00"

results = []

# Función individual que ejecutará cada hilo
def consultar_parada(row):
    params = {
        "fromPlace": f"{start_lat},{start_lon}",
        "toPlace": f"{row['stop_lat']},{row['stop_lon']}",
        "time": time,
        "date": date,
        "mode": "TRANSIT,WALK",       
        "maxWalkDistance": 1200,      
        "walkSpeed": 1.33,            
        "arriveBy": "false"
    }
    try:
        response = requests.get(url, params=params, timeout=10).json()
        duration = response['plan']['itineraries'][0]['duration'] # Primer itinerario disponible
        travel_time_mins = duration / 60
        
        return {
            'stop_name': row['stop_name'],
            'lat': row['stop_lat'],
            'lon': row['stop_lon'],
            'time_mins': travel_time_mins,
            'main_mode': row['mode']
        }
    except Exception:
        return None

print(f"\nCalculando tiempos multimodales con concurrencia (10 hilos)...")

# 4. Lanzar el pool de hilos concurrentes
contador = 0
with ThreadPoolExecutor(max_workers=10) as executor:
    futuras_consultas = {executor.submit(consultar_parada, row): row for _, row in df_unique_destinations.iterrows()}
    
    for future in as_completed(futuras_consultas):
        resultado = future.result()
        if resultado is not None:
            results.append(resultado)
        
        contador += 1
        if contador % 500 == 0:
            print(f"Progreso: {contador}/{total_paradas} paradas analizadas...")

# 5. Guardar el resultado final para QGIS
df_heatmap = pd.DataFrame(results)
df_heatmap.to_csv('tiempos_madrid_completo_8am.csv', index=False)

print(f"\n¡Proceso completado con éxito!")
print(f"Archivo 'tiempos_madrid_completo_8am.csv' generado con {len(df_heatmap)} destinos válidos.")
