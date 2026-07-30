import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path

# Carga condicional/defensiva de chromadb
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


def generar_id_oferta(url: str, titulo: str = "", empresa: str = "") -> str:
    """
    Genera un hash SHA-256 único y determinista de 32 caracteres para identificar una oferta.
    """
    identificador = f"{url.strip().lower()}|{titulo.strip().lower()}|{empresa.strip().lower()}"
    return hashlib.sha256(identificador.encode("utf-8")).hexdigest()[:32]


class VectorDBManager:
    """
    REQUERIMIENTO 1: Administrador de la Base de Datos Vectorial ChromaDB Embebida.
    Almacena vectores generados en CPU por intfloat/multilingual-e5-small y proporciona
    caché semántica anti-reprocesamiento en disco trabajando en conjunto con SQLite.
    """
    def __init__(self, db_dir: str = "database/chroma_data", collection_name: str = "ofertas_laborales"):
        self.db_dir = Path(db_dir).resolve()
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._init_db()

    def _init_db(self):
        """Inicializa el cliente de ChromaDB persistente en disco y obtiene/crea la colección con espacio cosenoidal."""
        if not CHROMADB_AVAILABLE:
            return
        
        try:
            self.client = chromadb.PersistentClient(path=str(self.db_dir))
            # HNSW space cosine => distancia = 1 - similitud_cosenoidal
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"Advertencia al inicializar ChromaDB: {e}")

    def existe_oferta(self, url_id: str) -> bool:
        """Verifica en tiempo O(1) si la oferta ya fue indexada en la colección de ChromaDB."""
        if not self.collection:
            return False
        try:
            res = self.collection.get(ids=[url_id])
            return bool(res and res.get("ids"))
        except Exception:
            return False

    def indexar_oferta(
        self,
        url_id: str,
        texto_oferta: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        REQUERIMIENTO 2: Registra una nueva oferta con su embedding en ChromaDB si no existe previa (Caché Semántica).
        
        Args:
            url_id: Identificador hash único de la oferta.
            texto_oferta: Descripción completa o resumen de la oferta.
            embedding: Vector numérico generado por intfloat/multilingual-e5-small en CPU.
            metadata: Diccionario con portal, título, empresa, fecha, etc.
            
        Returns:
            bool: True si se indexó correctamente, False si se omitió (ya existía) o falló.
        """
        if not self.collection:
            return False

        if self.existe_oferta(url_id):
            # Caché semántica: ya está en disco, omitir cálculo/inserción
            return False

        try:
            # Limpiar metadatos (ChromaDB solo acepta int, float, str, bool en metadatos)
            clean_meta = {}
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)

            self.collection.add(
                ids=[url_id],
                documents=[texto_oferta],
                embeddings=[embedding],
                metadatas=[clean_meta]
            )
            return True
        except Exception as e:
            print(f"Error al indexar oferta en ChromaDB: {e}")
            return False

    def buscar_similares(
        self,
        embedding_cv_query: List[float],
        umbral: float = 0.649,
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        REQUERIMIENTO 2: Consulta ChromaDB usando el embedding de la consulta/CV ('query:').
        Convierte la distancia cosenoidal de Chroma (distancia = 1 - similitud) a similitud cosenoidal
        y retorna únicamente las ofertas con similitud >= umbral.

        Args:
            embedding_cv_query: Vector embedding del CV generado con prefijo 'query:'.
            umbral: Umbral de similitud mínima (ej. 0.649).
            top_k: Cantidad máxima de vecinos más cercanos a consultar.

        Returns:
            List[Dict]: Lista de ofertas compatibles con sus metadatos y score de similitud.
        """
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_embeddings=[embedding_cv_query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            ofertas_similares = []
            if not results or not results.get("ids") or not results["ids"][0]:
                return []

            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for i in range(len(ids)):
                dist = distances[i]
                # En espacio 'cosine' de Chroma: distancia = 1 - similitud_cosenoidal
                similitud = 1.0 - dist

                if similitud >= umbral:
                    item = dict(metas[i])
                    item["id"] = ids[i]
                    item["descripcion"] = docs[i]
                    item["similitud_semantica"] = round(similitud, 4)
                    ofertas_similares.append(item)

            # Ordenar descendentemente por similitud
            ofertas_similares.sort(key=lambda x: x["similitud_semantica"], reverse=True)
            return ofertas_similares
        except Exception as e:
            print(f"Error al consultar ChromaDB: {e}")
            return []
