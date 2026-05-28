# -*- coding: utf-8 -*-
"""
StreamMind — Advanced RAG System (Fase 2: Memoria Contextual Mejorada)
=======================================================================
Sistema RAG profesional con:
- Embeddings de Hugging Face (sentence-transformers)
- Vector store FAISS para búsqueda rápida
- Persistencia (guardar/cargar índices)
- Recuperación contextual inteligente

Uso:
    from stream_rag_advanced import AdvancedStreamRAG
    
    rag = AdvancedStreamRAG()
    rag.add_documents(["mensaje 1", "mensaje 2", ...])
    context = rag.retrieve_context("query", top_k=3)
"""

import numpy as np
import faiss
import pickle
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import threading

# ─── Configuración ───────────────────────────────────────────────────────────

class AdvancedStreamRAG:
    """
    Sistema RAG avanzado con FAISS + sentence-transformers
    
    Características:
    - Embeddings semánticos de alta calidad
    - Búsqueda vectorial rápida (FAISS)
    - Persistencia automática
    - Thread-safe
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/distiluse-base-multilingual-cased-v2",
        index_dir: str = "data/rag_indexes",
        max_documents: int = 10000,
        dimension: int = 512
    ):
        """
        Inicializa el sistema RAG.
        
        Args:
            model_name: Modelo de embeddings (multiidioma, rápido)
            index_dir: Directorio para guardar índices
            max_documents: Máximo de documentos en memoria
            dimension: Dimensión de los embeddings
        """
        self.model_name = model_name
        self.index_dir = index_dir
        self.max_documents = max_documents
        self.dimension = dimension
        
        # Crear directorio si no existe
        os.makedirs(index_dir, exist_ok=True)
        
        # Cargar modelo de embeddings
        print(f"[*] Cargando modelo de embeddings: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        print(f"[✓] Modelo cargado (dimensión: {dimension})\n")
        
        # FAISS index
        self.index = None
        self.index_name = "stream_context_index"
        
        # Almacenamiento de documentos
        self.documents = []  # Lista de textos
        self.metadata = []   # Lista de metadatos
        self.document_ids = []  # IDs únicos
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Stats
        self.total_embedded = 0
        self.last_update = None
        
        # Intentar cargar índice existente
        self.load_index()

    def _create_index(self):
        """Crea nuevo índice FAISS"""
        self.index = faiss.IndexFlatL2(self.dimension)
        print(f"[✓] Nuevo índice FAISS creado (L2 distance)")

    def add_document(self, text: str, metadata: Optional[Dict] = None, doc_id: Optional[str] = None):
        """
        Añade un documento único.
        
        Args:
            text: Texto del documento
            metadata: Dict con info adicional (channel, username, timestamp, etc)
            doc_id: ID único del documento
        """
        if not text or len(text.strip()) == 0:
            return False
        
        with self.lock:
            # Generar ID si no se proporciona
            if doc_id is None:
                doc_id = f"doc_{len(self.documents)}_{datetime.now().timestamp()}"
            
            # Evitar duplicados exactos
            if text in self.documents:
                return False
            
            # Limitar documentos
            if len(self.documents) >= self.max_documents:
                # Remover el más antiguo (FIFO)
                self.documents.pop(0)
                self.metadata.pop(0)
                self.document_ids.pop(0)
                # Reconstruir índice
                self._rebuild_index()
            
            # Generar embedding
            embedding = self.embedding_model.encode(text, convert_to_numpy=True).astype(np.float32)
            
            # Añadir al índice
            if self.index is None:
                self._create_index()
            
            self.index.add(np.array([embedding]))
            
            # Guardar documento y metadata
            self.documents.append(text)
            self.document_ids.append(doc_id)
            
            if metadata is None:
                metadata = {}
            metadata["timestamp"] = datetime.now().isoformat()
            metadata["doc_id"] = doc_id
            self.metadata.append(metadata)
            
            self.total_embedded += 1
            self.last_update = datetime.now()
            
            return True

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        """
        Añade múltiples documentos.
        
        Args:
            texts: Lista de textos
            metadatas: Lista de dicts con metadata (opcional)
        """
        if metadatas is None:
            metadatas = [None] * len(texts)
        
        count = 0
        for text, metadata in zip(texts, metadatas):
            if self.add_document(text, metadata):
                count += 1
        
        print(f"[✓] {count}/{len(texts)} documentos añadidos")
        return count

    def retrieve_context(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.5,
        include_metadata: bool = True
    ) -> str | Dict:
        """
        Recupera documentos más relevantes.
        
        Args:
            query: Texto de búsqueda
            top_k: Número de resultados
            threshold: Score mínimo de similitud (0-1)
            include_metadata: Incluir metadata en respuesta
        
        Returns:
            str: Contexto combinado (por defecto)
            Dict: Contexto + metadata si include_metadata=True
        """
        if not self.documents or self.index is None:
            return "" if not include_metadata else {"context": "", "results": []}
        
        with self.lock:
            # Generar embedding de la query
            query_embedding = self.embedding_model.encode(query, convert_to_numpy=True).astype(np.float32)
            
            # Búsqueda en FAISS (retorna distancias L2)
            distances, indices = self.index.search(np.array([query_embedding]), top_k)
            
            # Convertir distancias L2 a similitud (0-1)
            # Similitud = 1 / (1 + distancia)
            results = []
            context_parts = []
            
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # Resultado inválido
                    continue
                
                similarity = 1.0 / (1.0 + float(dist))
                
                if similarity >= threshold:
                    text = self.documents[idx]
                    metadata = self.metadata[idx].copy() if idx < len(self.metadata) else {}
                    
                    results.append({
                        "text": text,
                        "similarity": float(similarity),
                        "document_id": self.document_ids[idx] if idx < len(self.document_ids) else None,
                        "metadata": metadata
                    })
                    
                    context_parts.append(text)
            
            # Retornar contexto
            if include_metadata:
                return {
                    "context": "\n".join(context_parts),
                    "results": results,
                    "query": query,
                    "top_k": top_k,
                    "total_docs": len(self.documents)
                }
            else:
                return "\n".join(context_parts)

    def get_stats(self) -> Dict:
        """Retorna estadísticas del RAG"""
        with self.lock:
            return {
                "total_documents": len(self.documents),
                "total_embedded": self.total_embedded,
                "index_size": len(self.documents) if self.index else 0,
                "model": self.model_name,
                "dimension": self.dimension,
                "last_update": self.last_update.isoformat() if self.last_update else None,
                "storage_path": self.index_dir
            }

    def save_index(self):
        """Guarda el índice FAISS y metadatos en disco"""
        try:
            with self.lock:
                if self.index is None:
                    return False
                
                # Guardar índice FAISS
                index_path = os.path.join(self.index_dir, f"{self.index_name}.faiss")
                faiss.write_index(self.index, index_path)
                
                # Guardar documentos y metadata
                data = {
                    "documents": self.documents,
                    "metadata": self.metadata,
                    "document_ids": self.document_ids,
                    "total_embedded": self.total_embedded,
                    "last_update": self.last_update,
                    "model_name": self.model_name
                }
                
                data_path = os.path.join(self.index_dir, f"{self.index_name}_data.pkl")
                with open(data_path, "wb") as f:
                    pickle.dump(data, f)
                
                print(f"[✓] Índice FAISS guardado: {index_path}")
                print(f"[✓] Datos guardados: {data_path}")
                return True
        except Exception as e:
            print(f"[✗] Error guardando índice: {e}")
            return False

    def load_index(self):
        """Carga índice FAISS y metadatos desde disco"""
        try:
            index_path = os.path.join(self.index_dir, f"{self.index_name}.faiss")
            data_path = os.path.join(self.index_dir, f"{self.index_name}_data.pkl")
            
            if not os.path.exists(index_path) or not os.path.exists(data_path):
                print(f"[*] No se encontraron índices guardados. Se creará uno nuevo.\n")
                return False
            
            with self.lock:
                # Cargar índice
                self.index = faiss.read_index(index_path)
                
                # Cargar datos
                with open(data_path, "rb") as f:
                    data = pickle.load(f)
                
                self.documents = data.get("documents", [])
                self.metadata = data.get("metadata", [])
                self.document_ids = data.get("document_ids", [])
                self.total_embedded = data.get("total_embedded", 0)
                self.last_update = data.get("last_update")
                
                print(f"[✓] Índice FAISS cargado: {len(self.documents)} documentos")
                return True
        except Exception as e:
            print(f"[⚠] Error cargando índice: {e}")
            return False

    def _rebuild_index(self):
        """Reconstruye el índice desde los documentos actuales"""
        if not self.documents:
            self.index = None
            return
        
        # Generar embeddings para todos los documentos
        embeddings = self.embedding_model.encode(
            self.documents,
            convert_to_numpy=True,
            show_progress_bar=False
        ).astype(np.float32)
        
        # Crear nuevo índice
        self._create_index()
        self.index.add(embeddings)

    def clear(self):
        """Limpia todos los documentos e índice"""
        with self.lock:
            self.documents = []
            self.metadata = []
            self.document_ids = []
            self.index = None
            self.total_embedded = 0
            self.last_update = None
            print("[✓] RAG limpiado")

    def search_metadata(self, **filters) -> List[Dict]:
        """
        Busca documentos por metadata.
        
        Ejemplo:
            results = rag.search_metadata(channel="xqcow", category="gaming")
        """
        results = []
        
        for i, meta in enumerate(self.metadata):
            match = all(meta.get(k) == v for k, v in filters.items())
            if match:
                results.append({
                    "text": self.documents[i],
                    "metadata": meta,
                    "index": i
                })
        
        return results


# ─── Demo y Testing ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 80)
    print("StreamMind — Advanced RAG System (DEMO)")
    print("=" * 80 + "\n")
    
    # Crear instancia
    rag = AdvancedStreamRAG()
    
    # Documentos de prueba
    documents = [
        "El streamer está jugando Valorant en la categoría esports",
        "La categoría es just chatting y todos están hablando de memes",
        "xQc está jugando a League of Legends con su equipo",
        "El chat está hipeado porque es un torneo importante",
        "Pokimane está haciendo un stream de costura y creatividad",
        "Los espectadores están enviando emotes de Twitch",
        "El equipo ganó la partida de Valorant con un clutch increíble",
        "La categoría gaming tiene mucha audiencia ahora",
        "Es un IRL stream en un evento de esports",
        "El chat está tranquilo en el stream de just chatting"
    ]
    
    metadatas = [
        {"channel": "valorant", "category": "esports", "username": "obs"},
        {"channel": "just_chatting", "category": "chat", "username": "bot1"},
        {"channel": "xqcow", "category": "gaming", "username": "xqc"},
        {"channel": "valorant", "category": "esports", "username": "viewer1"},
        {"channel": "pokimane", "category": "creative", "username": "poki"},
        {"channel": "xqcow", "category": "gaming", "username": "viewer2"},
        {"channel": "valorant", "category": "esports", "username": "caster"},
        {"channel": "leagueoflegends", "category": "gaming", "username": "lol_bot"},
        {"channel": "ibai", "category": "variety_gaming", "username": "ibai"},
        {"channel": "just_chatting", "category": "chat", "username": "lurker"}
    ]
    
    # Añadir documentos
    print("[*] Añadiendo documentos de prueba...")
    rag.add_documents(documents, metadatas)
    
    # Test de búsqueda
    print("\n[*] Buscando contexto...")
    
    queries = [
        "Valorant esports",
        "chat tranquilo",
        "gaming popular"
    ]
    
    for query in queries:
        print(f"\n📝 Query: \"{query}\"")
        result = rag.retrieve_context(query, top_k=2, include_metadata=True)
        
        print(f"Contexto encontrado:")
        for i, res in enumerate(result["results"], 1):
            print(f"  [{i}] (similitud: {res['similarity']:.2%})")
            print(f"      \"{res['text'][:60]}...\"")
    
    # Guardar
    print("\n[*] Guardando índice...")
    rag.save_index()
    
    # Stats
    print("\n[*] Estadísticas:")
    stats = rag.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    print("\n[✓] Demo completada")
