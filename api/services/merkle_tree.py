"""
Servicio de Merkle Tree para crear hashes criptográficos de lecturas
Permite verificar la integridad de batches de lecturas sin almacenar todos los datos en blockchain
"""
import hashlib
from typing import List, Dict, Tuple
from datetime import datetime


class MerkleTree:
    """
    Implementación de Merkle Tree para verificar integridad de lecturas
    """

    def __init__(self, data: List[Dict]):
        """
        Inicializa el árbol merkle con una lista de lecturas

        Args:
            data: Lista de diccionarios con datos de lecturas
        """
        self.leaves = [self._hash_reading(reading) for reading in data]
        self.tree = self._build_tree(self.leaves)
        self.root = self.tree[-1][0] if self.tree else None

    def _hash_reading(self, reading: Dict) -> str:
        """
        Crea un hash SHA-256 de una lectura individual

        Args:
            reading: Diccionario con sensor_id, humidity, temperature, timestamp

        Returns:
            Hash hexadecimal de 64 caracteres
        """
        # Crear string canónico de la lectura
        reading_str = f"{reading['sensor_id']}|{reading['humidity']}|{reading['temperature']}|{reading['timestamp']}"
        return hashlib.sha256(reading_str.encode()).hexdigest()

    def _hash_pair(self, left: str, right: str = None) -> str:
        """
        Hashea un par de nodos (o un nodo solo si es impar)

        Args:
            left: Hash del nodo izquierdo
            right: Hash del nodo derecho (opcional)

        Returns:
            Hash combinado
        """
        if right is None:
            # Si no hay par, duplicar el nodo (estándar en merkle trees)
            right = left

        combined = left + right
        return hashlib.sha256(combined.encode()).hexdigest()

    def _build_tree(self, leaves: List[str]) -> List[List[str]]:
        """
        Construye el árbol merkle completo desde las hojas hasta la raíz

        Args:
            leaves: Lista de hashes de las lecturas

        Returns:
            Lista de niveles del árbol, donde tree[-1][0] es la raíz
        """
        if not leaves:
            return []

        tree = [leaves]
        current_level = leaves

        # Construir niveles hasta llegar a la raíz
        while len(current_level) > 1:
            next_level = []

            # Procesar pares de nodos
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else None
                parent = self._hash_pair(left, right)
                next_level.append(parent)

            tree.append(next_level)
            current_level = next_level

        return tree

    def get_root(self) -> str:
        """
        Obtiene el hash raíz del árbol

        Returns:
            Hash raíz de 64 caracteres hexadecimales
        """
        return self.root

    def get_proof(self, index: int) -> List[Tuple[str, str]]:
        """
        Genera una prueba merkle para verificar una lectura específica

        Args:
            index: Índice de la lectura en la lista original

        Returns:
            Lista de tuplas (hash, posición) donde posición es 'left' o 'right'
        """
        if index < 0 or index >= len(self.leaves):
            raise ValueError(f"Índice {index} fuera de rango")

        proof = []
        current_index = index

        # Recorrer cada nivel del árbol
        for level in self.tree[:-1]:  # Excluir el nivel raíz
            # Determinar el índice del hermano
            if current_index % 2 == 0:
                # Nodo izquierdo, hermano está a la derecha
                sibling_index = current_index + 1
                position = 'right'
            else:
                # Nodo derecho, hermano está a la izquierda
                sibling_index = current_index - 1
                position = 'left'

            # Agregar hash del hermano si existe
            if sibling_index < len(level):
                proof.append((level[sibling_index], position))
            else:
                # No hay hermano (número impar de nodos), usar el mismo nodo
                proof.append((level[current_index], position))

            # Subir al siguiente nivel
            current_index = current_index // 2

        return proof

    @staticmethod
    def verify_proof(leaf_hash: str, proof: List[Tuple[str, str]], root: str) -> bool:
        """
        Verifica que una lectura pertenece al árbol usando su prueba merkle

        Args:
            leaf_hash: Hash de la lectura a verificar
            proof: Prueba merkle (lista de tuplas hash, posición)
            root: Hash raíz esperado

        Returns:
            True si la prueba es válida, False en caso contrario
        """
        current_hash = leaf_hash

        # Reconstruir el camino hacia la raíz
        for sibling_hash, position in proof:
            if position == 'left':
                combined = sibling_hash + current_hash
            else:
                combined = current_hash + sibling_hash

            current_hash = hashlib.sha256(combined.encode()).hexdigest()

        # Verificar que llegamos a la raíz correcta
        return current_hash == root

    def get_tree_info(self) -> Dict:
        """
        Obtiene información del árbol para debugging

        Returns:
            Diccionario con información del árbol
        """
        return {
            "num_leaves": len(self.leaves),
            "tree_height": len(self.tree),
            "root_hash": self.root,
            "leaves_sample": self.leaves[:3] if len(self.leaves) > 3 else self.leaves
        }


def create_rollup_merkle(readings: List[Dict]) -> Dict:
    """
    Función helper para crear un rollup con merkle tree

    Args:
        readings: Lista de lecturas del día

    Returns:
        Diccionario con root hash, estadísticas y metadata
    """
    if not readings:
        raise ValueError("No hay lecturas para crear rollup")

    # Crear merkle tree
    tree = MerkleTree(readings)

    # Calcular estadísticas
    humidities = [r['humidity'] for r in readings]
    temperatures = [r['temperature'] for r in readings]

    return {
        "merkle_root": tree.get_root(),
        "readings_count": len(readings),
        "sensor_id": readings[0]['sensor_id'],
        "date": readings[0]['timestamp'].split('T')[0],
        "statistics": {
            "humidity_min": min(humidities),
            "humidity_max": max(humidities),
            "humidity_avg": sum(humidities) / len(humidities),
            "temperature_min": min(temperatures),
            "temperature_max": max(temperatures),
            "temperature_avg": sum(temperatures) / len(temperatures)
        },
        "first_reading": readings[0]['timestamp'],
        "last_reading": readings[-1]['timestamp']
    }
