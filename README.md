# StreamMind-IA

**Sistema inteligente de generación de comentarios de chat con IA para streaming**

Genera comentarios tan realistas que son indistinguibles de los que escriben humanos.

---

## 🎯 ¿Qué hace?

StreamMind-IA es un pipeline de 5 fases que:

1. 🎤 **Escucha** → Transcribe audio a texto (Whisper)
2. 🧠 **Comprende** → Busca contexto en historial (FAISS RAG)
3. 💬 **Genera** → Crea 3 comentarios únicos (LLM - NVIDIA NIM)
4. 🎨 **Muestra** → Visualiza en chat elegante
5. 📊 **Evalúa** → Califica realismo automático

---

## ⚡ Instalación Rápida

### Requisitos
- Python 3.9+
- 8GB RAM (16GB recomendado)
- GPU opcional (CUDA acelera)

### Setup
```bash
# 1. Clonar/descargar repositorio
cd StreamMind-IA

# 2. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements_stt.txt

# 4. Ejecutar
python stt_gui.py
```

### Configuración Opcional
```bash
# Si tienes API key de NVIDIA para mejor LLM:
set NVIDIA_API_KEY=tu_key_aqui
```

---

## 🚀 Uso

### Interfaz Principal
```bash
python stt_gui.py
```

Características:
- Captura audio del micrófono
- Transcripción en tiempo real
- Generación de comentarios con contexto
- Chat interactivo con 3 bots (HypeBot, CritiBot, LurkerBot)
- Evaluación automática de realismo

### Test Ciego (Validación Humana)
```bash
python blind_test_interface.py
```

Permite a humanos determinar si comentarios son IA o reales.

---

## 📊 Componentes

| Módulo | Descripción |
|--------|-------------|
| `stt_gui.py` | Interfaz gráfica principal |
| `stt_whisper.py` | Transcripción de voz (STT) |
| `stream_rag_advanced.py` | Búsqueda contextual (RAG) |
| `stream_llm_advanced.py` | Generación de comentarios (LLM) |
| `llm_as_judge.py` | Evaluador automático |
| `blind_test_interface.py` | Tests ciegos interactivos |
| `utils/` | Utilidades (análisis, datasets) |

---

## 🔧 Estructura de Archivos

```
StreamMind-IA/
├── stt_gui.py                  # GUI principal
├── stt_whisper.py              # STT engine
├── stream_rag_advanced.py      # Sistema RAG
├── stream_llm_advanced.py      # Generador LLM
├── llm_as_judge.py             # Evaluador
├── blind_test_interface.py     # Tests ciegos
├── stream_chat_ui.py           # Componente chat
│
├── utils/                      # Utilidades
│   ├── labeled_dataset.py
│   ├── eda_analysis.py
│   └── __init__.py
│
├── rag_indexes/                # Índices FAISS
├── requirements_stt.txt        # Dependencias
├── README.md                   # Este archivo
├── DOCUMENTATION.md            # Docs técnicas
└── CHANGELOG.md                # Historial
```

---

## 📚 Los 3 Bots

| Bot | Personalidad | Ejemplo |
|-----|-------------|---------|
| **HypeBot** 🔴 | Entusiasta, energético | "LET'S GOO!!! Increíble 🔥" |
| **CritiBot** 💚 | Analítico, inteligente | "Jugada bien ejecutada, timing ajustado" |
| **LurkerBot** 💜 | Misterioso, observador | "...eso estuvo bien" |

---

## 📊 Requisitos del Sistema

- **CPU**: 4+ núcleos
- **RAM**: 8GB mínimo (16GB recomendado)
- **Almacen**: 5GB (modelos + índices)
- **GPU**: Opcional (CUDA/cuDNN)
- **Micrófono**: Funcional

---

## 🎓 Para Aprender Más

Ver `DOCUMENTATION.md` para documentación técnica completa incluyendo:
- Arquitectura del sistema
- API de cada módulo
- Configuración avanzada
- Troubleshooting

---

## 📈 Objetivo

Generar comentarios que:
- ✅ Parezcan escritos por humanos reales
- ✅ Sean contextualmente relevantes
- ✅ Tengan personalidades consistentes
- ✅ Engañen a humanos (>30% de error)
- ✅ Pasen evaluación automática (>85 score)

---

**Última actualización**: Mayo 2026
**Versión**: 2.0 Simplificada
**Estado**: ✅ Funcional y listo para usar
