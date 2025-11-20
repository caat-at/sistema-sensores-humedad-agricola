"""
Script de Auditoria V2: Blockchain vs PostgreSQL
Matching inteligente por timestamp con tolerancia
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent / "pycardano-client"))
sys.path.insert(0, str(Path(__file__).parent / "api"))

from api.services.blockchain_service import BlockchainService
from api.database.connection import SessionLocal
from api.database.models import ReadingHistory


class DataIntegrityAuditorV2:
    """Audita integridad con matching inteligente por timestamp"""

    def __init__(self):
        self.blockchain = BlockchainService()
        self.db = SessionLocal()
        self.discrepancias = []
        self.coincidencias_detalle = []

    def obtener_lecturas_blockchain(self) -> List[Dict]:
        """Obtiene todas las lecturas desde el blockchain"""
        print("\n[1/4] Obteniendo lecturas desde Blockchain...")
        print("=" * 70)

        try:
            readings = self.blockchain.get_all_readings()

            lecturas_blockchain = []
            for r in readings:
                lectura = {
                    'sensor_id': r.sensor_id.decode('utf-8', errors='ignore'),
                    'humidity_percentage': r.humidity_percentage,
                    'temperature_celsius': r.temperature_celsius,
                    'timestamp': datetime.fromtimestamp(r.timestamp / 1000),
                    'alert_level': type(r.alert_level).__name__,
                    'source': 'blockchain'
                }
                lecturas_blockchain.append(lectura)

            print(f"[OK] {len(lecturas_blockchain)} lecturas en blockchain")
            return lecturas_blockchain

        except Exception as e:
            print(f"[ERROR] {e}")
            return []

    def obtener_lecturas_postgresql(self) -> List[Dict]:
        """Obtiene todas las lecturas desde PostgreSQL"""
        print("\n[2/4] Obteniendo lecturas desde PostgreSQL...")
        print("=" * 70)

        try:
            db_readings = self.db.query(ReadingHistory).order_by(
                ReadingHistory.timestamp.desc()
            ).all()

            lecturas_db = []
            for r in db_readings:
                lectura = {
                    'sensor_id': r.sensor_id,
                    'humidity_percentage': r.humidity_percentage,
                    'temperature_celsius': r.temperature_celsius,
                    'timestamp': r.timestamp,
                    'tx_hash': r.tx_hash,
                    'on_chain': r.on_chain,
                    'source': 'postgresql'
                }
                lecturas_db.append(lectura)

            print(f"[OK] {len(lecturas_db)} lecturas en PostgreSQL")
            return lecturas_db

        except Exception as e:
            print(f"[ERROR] {e}")
            return []

    def encontrar_match(self, lectura_bc: Dict, lecturas_db: List[Dict], tolerancia_segundos: int = 5) -> Dict:
        """
        Busca una lectura en PostgreSQL que coincida con una de blockchain
        Tolerancia: diferencia máxima en segundos
        """
        mejor_match = None
        menor_diferencia = timedelta(seconds=999999)

        for lectura_db in lecturas_db:
            # Mismo sensor
            if lectura_bc['sensor_id'] != lectura_db['sensor_id']:
                continue

            # Calcular diferencia de tiempo
            diff = abs(lectura_bc['timestamp'] - lectura_db['timestamp'])

            # Si está dentro de la tolerancia y es el más cercano
            if diff <= timedelta(seconds=tolerancia_segundos) and diff < menor_diferencia:
                menor_diferencia = diff
                mejor_match = lectura_db

        return mejor_match

    def comparar_lecturas(self, blockchain_data: List[Dict], db_data: List[Dict]):
        """Compara con matching inteligente por timestamp"""
        print("\n[3/4] Comparando con matching inteligente...")
        print("=" * 70)

        print(f"\nTotal Blockchain:  {len(blockchain_data)}")
        print(f"Total PostgreSQL:  {len(db_data)}")
        print(f"Tolerancia:        ±5 segundos\n")

        coincidencias = 0
        discrepancias_valores = 0
        sin_match_bc = 0
        sin_match_db = list(db_data)  # Copiar lista

        # Para cada lectura blockchain, buscar match en PostgreSQL
        for bc_reading in blockchain_data:
            match = self.encontrar_match(bc_reading, sin_match_db)

            if match:
                # Encontró match, verificar si los valores coinciden
                if (bc_reading['humidity_percentage'] == match['humidity_percentage'] and
                    bc_reading['temperature_celsius'] == match['temperature_celsius']):
                    coincidencias += 1
                    self.coincidencias_detalle.append({
                        'sensor_id': bc_reading['sensor_id'],
                        'timestamp_bc': bc_reading['timestamp'],
                        'timestamp_db': match['timestamp'],
                        'diff_segundos': abs(bc_reading['timestamp'] - match['timestamp']).total_seconds(),
                        'tx_hash': match.get('tx_hash', 'N/A')
                    })
                else:
                    discrepancias_valores += 1
                    self.discrepancias.append({
                        'tipo': 'VALORES_DIFERENTES',
                        'sensor_id': bc_reading['sensor_id'],
                        'timestamp_bc': bc_reading['timestamp'],
                        'timestamp_db': match['timestamp'],
                        'diff_segundos': abs(bc_reading['timestamp'] - match['timestamp']).total_seconds(),
                        'blockchain': f"H:{bc_reading['humidity_percentage']}% T:{bc_reading['temperature_celsius']}°C",
                        'postgresql': f"H:{match['humidity_percentage']}% T:{match['temperature_celsius']}°C",
                        'tx_hash': match.get('tx_hash', 'N/A')
                    })

                # Remover de la lista para no reusar
                sin_match_db.remove(match)

            else:
                # No encontró match en PostgreSQL
                sin_match_bc += 1
                self.discrepancias.append({
                    'tipo': 'SOLO_EN_BLOCKCHAIN',
                    'sensor_id': bc_reading['sensor_id'],
                    'timestamp': bc_reading['timestamp'],
                    'datos': f"H:{bc_reading['humidity_percentage']}% T:{bc_reading['temperature_celsius']}°C"
                })

        # Lecturas que quedaron sin match en PostgreSQL
        sin_match_postgresql = len(sin_match_db)

        for db_reading in sin_match_db:
            self.discrepancias.append({
                'tipo': 'SOLO_EN_POSTGRESQL',
                'sensor_id': db_reading['sensor_id'],
                'timestamp': db_reading['timestamp'],
                'datos': f"H:{db_reading['humidity_percentage']}% T:{db_reading['temperature_celsius']}°C",
                'tx_hash': db_reading.get('tx_hash', 'N/A'),
                'on_chain': db_reading.get('on_chain', False)
            })

        return {
            'total_blockchain': len(blockchain_data),
            'total_postgresql': len(db_data),
            'coincidencias': coincidencias,
            'discrepancias_valores': discrepancias_valores,
            'solo_blockchain': sin_match_bc,
            'solo_postgresql': sin_match_postgresql
        }

    def generar_reporte(self, stats: Dict):
        """Genera reporte detallado"""
        print("\n[4/4] Generando Reporte...")
        print("=" * 70)

        # Calcular integridad
        total_con_match = stats['coincidencias'] + stats['discrepancias_valores']
        if total_con_match > 0:
            integridad = (stats['coincidencias'] / total_con_match) * 100
        else:
            integridad = 0

        print("\n" + "=" * 70)
        print("           REPORTE DE AUDITORIA V2")
        print("      Matching Inteligente por Timestamp")
        print("=" * 70)
        print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print("\n--- RESUMEN ---")
        print(f"  Blockchain:                    {stats['total_blockchain']:>6}")
        print(f"  PostgreSQL:                    {stats['total_postgresql']:>6}")
        print(f"  Coincidencias perfectas:       {stats['coincidencias']:>6}")
        print(f"  Valores diferentes:            {stats['discrepancias_valores']:>6}")
        print(f"  Solo en Blockchain:            {stats['solo_blockchain']:>6}")
        print(f"  Solo en PostgreSQL:            {stats['solo_postgresql']:>6}")

        print(f"\n--- INTEGRIDAD ---")
        if integridad >= 99:
            estado = "[EXCELENTE]"
            emoji = "✓✓✓"
        elif integridad >= 95:
            estado = "[MUY BUENO]"
            emoji = "✓✓"
        elif integridad >= 90:
            estado = "[BUENO]"
            emoji = "✓"
        elif integridad >= 80:
            estado = "[ACEPTABLE]"
            emoji = "~"
        else:
            estado = "[CRITICO]"
            emoji = "✗"

        print(f"  {emoji} {integridad:.2f}% {estado}")
        print(f"  ({stats['coincidencias']} de {total_con_match} lecturas coinciden)")

        # Análisis de diferencias temporales
        if len(self.coincidencias_detalle) > 0:
            diffs = [c['diff_segundos'] for c in self.coincidencias_detalle]
            print(f"\n--- ANÁLISIS TEMPORAL DE COINCIDENCIAS ---")
            print(f"  Diferencia promedio:  {sum(diffs)/len(diffs):.2f} segundos")
            print(f"  Diferencia máxima:    {max(diffs):.2f} segundos")
            print(f"  Diferencia mínima:    {min(diffs):.2f} segundos")

        # Discrepancias
        if len(self.discrepancias) > 0:
            print(f"\n--- DISCREPANCIAS ENCONTRADAS ({len(self.discrepancias)}) ---")

            # Contar por tipo
            tipos = {}
            for d in self.discrepancias:
                tipo = d['tipo']
                tipos[tipo] = tipos.get(tipo, 0) + 1

            # Separar por tipo para mostrar en orden de importancia
            valores_dif = [d for d in self.discrepancias if d['tipo'] == 'VALORES_DIFERENTES']
            solo_bc = [d for d in self.discrepancias if d['tipo'] == 'SOLO_EN_BLOCKCHAIN']
            solo_db = [d for d in self.discrepancias if d['tipo'] == 'SOLO_EN_POSTGRESQL']

            print(f"\nTotales por tipo:")
            for tipo, count in tipos.items():
                print(f"  {tipo}: {count}")

            # PRIORIDAD 1: Mostrar VALORES_DIFERENTES (las más críticas)
            if valores_dif:
                print(f"\n{'='*70}")
                print(f"VALORES DIFERENTES ({len(valores_dif)} encontrados)")
                print(f"{'='*70}")
                for i, disc in enumerate(valores_dif, 1):
                    print(f"\n  [{i}] Tipo: VALORES_DIFERENTES")
                    print(f"      Sensor: {disc['sensor_id']}")
                    print(f"      Timestamp BC: {disc['timestamp_bc']}")
                    print(f"      Timestamp DB: {disc['timestamp_db']}")
                    print(f"      Blockchain: {disc['blockchain']}")
                    print(f"      PostgreSQL: {disc['postgresql']}")
                    print(f"      TX Hash: {disc['tx_hash']}")

            # PRIORIDAD 2: Mostrar SOLO_EN_BLOCKCHAIN (resumido)
            if solo_bc:
                print(f"\n{'='*70}")
                print(f"SOLO EN BLOCKCHAIN ({len(solo_bc)} lecturas)")
                print(f"{'='*70}")
                print("(Lecturas antiguas sin registro en PostgreSQL)")

                for i, disc in enumerate(solo_bc[:10], 1):
                    print(f"\n  [{i}] Tipo: SOLO_EN_BLOCKCHAIN")
                    print(f"      Sensor: {disc['sensor_id']}")
                    print(f"      Timestamp: {disc['timestamp']}")
                    print(f"      Datos: {disc['datos']}")

                if len(solo_bc) > 10:
                    print(f"\n  ... y {len(solo_bc) - 10} lecturas más")

            # PRIORIDAD 3: Mostrar SOLO_EN_POSTGRESQL (resumido)
            if solo_db:
                print(f"\n{'='*70}")
                print(f"SOLO EN POSTGRESQL ({len(solo_db)} lecturas)")
                print(f"{'='*70}")
                print("(Lecturas en DB sin match temporal en blockchain)")

                for i, disc in enumerate(solo_db[:10], 1):
                    on_chain_str = "SI" if disc.get('on_chain') else "NO (archivada)"
                    print(f"\n  [{i}] Tipo: SOLO_EN_POSTGRESQL")
                    print(f"      Sensor: {disc['sensor_id']}")
                    print(f"      Timestamp: {disc['timestamp']}")
                    print(f"      Datos: {disc['datos']}")
                    print(f"      TX Hash: {disc.get('tx_hash', 'N/A')}")
                    print(f"      On-chain: {on_chain_str}")

                if len(solo_db) > 10:
                    print(f"\n  ... y {len(solo_db) - 10} lecturas más")

        else:
            print("\n--- SIN DISCREPANCIAS ---")
            print("  ✓✓✓ Integridad perfecta - Todos los datos coinciden!")

        print("\n" + "=" * 70)

        # Guardar reporte
        self.guardar_reporte(stats, integridad)

    def guardar_reporte(self, stats: Dict, integridad: float):
        """Guarda reporte en archivo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"audit_report_v2_{timestamp}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("REPORTE DE AUDITORIA V2\n")
                f.write("Matching Inteligente por Timestamp\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Fecha: {datetime.now()}\n")
                f.write(f"Blockchain:         {stats['total_blockchain']}\n")
                f.write(f"PostgreSQL:         {stats['total_postgresql']}\n")
                f.write(f"Coincidencias:      {stats['coincidencias']}\n")
                f.write(f"Valores diferentes: {stats['discrepancias_valores']}\n")
                f.write(f"Solo Blockchain:    {stats['solo_blockchain']}\n")
                f.write(f"Solo PostgreSQL:    {stats['solo_postgresql']}\n")
                f.write(f"\nIntegridad: {integridad:.2f}%\n")

                # Detalles de coincidencias
                if self.coincidencias_detalle:
                    f.write(f"\n--- COINCIDENCIAS ({len(self.coincidencias_detalle)}) ---\n")
                    for c in self.coincidencias_detalle:
                        f.write(f"\nSensor: {c['sensor_id']}\n")
                        f.write(f"  Timestamp BC: {c['timestamp_bc']}\n")
                        f.write(f"  Timestamp DB: {c['timestamp_db']}\n")
                        f.write(f"  Diferencia:   {c['diff_segundos']:.2f}s\n")
                        f.write(f"  TX Hash:      {c['tx_hash']}\n")

                # Discrepancias completas
                if self.discrepancias:
                    f.write(f"\n--- DISCREPANCIAS ({len(self.discrepancias)}) ---\n")
                    for i, d in enumerate(self.discrepancias, 1):
                        f.write(f"\n[{i}] {d['tipo']}\n")
                        f.write(f"    Sensor: {d['sensor_id']}\n")
                        if 'timestamp_bc' in d:
                            f.write(f"    BC Time: {d['timestamp_bc']}\n")
                            f.write(f"    DB Time: {d['timestamp_db']}\n")
                            f.write(f"    Diff: {d['diff_segundos']:.2f}s\n")
                            f.write(f"    BC: {d['blockchain']}\n")
                            f.write(f"    DB: {d['postgresql']}\n")
                        else:
                            f.write(f"    Time: {d['timestamp']}\n")
                            f.write(f"    Data: {d['datos']}\n")

            print(f"\n[OK] Reporte guardado: {filename}")

        except Exception as e:
            print(f"[WARN] Error guardando reporte: {e}")

    def ejecutar_auditoria(self):
        """Ejecuta auditoria completa"""
        print("\n" + "=" * 70)
        print("    AUDITORIA DE INTEGRIDAD V2")
        print("    Matching Inteligente por Timestamp")
        print("=" * 70)

        # Obtener datos
        blockchain_data = self.obtener_lecturas_blockchain()
        db_data = self.obtener_lecturas_postgresql()

        if not blockchain_data and not db_data:
            print("\n[ERROR] No hay datos")
            return

        # Comparar
        stats = self.comparar_lecturas(blockchain_data, db_data)

        # Reporte
        self.generar_reporte(stats)

        # Cerrar DB
        self.db.close()


if __name__ == "__main__":
    try:
        auditor = DataIntegrityAuditorV2()
        auditor.ejecutar_auditoria()

    except KeyboardInterrupt:
        print("\n\n[!] Interrumpido")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
