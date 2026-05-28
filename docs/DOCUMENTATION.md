# StreamMind-IA — Documentación Técnica

## 1. Descripción General

StreamMind-IA es un sistema de IA para generación de comentarios de chat simulados en tiempo real, diseñado para aplicaciones de streaming (Twitch, YouTube, etc). El sistema integra transcripción de voz, recuperación contextual (RAG), generación de comentarios con LLM y evaluación automática de calidad.

**Arquitectura de 5 Fases:**
1. **Fase 1**: Recolección de datos de Twitch + Análisis Exploratorio
2. **Fase 2**: Sistema RAG (FAISS) para recuperación contextual
3. **Fase 3**: Generación de comentarios con LLM (NVIDIA NIM)
4. **Fase 4**: Interfaz de usuario mejorada con CustomTkinter
5. **Fase 5**: Evaluación automática y tests ciegos

---

## 2. Requisitos del Sistema

### Hardware
- CPU: 4+ núcleos
- RAM: 8GB mínimo (16GB recomendado)
- GPU: Opcional (acelera embeddings)

### Software
- Python 3.9+
- pip o conda

### Dependencias Principales
```bash
pip install -r requirements_stt.txt
```

**Paquetes clave:**
- `faster-whisper`: Transcripción de voz
- `customtkinter`: Interfaz gráfica moderna
- `faiss-cpu`: Vector store para RAG
- `sentence-transformers`: Generación de embeddings
- `numpy`, `pandas`: Procesamiento de datos
- `sounddevice`: Captura de audio

---

## 3. Estructura de Archivos

### Módulos Principales

#### `stt_gui.py` (1200+ líneas)
**Propósito**: Interfaz gráfica principal que integra todas las fases.

**Componentes**:
- Panel de grabación con volumen en vivo
- Display de transcripción (Whisper)
- Integración RAG para contexto
- Generación de comentarios con delays realistas
- Chat interactivo con animaciones

**Uso**:
```bash
python stt_gui.py
```

**Variables de entorno**:
- `NVIDIA_API_KEY`: API key para generación de comentarios (opcional)

---

#### `stream_rag_advanced.py` (470+ líneas)
**Propósito**: Sistema de Recuperación Aumentada por Generación (RAG) con FAISS.

**Características**:
- Embeddings semánticos multiidioma (sentence-transformers)
- Búsqueda vectorial rápida (FAISS IndexFlatL2)
- Persistencia automática a disco
- Thread-safe para operaciones concurrentes

**Clase Principal**: `AdvancedStreamRAG`

**Métodos clave**:
```python
rag = AdvancedStreamRAG()
rag.add_document(text, metadata={...})
context = rag.retrieve_context(query, top_k=3)
rag.save_index()
```

**Configuración**:
- Modelo embedding: `sentence-transformers/distiluse-base-multilingual-cased-v2` (539MB)
- Dimensión: 512
- Max documentos: 10,000
- Métrica distancia: L2 Euclidiana

---

#### `stream_llm_advanced.py` (350+ líneas)
**Propósito**: Generación de comentarios con LLM usando NVIDIA NIM API.

**Características**:
- 3 personalidades distintas (HypeBot, CritiBot, LurkerBot)
- Prompts adaptados por categoría de stream
- Delays realistas entre bots (2-4 segundos)
- Manejo robusto de errores y reintentos
- Fallback a generación heurística

**Clase Principal**: `AdvancedMultiBotGenerator`

**Categorías soportadas**:
- `gaming`: Competitivo, cortos (5-15 palabras)
- `esports`: Profesional, medios (8-20 palabras)
- `creative`: Admirativo, medios (10-20 palabras)
- `just_chatting`: Casual, variados (3-25 palabras)
- `variety_gaming`: Espontáneo, cortos-medios (5-18 palabras)
- `irl`: Amigable, medios (8-18 palabras)

**Uso**:
```python
gen = AdvancedMultiBotGenerator()
gen.connect("NVIDIA_API_KEY")
comments = gen.generate_comments(
    streamer_text="mensaje del streamer",
    context="contexto histórico",
    stream_category="gaming"
)
```

---

#### `stream_chat_ui.py` (450+ líneas)
**Propósito**: Componente de interfaz para display de mensajes del chat.

