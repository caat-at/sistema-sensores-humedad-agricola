# -*- coding: utf-8 -*-
"""
Script mejorado para decodificar y visualizar el datum del contrato
con estadísticas, filtros, y exportación de datos
"""

import sys
import argparse
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import Counter

import config
import cardano_utils as cu
from contract_types import (
    HumiditySensorDatum,
    SensorConfig,
    HumidityReading,
    Active, Inactive, Maintenance, ErrorStatus,
    Normal, Low, High, Critical
)


# ========================================
# UTILIDADES DE FORMATO Y COLOR
# ========================================

class Colors:
    """Códigos ANSI para colores en terminal (Windows compatible)"""
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Colores básicos
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Fondo
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'


def format_color(text: str, color: str, bold: bool = False) -> str:
    """Formatea texto con color ANSI"""
    prefix = Colors.BOLD if bold else ''
    return f"{prefix}{color}{text}{Colors.RESET}"


def print_header(title: str, width: int = 80):
    """Imprime un header con formato"""
    print()
    print("=" * width)
    print(f" {title}")
    print("=" * width)
    print()


def print_section(title: str):
    """Imprime un título de sección"""
    print()
    print(format_color(f"[{title}]", Colors.CYAN, bold=True))
    print("-" * 80)


def format_percentage(value: int, min_val: int, max_val: int) -> str:
    """Formatea porcentaje con barra visual (Windows compatible)"""
    if value < 20:
        color = Colors.RED
        bar_char = '#'
    elif value < 40:
        color = Colors.YELLOW
        bar_char = '='
    elif value <= 70:
        color = Colors.GREEN
        bar_char = '='
    elif value <= 85:
        color = Colors.YELLOW
        bar_char = '='
    else:
        color = Colors.RED
        bar_char = '#'

    bar_length = min(50, value // 2)
    bar = bar_char * bar_length

    return f"{format_color(f'{value:3d}%', color)} [{format_color(bar, color)}]"


# ========================================
# DECODIFICACIÓN Y HELPERS
# ========================================

def decode_status(status) -> Tuple[str, str]:
    """Decodifica el estado del sensor y retorna (nombre, color)"""
    if isinstance(status, Active):
        return "Active", Colors.GREEN
    elif isinstance(status, Inactive):
        return "Inactive", Colors.YELLOW
    elif isinstance(status, Maintenance):
        return "Maintenance", Colors.BLUE
    elif isinstance(status, ErrorStatus):
        return "Error", Colors.RED
    else:
        return "Unknown", Colors.WHITE


def decode_alert_level(alert) -> Tuple[str, str, str]:
    """Decodifica nivel de alerta y retorna (nombre, color, icono) (Windows compatible)"""
    if isinstance(alert, Normal):
        return "Normal", Colors.GREEN, "[OK]"
    elif isinstance(alert, Low):
        return "Low", Colors.YELLOW, "[LOW]"
    elif isinstance(alert, High):
        return "High", Colors.YELLOW, "[HIGH]"
    elif isinstance(alert, Critical):
        return "Critical", Colors.RED, "[!]"
    else:
        return "Unknown", Colors.WHITE, "[?]"


def format_timestamp(timestamp_ms: int) -> str:
    """Convierte timestamp de milisegundos a formato legible"""
    try:
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(timestamp_ms)


def format_coordinates(lat_int: int, lon_int: int) -> str:
    """Convierte coordenadas enteras a decimales"""
    lat = lat_int / 1_000_000
    lon = lon_int / 1_000_000
    return f"{lat:.4f}, {lon:.4f}"


# ========================================
# ESTADÍSTICAS
# ========================================

class DatumStats:
    """Calcula estadísticas del datum"""

    def __init__(self, datum: HumiditySensorDatum):
        self.datum = datum
        self.sensors = datum.sensors
        self.readings = datum.recent_readings

    def sensor_status_distribution(self) -> Dict[str, int]:
        """Distribución de sensores por estado"""
        statuses = [decode_status(s.status)[0] for s in self.sensors]
        return dict(Counter(statuses))

    def alert_level_distribution(self) -> Dict[str, int]:
        """Distribución de lecturas por nivel de alerta"""
        alerts = [decode_alert_level(r.alert_level)[0] for r in self.readings]
        return dict(Counter(alerts))

    def humidity_stats(self) -> Dict[str, float]:
        """Estadísticas de humedad"""
        if not self.readings:
            return {"min": 0, "max": 0, "avg": 0}

        humidities = [r.humidity_percentage for r in self.readings]
        return {
            "min": min(humidities),
            "max": max(humidities),
            "avg": sum(humidities) / len(humidities)
        }

    def temperature_stats(self) -> Dict[str, float]:
        """Estadísticas de temperatura"""
        if not self.readings:
            return {"min": 0, "max": 0, "avg": 0}

        temps = [r.temperature_celsius for r in self.readings]
        return {
            "min": min(temps),
            "max": max(temps),
            "avg": sum(temps) / len(temps)
        }

    def readings_per_sensor(self) -> Dict[str, int]:
        """Cantidad de lecturas por sensor"""
        sensor_ids = [r.sensor_id.decode('utf-8', errors='ignore') for r in self.readings]
        return dict(Counter(sensor_ids))


# ========================================
# VISUALIZADORES
# ========================================

def display_overview(datum: HumiditySensorDatum, utxo_info: Dict):
    """Muestra resumen general del contrato"""
    print_section("RESUMEN DEL CONTRATO")

    print(f"  Contract Address:  {config.CONTRACT_ADDRESS}")
    print(f"  UTxO TxHash:       {utxo_info['tx_hash']}")
    print(f"  UTxO Balance:      {format_color(f'{utxo_info['balance']:.2f} ADA', Colors.GREEN, bold=True)}")
    print()
    print(f"  Admin PKH:         {datum.admin.hex()[:32]}...")
    print(f"  Last Updated:      {format_timestamp(datum.last_updated)}")
    print(f"  Total Sensors:     {format_color(str(datum.total_sensors), Colors.CYAN, bold=True)}")
    print(f"  Active Sensors:    {format_color(str(len(datum.sensors)), Colors.GREEN, bold=True)}")
    print(f"  Recent Readings:   {format_color(str(len(datum.recent_readings)), Colors.BLUE, bold=True)}")


def display_statistics(stats: DatumStats):
    """Muestra estadísticas calculadas"""
    print_section("ESTADISTICAS")

    # Distribución de estados
    print(f"  {format_color('Sensores por Estado:', Colors.BOLD)}")
    status_dist = stats.sensor_status_distribution()
    for status, count in status_dist.items():
        color = Colors.GREEN if status == "Active" else Colors.YELLOW
        print(f"    • {status:12s}: {format_color(str(count), color)}")

    print()

    # Distribución de alertas
    print(f"  {format_color('Lecturas por Nivel de Alerta:', Colors.BOLD)}")
    alert_dist = stats.alert_level_distribution()
    alert_colors = {
        "Normal": Colors.GREEN,
        "Low": Colors.YELLOW,
        "High": Colors.YELLOW,
        "Critical": Colors.RED
    }
    for alert, count in alert_dist.items():
        color = alert_colors.get(alert, Colors.WHITE)
        print(f"    • {alert:12s}: {format_color(str(count), color)}")

    print()

    # Estadísticas de humedad
    humidity_stats = stats.humidity_stats()
    print(f"  {format_color('Humedad:', Colors.BOLD)}")
    print(f"    • Mínima:    {humidity_stats['min']:.1f}%")
    print(f"    • Máxima:    {humidity_stats['max']:.1f}%")
    print(f"    • Promedio:  {format_color(f'{humidity_stats['avg']:.1f}%', Colors.CYAN)}")

    print()

    # Estadísticas de temperatura
    temp_stats = stats.temperature_stats()
    print(f"  {format_color('Temperatura:', Colors.BOLD)}")
    print(f"    • Mínima:    {temp_stats['min']:.1f}°C")
    print(f"    • Máxima:    {temp_stats['max']:.1f}°C")
    print(f"    • Promedio:  {format_color(f'{temp_stats['avg']:.1f}°C', Colors.CYAN)}")

    print()

    # Lecturas por sensor
    readings_per_sensor = stats.readings_per_sensor()
    if readings_per_sensor:
        print(f"  {format_color('Lecturas por Sensor:', Colors.BOLD)}")
        for sensor_id, count in readings_per_sensor.items():
            print(f"    • {sensor_id:15s}: {format_color(str(count), Colors.BLUE)}")


def display_sensors(sensors: List[SensorConfig], filter_sensor_id: Optional[str] = None):
    """Muestra detalles de todos los sensores"""
    print_section(f"SENSORES REGISTRADOS ({len(sensors)})")

    for i, sensor in enumerate(sensors, 1):
        sensor_id = sensor.sensor_id.decode('utf-8', errors='ignore')

        # Aplicar filtro si existe
        if filter_sensor_id and sensor_id != filter_sensor_id:
            continue

        zone_name = sensor.location.zone_name.decode('utf-8', errors='ignore')
        coords = format_coordinates(sensor.location.latitude, sensor.location.longitude)
        status_name, status_color = decode_status(sensor.status)
        installed = format_timestamp(sensor.installed_date)

        print()
        print(f"  {format_color(f'[{i}] {sensor_id}', Colors.CYAN, bold=True)}")
        print(f"      Ubicación:       {zone_name}")
        print(f"      Coordenadas:     {coords}")
        print(f"      Umbrales:        {sensor.min_humidity_threshold}% - {sensor.max_humidity_threshold}%")
        print(f"      Intervalo:       {sensor.reading_interval_minutes} minutos")
        print(f"      Estado:          {format_color(status_name, status_color)}")
        print(f"      Propietario:     {sensor.owner.hex()[:32]}...")
        print(f"      Instalado:       {installed}")


def display_readings(readings: List[HumidityReading], filter_sensor_id: Optional[str] = None):
    """Muestra detalles de todas las lecturas"""
    print_section(f"LECTURAS RECIENTES ({len(readings)})")

    if not readings:
        print(f"  {format_color('No hay lecturas registradas', Colors.YELLOW)}")
        return

    # Ordenar por timestamp (más reciente primero)
    sorted_readings = sorted(readings, key=lambda r: r.timestamp, reverse=True)

    for i, reading in enumerate(sorted_readings, 1):
        sensor_id = reading.sensor_id.decode('utf-8', errors='ignore')

        # Aplicar filtro si existe
        if filter_sensor_id and sensor_id != filter_sensor_id:
            continue

        timestamp = format_timestamp(reading.timestamp)
        alert_name, alert_color, alert_icon = decode_alert_level(reading.alert_level)

        print()
        print(f"  {format_color(f'[{i}] {sensor_id}', Colors.CYAN, bold=True)} @ {timestamp}")
        print(f"      Humedad:         {format_percentage(reading.humidity_percentage, 0, 100)}")
        print(f"      Temperatura:     {format_color(f'{reading.temperature_celsius}°C', Colors.BLUE)}")
        print(f"      Alerta:          {alert_icon} {format_color(alert_name, alert_color, bold=True)}")


# ========================================
# EXPORTACIÓN
# ========================================

def export_to_json(datum: HumiditySensorDatum, filename: str):
    """Exporta el datum completo a JSON"""

    def serialize_sensor(sensor: SensorConfig) -> dict:
        status_name, _ = decode_status(sensor.status)
        return {
            "sensor_id": sensor.sensor_id.decode('utf-8', errors='ignore'),
            "location": {
                "latitude": sensor.location.latitude / 1_000_000,
                "longitude": sensor.location.longitude / 1_000_000,
                "zone_name": sensor.location.zone_name.decode('utf-8', errors='ignore')
            },
            "min_humidity_threshold": sensor.min_humidity_threshold,
            "max_humidity_threshold": sensor.max_humidity_threshold,
            "reading_interval_minutes": sensor.reading_interval_minutes,
            "status": status_name,
            "owner": sensor.owner.hex(),
            "installed_date": format_timestamp(sensor.installed_date)
        }

    def serialize_reading(reading: HumidityReading) -> dict:
        alert_name, _, _ = decode_alert_level(reading.alert_level)
        return {
            "sensor_id": reading.sensor_id.decode('utf-8', errors='ignore'),
            "humidity_percentage": reading.humidity_percentage,
            "temperature_celsius": reading.temperature_celsius,
            "timestamp": format_timestamp(reading.timestamp),
            "alert_level": alert_name
        }

    data = {
        "contract_address": config.CONTRACT_ADDRESS,
        "admin": datum.admin.hex(),
        "last_updated": format_timestamp(datum.last_updated),
        "total_sensors": datum.total_sensors,
        "sensors": [serialize_sensor(s) for s in datum.sensors],
        "recent_readings": [serialize_reading(r) for r in datum.recent_readings]
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Datos exportados a: {filename}")


def export_readings_to_csv(readings: List[HumidityReading], filename: str):
    """Exporta las lecturas a CSV"""

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Sensor ID', 'Timestamp', 'Humidity %', 'Temperature °C', 'Alert Level'])

        for reading in readings:
            sensor_id = reading.sensor_id.decode('utf-8', errors='ignore')
            timestamp = format_timestamp(reading.timestamp)
            alert_name, _, _ = decode_alert_level(reading.alert_level)

            writer.writerow([
                sensor_id,
                timestamp,
                reading.humidity_percentage,
                reading.temperature_celsius,
                alert_name
            ])

    print(f"[OK] Lecturas exportadas a: {filename}")


# ========================================
# MAIN
# ========================================

def main():
    parser = argparse.ArgumentParser(
        description='Decodifica y visualiza el datum del contrato de sensores de humedad',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python decode_datum_enhanced.py                    # Vista completa
  python decode_datum_enhanced.py --sensor SENSOR_001  # Filtrar por sensor
  python decode_datum_enhanced.py --stats-only       # Solo estadísticas
  python decode_datum_enhanced.py --export-json data.json  # Exportar a JSON
  python decode_datum_enhanced.py --export-csv readings.csv # Exportar lecturas a CSV
        """
    )

    parser.add_argument('--sensor', '-s', type=str, help='Filtrar por ID de sensor')
    parser.add_argument('--stats-only', action='store_true', help='Mostrar solo estadísticas')
    parser.add_argument('--sensors-only', action='store_true', help='Mostrar solo sensores')
    parser.add_argument('--readings-only', action='store_true', help='Mostrar solo lecturas')
    parser.add_argument('--export-json', type=str, metavar='FILE', help='Exportar datum completo a JSON')
    parser.add_argument('--export-csv', type=str, metavar='FILE', help='Exportar lecturas a CSV')
    parser.add_argument('--no-color', action='store_true', help='Desactivar colores')

    args = parser.parse_args()

    # Desactivar colores si se solicita
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')

    print_header("DECODIFICADOR DE DATUM - Sistema de Sensores de Humedad", 80)

    try:
        # 1. Obtener UTxOs del contrato
        print("[+] Consultando UTxOs del contrato...")
        utxos = cu.get_contract_utxos()

        # 2. Buscar el UTxO con datum inline
        datum_utxo = None
        for utxo in utxos:
            if hasattr(utxo, 'inline_datum') and utxo.inline_datum:
                datum_utxo = utxo
                break

        if not datum_utxo:
            print(format_color("[ERROR] No se encontró ningún UTxO con datum inline", Colors.RED))
            return

        print(format_color("[OK] UTxO encontrado", Colors.GREEN))

        # 3. Decodificar datum
        print("[+] Decodificando datum CBOR...")

        import cbor2
        datum_bytes = bytes.fromhex(datum_utxo.inline_datum)
        decoded_cbor = cbor2.loads(datum_bytes)

        # Parsear como HumiditySensorDatum
        datum = HumiditySensorDatum.from_primitive(decoded_cbor)

        print(format_color("[OK] Datum decodificado exitosamente", Colors.GREEN))

        # 4. Información del UTxO
        utxo_info = {
            'tx_hash': str(datum_utxo.tx_hash)[:64],
            'balance': int(datum_utxo.amount[0].quantity) / 1_000_000
        }

        # 5. Calcular estadísticas
        stats = DatumStats(datum)

        # 6. Mostrar información según argumentos
        if args.stats_only:
            display_statistics(stats)
        elif args.sensors_only:
            display_sensors(datum.sensors, args.sensor)
        elif args.readings_only:
            display_readings(datum.recent_readings, args.sensor)
        else:
            # Mostrar todo
            display_overview(datum, utxo_info)
            display_statistics(stats)
            display_sensors(datum.sensors, args.sensor)
            display_readings(datum.recent_readings, args.sensor)

        # 7. Exportación
        if args.export_json:
            export_to_json(datum, args.export_json)

        if args.export_csv:
            export_readings_to_csv(datum.recent_readings, args.export_csv)

        print()
        print("=" * 80)
        print()

        # 8. Enlace al explorer
        print(f"Ver en Cardano Explorer:")
        print(f"  https://preview.cardanoscan.io/address/{config.CONTRACT_ADDRESS}")
        print()

    except Exception as e:
        print()
        print(format_color(f"[ERROR] {e}", Colors.RED, bold=True))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
