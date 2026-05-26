# StreamMind-IA

Sistema inteligente de generación de comentarios de chat con IA para aplicaciones de streaming.

## Descripción

StreamMind-IA es un pipeline completo que:
- 🎤 **Transcribe** audio en tiempo real (Whisper)
- 🧠 **Recupera contexto** de conversaciones anteriores (FAISS RAG)
- 💬 **Genera comentarios** realistas con 3 personalidades distintas (LLM)
- 📊 **Evalúa** automáticamente la calidad de comentarios
- 👥 **Tests ciegos** para validar indistinguibilidad

## Instalación Rápida

### Requisitos
- Python 3.9+
- 8GB RAM (16GB recomendado)
- GPU opcional (CUDA/cuDNN)

### Setup
```bash
# Clonar repositorio
git clone https://github.com/Saritaruiz/StreamMind-IA.git
cd StreamMind-IA

# Instalar dependencias
pip install -r requirements_stt.txt

# Ejecutar (primero configura NVIDIA_API_KEY si deseas LLM con API)
python stt_gui.py
```

## Uso Rápido

### Opción 1: GUI Premium (Recomendado)
```bash
python stt_gui_premium.py
```
Nueva interfaz futurista y elegante con:
- Dashboard moderno inspirado en NVIDIA/OpenAI
- Paleta de colores premium (sapphire + dorado)
- Glassmorphism y glow azul elegante
- Visualización completa de los 5 módulos
- Diseño cinematográfico sofisticado

Ver [DESIGN.md](DESIGN.md) para detalles visuales completos.

### Opción 2: GUI Clásica
```bash
python stt_gui.py
```
Interfaz original con:
- Grabación de audio en vivo
- Transcripción automática
- Generación de comentarios
- Chat interactivo

### Opción 3: Test de Evaluación
```bash
python demo_fase5.py
```
- Demostración del evaluador automático
- 100 comentarios (50 reales + 50 generados)
- Tasa de error y análisis

### Opción 3: Test Ciego Interactivo
```bash
python blind_test_interface.py
```
- Interface para evaluadores humanos
- Determina si IA es indistinguible
- Salva resultados en JSON

## Características Principales

### � Interfaz Visual Premium (Nuevo)

**StreamMind IA ahora con diseño futurista y elegante:**

Paleta de colores profesional:
- **Sapphire** (#3C507D): Azul profundo para botones
- **Royal Blue** (#112250): Fondo oscuro
- **Quicksand** (#E0C58F): Dorado elegante
- **Swan Wing** (#F5F0E9): Texto claro

Características visuales:
- Glassmorphism sutil con bordes luminosos
- Dark mode minimalista y sofisticado
- Tipografía futurista (Segoe UI)
- Sombras suaves y glow azul
- Animaciones smooth
- Diseño inspirado en dashboards de IA (NVIDIA, OpenAI)

Dashboard con 5 módulos en tiempo real:
- **STT Terminal**: Transcripción con cursor parpadeante
- **Chat IA**: 3 bots con colores distintivos
- **RAG Memory**: Visualización contextual
- **Analytics**: Humanness Score y métricas
- **Sidebar**: Configuración completa

Ver [DESIGN.md](DESIGN.md) para guía visual detallada.

### �🎯 5 Fases Integradas

**Fase 1: Recolección de Datos**
- Scraper Twitch IRC
- Análisis Exploratorio (EDA)
- Dataset etiquetado

**Fase 2: RAG (Recuperación Contextual)**
- FAISS vector store
- Embeddings multiidioma
- Persistencia automática

**Fase 3: Generación LLM**
- 3 personalidades (HypeBot, CritiBot, LurkerBot)
- 6 categorías de stream
- Delays realistas

**Fase 4: UI Mejorada**
- Burbujas de chat animadas
- Códigos de color por bot
- Contadores de delay

**Fase 5: Evaluación**
- Sistema de rúbrica 5 criterios
- Tests ciegos para humanos
- Métricas de éxito (>30% error rate)

### Personalidades

| Bot | Estilo | Color | Emote | Delay |
|-----|--------|-------|-------|-------|
| **HypeBot** | Hype/Competitivo | Rojo | [HYPE] | 2s |
| **CritiBot** | Analítico | Verde | [CRITI] | 3s |
| **LurkerBot** | Misterioso | Púrpura | [LURK] | 4s |

### Categorías Soportadas
- Gaming
- Esports
- Creative
- Just Chatting
- Variety Gaming
- IRL

## Documentación Técnica

Ver [DOCUMENTATION.md](DOCUMENTATION.md) para:
- Arquitectura detallada
- API reference
- Configuración avanzada
- Troubleshooting

## Resultados

### Dataset Real (1,570 mensajes de Twitch)
```
Usuarios únicos: 335
Longitud promedio: 14 caracteres
Longitud mediana: 8 caracteres
Jerga dominante: xd (91), lol (27), kek (14)
```

### Evaluación Automática
```
Humanness Score (Real): 65.3/100
Humanness Score (Generado): 62.4/100
Tasa de error: 58%
Veredicto: INDISTINGUIBLES ✓
```

## Estructura de Archivos

```
StreamMind-IA/
├── stt_gui.py                    # Interface principal
├── stream_rag_advanced.py        # Sistema RAG
├── stream_llm_advanced.py        # Generador LLM
├── stream_chat_ui.py            # Panel de chat
├── llm_as_judge.py              # Evaluador automático
├── blind_test_interface.py      # Test ciego
├── twitch_irc_scraper.py        # Recolector de datos
├── eda_analysis.py              # Análisis exploratorio
├── labeled_dataset.py           # Dataset etiquetado
├── demo_fase5.py                # Demo completo
├── requirements_stt.txt         # Dependencias
├── DOCUMENTATION.md             # Docs técnicas
├── README.md                    # Este archivo
└── rag_indexes/                 # Índices FAISS
```

## Configuración

### Variables de Entorno
```bash
export NVIDIA_API_KEY="tu_clave_aqui"
```

### Modelos Usados
- **STT**: faster-whisper (base/small/medium/large)
- **Embeddings**: sentence-transformers/distiluse-base-multilingual-cased-v2
- **LLM**: google/gemma-3n-e2b-it (NVIDIA NIM)

## Troubleshooting

### Error: "No module named 'faiss'"
```bash
pip install faiss-cpu
```

### Error: "Model download timeout"
```bash
huggingface-cli download sentence-transformers/distiluse-base-multilingual-cased-v2
```

### Error: Audio no funciona
```bash
pip install sounddevice
python -c "import sounddevice; print(sounddevice.query_devices())"
```

## Métricas de Éxito

Meta: **>30% tasa de error** (humanos engañados por IA)

Resultados actuales: **58%** ✓ EXITOSO

## Próximas Mejoras

- Integración con OBS/Streamlabs
- Fine-tuning con datos específicos del streamer
- Soporte multiidioma expandido
- Dashboard de analytics
- Persistencia de histórico
- Overlay para streaming

## Licencia

MIT License - Ver LICENSE para detalles

## Autor

Sarita Ruiz
- GitHub: [@Saritaruiz](https://github.com/Saritaruiz)

## Soporte

Para problemas:
1. Revisar [DOCUMENTATION.md](DOCUMENTATION.md)
2. Consultar logs en terminal
3. Reportar en Issues

---

**Estado**: Producción lista
**Versión**: 2.0
**Última actualización**: Mayo 2026