**Características**:
- Burbujas de mensajes animadas por bot
- Códigos de color distintivos:
  - HypeBot: Rojo (#ff453a)
  - CritiBot: Verde (#30d158)
  - LurkerBot: Púrpura (#bf5af2)
- Contadores de delay en tiempo real
- Auto-scroll inteligente
- Límite de 50 mensajes en pantalla

**Clase Principal**: `ChatPanel`

**Métodos**:
```python
chat = ChatPanel(parent_frame)
chat.add_message("HypeBot", "¡Pog!", delay=2)
chat.clear_chat()
stats = chat.get_stats()
```

---

#### `llm_as_judge.py` (600+ líneas)
**Propósito**: Sistema automático de evaluación de calidad de comentarios.

**Características**:
- Rúbrica de 5 criterios (naturalidad, coherencia, longitud, jerga, personalidad)
- Scoring 0-100 en cada criterio
- Modo API (NVIDIA NIM) o heurístico local
- Clasificación REAL vs GENERADO
- Comparativa real vs generados

**Clase Principal**: `LLMJudge`

**Métodos**:
```python
judge = LLMJudge(api_key="...")
result = judge.evaluate_comment("¡Pog!", "HypeBot")
comparison = judge.compare_real_vs_generated(real_list, gen_list, "HypeBot")
```

**Criterios de Evaluación**:
- Naturalidad: Errores tipográficos, emojis, estructura
- Coherencia: Relación con contexto, palabras Twitch
- Longitud: Adecuación por personalidad
- Jerga: Uso de slang y emotes característicos
- Personalidad: Consistencia con bot personality

---

#### `blind_test_interface.py` (500+ líneas)
**Propósito**: Interfaz GUI para tests ciegos con evaluadores humanos.

**Características**:
- 100 comentarios aleatorios (50 reales + 50 generados)
- Pregunta binaria: "¿Real o Generado?"
- Barra de progreso visual
- Opción skip para comentarios ambiguos
- Resultados detallados con tasa de error
- Guardado automático de resultados en JSON

**Uso**:
```bash
python blind_test_interface.py
```

**Métrica de Éxito**:
- Meta: >30% tasa de error (humanos engañados)
- Interpretación:
  - >50%: IA casi perfecta
  - 30-50%: IA muy buena
  - 10-30%: IA promedio
  - <10%: IA distinguible

---

### Scripts de Análisis y Recolección

#### `twitch_irc_scraper.py` (220+ líneas)
**Propósito**: Recolección de mensajes reales desde Twitch IRC.

**Características**:
- Conexión anónima (sin API key)
- 10 canales populares
- 500+ mensajes por canal
- Timeout configurable (3000s por defecto)
- CSV output con metadatos

**Uso**:
```bash
python twitch_irc_scraper.py
```

**Output**: `twitch_raw_data.csv`
Columnas: username, message, timestamp, channel, stream_category

---

#### `eda_analysis.py` (320+ líneas)
**Propósito**: Análisis Exploratorio de Datos (EDA) del dataset de Twitch.

**Análisis incluidos**:
- Estadísticas básicas (usuarios, canales, categorías)
- Distribución de longitudes
- Análisis por categoría
- Detección de emotes y jerga
- Indicadores de sentimiento
- Reportes JSON y gráficos

**Uso**:
```bash
python eda_analysis.py
```

**Output**: 
- `eda_report.json`: Estadísticas en JSON
- Reporte en consola con insights

---

#### `labeled_dataset.py` (180+ líneas)
**Propósito**: Extracción de dataset etiquetado para evaluación.

**Características**:
- Filtrado de calidad (spam, bots, longitud)
- Muestreo estratificado por categoría
- Etiquetado: es_humano=1, quality_score=5
- Metadata enriquecida

**Uso**:
```bash
python labeled_dataset.py
```

**Output**: 
- `evaluation_labeled_dataset.csv`: 50 comentarios etiquetados
- `evaluation_labeled_dataset.json`: Metadata

---

### Demostraciones

#### `demo_llm_advanced.py`
Demuestra capacidades del LLM sin requerir API key.
```bash
python demo_llm_advanced.py
```

#### `demo_fase5.py`
Demo completo de evaluación (50 reales + 50 generados).
```bash
python demo_fase5.py
```

---

## 4. Flujo de Uso Recomendado

### Opción 1: Demo Completo (Sin datos reales)
```bash
# Demostración del evaluador automático
python demo_fase5.py

# Test ciego interactivo
python blind_test_interface.py
```

### Opción 2: Recolección de Datos + Análisis
```bash
# Fase 1: Recolectar datos de Twitch
python twitch_irc_scraper.py        # ~50-60 minutos

# Analizar dataset
python eda_analysis.py               # ~1 minuto

# Crear dataset etiquetado
python labeled_dataset.py            # <1 minuto
```

### Opción 3: Sistema Completo (Recomendado)
```bash
# 1. Lanzar GUI principal
python stt_gui.py

# 2. En otra terminal, ejecutar test ciego
python blind_test_interface.py

# 3. Analizar resultados JSON generados
# Los resultados se guardan automáticamente en:
# blind_test_results_YYYYMMDD_HHMMSS.json
```

---

## 5. Configuración y Personalización

### Variables de Entorno
```bash
# Para usar LLM con API real:
export NVIDIA_API_KEY="tu_clave_aqui"

# (En Windows PowerShell)
$env:NVIDIA_API_KEY="tu_clave_aqui"
```

### Configuración por Archivo

#### `stt_gui.py`
- **Línea 48-54**: Paleta de colores (tema oscuro Apple)
- **Línea 100**: Modelo Whisper (tiny/base/small/medium/large)
- **Línea 950**: Canvas size (puede ajustarse)

#### `stream_rag_advanced.py`
- **Línea 37**: Modelo embedding (cambiar por otro de HuggingFace)
- **Línea 38**: Dimensión (debe coincidir con modelo)
- **Línea 40**: Max documentos (aumentar para datasets grandes)
- **Línea 39**: Directorio de índices

#### `stream_llm_advanced.py`
- **Línea 46-65**: Temperatura (generación vs evaluación)
- **Línea 70-120**: System prompts por categoría
- **Línea 140-145**: Delays por bot (en segundos)

#### `blind_test_interface.py`
- **Línea 32**: Umbral de éxito (por defecto 30%)
- **Línea 150-200**: REAL_COMMENTS y GENERATED_COMMENTS

---

## 6. Troubleshooting

### Problema: "No module named 'faiss'"
**Solución**:
```bash
pip install faiss-cpu
# o para GPU:
pip install faiss-gpu
```

### Problema: "Model download timeout"
**Solución**:
```bash
# Descargar manualmente:
huggingface-cli download sentence-transformers/distiluse-base-multilingual-cased-v2
```

### Problema: Audio no funciona
**Solución**:
```bash
# Instalar sounddevice:
pip install sounddevice

# Verificar dispositivos:
python -c "import sounddevice; print(sounddevice.query_devices())"
```

### Problema: NVIDIA NIM API falla
**Solución**:
- Verificar API key en https://build.nvidia.com/
- Usar modo heurístico (sin API key)
- Los comentarios se generan localmente como fallback

---

## 7. Métricas y Resultados

### Dataset Real (EDA)
- **Mensajes recolectados**: 1,570
- **Usuarios únicos**: 335
- **Longitud promedio**: 14 caracteres
- **Longitud mediana**: 8 caracteres
- **Jerga dominante**: xd (91), lol (27), kek (14), pog (11)
- **Sentimiento**: 66.4% mayúsculas, 2.2% preguntas

### Evaluación Automática
- **Humanness Score promedio (real)**: 65.3/100
- **Humanness Score promedio (generado)**: 62.4/100
- **Tasa de error (misclassification)**: 58%
- **Veredicto**: INDISTINGUIBLES

### Test Ciego
- **Comentarios evaluados**: 100 (50 reales + 50 generados)
- **Tasa de error**: Variable según evaluador
- **Meta**: >30% humanos engañados

---

## 8. Notas de Desarrollo

### Cambios Recientes
- Eliminación de emojis en outputs (simplificación)
- Documentación mejorada con docstrings completos
- Estandarización de prefijos de logs: [OK], [ERROR], [INFO], [WARNING]
- Thread-safety en todas las operaciones RAG

### Próximas Mejoras
- Integración con OBS/Streamlabs para overlay
- Persistencia de históricos de chat
- Fine-tuning de modelos con datos reales
- Soporte multiidioma expandido
- Dashboard de analytics

---

## 9. Contacto y Soporte

Para problemas o sugerencias, documentar en:
- Error logs: stdout/stderr de terminal
- Resultados tests: JSON files en directorio raíz
- Índices RAG: `rag_indexes/` directorio

---

**Última actualización**: Mayo 2026
**Versión**: 2.0 (Sistema completo integrado)
**Estado**: Producción lista

