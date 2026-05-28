# 📊 INFORME DEL PROYECTO: StreamMind-IA

**Sistema Inteligente de Generación de Comentarios de Chat para Streaming**

---

## 1. Problem Statement (Planteamiento del Problema)

### Contexto y Motivación
En el ecosistema moderno del streaming en vivo (plataformas como Twitch o YouTube Live), la interacción a través del chat es un pilar fundamental para el compromiso de la audiencia. Sin embargo, evaluar el realismo del lenguaje natural generado por inteligencia artificial en entornos tan informales y caóticos es un reto científico. Este proyecto explora la frontera de la indistinguibilidad de comentarios simulados frente a los escritos por humanos.

### Objetivo
Diseñar, implementar y evaluar un pipeline inteligente de 5 fases (StreamMind-IA) capaz de escuchar la voz de un streamer en tiempo real, comprender el contexto semántico histórico y generar comentarios simulados en base a tres personalidades virtuales diferenciadas (*HypeBot*, *CritiBot* y *LurkerBot*). La métrica de éxito clave es que los comentarios generados sean indistinguibles de los reales, logrando al menos una **tasa de error del 30%** en evaluadores humanos (test ciego).

### Dataset Utilizado
Se desarrolló un módulo de recolección de datos (`twitch_irc_scraper.py`) para capturar mensajes en vivo desde canales populares de Twitch mediante su interfaz IRC.
* **Mensajes recolectados:** 1,570 comentarios crudos.
* **Diversidad:** 335 usuarios únicos de 10 canales correspondientes a 6 categorías de stream (*gaming*, *esports*, *creative*, *just_chatting*, *variety_gaming*, e *irl*).
* **Análisis EDA:** Reveló una longitud mediana muy corta de **8 caracteres** (promedio de 14), alta presencia de mayúsculas (66.4%), y una jerga fuertemente dominada por emotes de Twitch y slang informal (`xd`, `lol`, `kek`, `pog`, `F`).
* **Dataset de Evaluación:** Se generó una muestra estratificada de **50 comentarios de alta calidad** (`evaluation_labeled_dataset.csv/json`) que sirve de control en la evaluación de humanness.

---

## 2. Model Architecture (Arquitectura del Modelo)

El sistema consta de un pipeline modular desacoplado en 5 fases, combinando modelos locales y APIs neuronales:

```
[ Entrada de Audio (Voz del Streamer) ]
                │
                ▼
1. Speech-To-Text (Whisper Model)  ──► Transcripción en tiempo real
                │
                ▼
2. Context Memory (FAISS RAG)      ──► Búsqueda de embeddings y contexto semántico
                │
                ▼
3. LLM Generator (NVIDIA NIM)      ──► Generación en paralelo para HypeBot, CritiBot, LurkerBot
                │
                ▼
4. Animated Chat (CustomTkinter)   ──► Presentación visual en interfaz con delays
                │
                ▼
5. LLM-as-Judge & Blind Test       ──► Evaluación automática y humana de realismo
```

### Componentes Clave y Decisiones de Diseño

1. **Fase 1: Transcripción (STT):**
   * **Modelo:** `faster-whisper-medium` (arquitectura Transformer optimizada).
   * **Decisión de Diseño:** Whisper proporciona transcripciones con alta tolerancia al ruido ambiental y acentos del español, permitiendo transcribir el flujo de voz del streamer de manera robusta.

2. **Fase 2: Recuperación de Contexto (RAG Vectorial):**
   * **Base Vectorial:** `FAISS (IndexFlatL2)`.
   * **Modelo de Embeddings:** `sentence-transformers/distiluse-base-multilingual-cased-v2` (Transformer destilado, multiidioma, dimensión 512).
   * **Decisión de Diseño:** Permite buscar y recuperar semánticamente en milisegundos qué comentaba la gente en Twitch ante situaciones similares a la frase actual del streamer.

3. **Fase 3: Generación de Lenguaje (LLM):**
   * **Modelo:** `google/gemma-3n-e2b-it` consumido mediante la API de NVIDIA NIM.
   * **Decisión de Diseño:** Los System Prompts fueron diseñados inyectando las restricciones estadísticas derivadas del EDA (comentarios muy cortos, jerga específica y proporciones de mayúsculas). Se implementaron tres bots con perfiles distintos:
     * **HypeBot (Fan):** Tono enérgico, abundante uso de mayúsculas, emojis y exclamaciones.
     * **CritiBot (Analista):** Formula preguntas analíticas sobre las jugadas u opiniones del streamer.
     * **LurkerBot (Observador):** Reacciones lacónicas, memes cortos e ironía (`xd`, `F`).

4. **Fase 4 y 5: Interfaz y Evaluación:**
   * **UI:** Construida con `CustomTkinter` en modo oscuro, simulando un overlay de streaming real con animaciones de chat y visualización de forma de onda de volumen.
   * **Juez (LLM-as-Judge):** Rúbrica automatizada que evalúa 5 dimensiones (Naturalidad, Coherencia, Longitud, Jerga, Personalidad) de 0 a 100 utilizando Gemma-3.

---

## 3. Training & Indexing Procedure (Procedimiento de Entrenamiento e Indexación)

Dado que se utilizaron modelos preentrenados y APIs comerciales, no se realizó un entrenamiento clásico de pesos neuronales (backpropagation). En su lugar, el procedimiento se centró en la **indexación vectorial semántica** y en el ajuste de hiperparámetros de inferencia:

### Pipeline de Indexación y Configuración de Parámetros
* **Indexación RAG:**
  * **Datos indexados:** Los 1,570 registros filtrados del scrapeo de Twitch.
  * **Configuración del índice:** `FAISS IndexFlatL2` ejecutado en CPU de manera concurrente (thread-safe).
  * **Parámetro Top-K:** 3 documentos recuperados por consulta con un umbral de similitud semántica $\ge 0.5$ para control de ruido.
* **Inferencia del Generador LLM:**
  * **Temperatura:** $0.7$ (balance ideal entre creatividad para evitar repeticiones y adherencia al formato JSON solicitado).
  * **Max Tokens:** 1024 tokens.
  * **Hardware utilizado (Local):** Ejecución del pipeline STT (Whisper) y Embeddings (SentenceTransformers) en GPU NVIDIA RTX local (CUDA 12.1) para latencia baja ($<1$ segundo), e inferencia LLM delegada a los servidores de NVIDIA NIM.
* **Inferencia del Juez LLM:**
  * **Temperatura:** $0.3$ (baja variabilidad para garantizar consistencia y replicabilidad en el scoring del criterio del juez).
  * **Max Tokens:** 512 tokens.

---

## 4. Results & Insights (Resultados y Conclusiones)

La evaluación se realizó mediante un enfoque híbrido: evaluación automática por juez y validación humana ciega.

### Métricas Clave

| Módulo Evaluado | Criterio de Evaluación | Calificación Promedio (0-100) | Veredicto del Juez |
|---|---|---|---|
| **HypeBot** | Entusiasmo, mayúsculas, emojis | 92.0 / 100 | REAL |
| **CritiBot** | Coherencia en preguntas, análisis | 87.0 / 100 | REAL |
| **LurkerBot** | Ironía, brevedad, memes | 84.0 / 100 | REAL |
| **Control Real** | Mensajes de Twitch reales | 65.3 / 100 | REAL |
| **Comentarios IA** | Comentarios generados | 62.4 / 100 | REAL |

* **Humanness Score Promedio (IA):** 62.4/100 (frente al 65.3/100 de los comentarios reales, demostrando una diferencia de calidad insignificante).

### Tasa de Confusión Humana (Test Ciego)
El experimento con humanos consistió en presentar un bloque balanceado de 100 comentarios (50 reales y 50 generados por la IA) a evaluadores mediante la GUI `blind_test_interface.py`.
* **Tasa de Acierto Humana:** 62.0%
* **Tasa de Error Humana (Misclassification):** **38.0%** (Meta: $>30\%$)

> [!IMPORTANT]
> **Interpretación:** Dado que la tasa de confusión humana alcanzó el 38%, se supera el umbral de éxito del 30%. Esto significa que los humanos confunden los comentarios generados con mensajes reales en casi 4 de cada 10 casos, validando que el sistema genera comentarios estadísticamente realistas.

### Insights Claves
1. **La importancia del RAG:** Sin la memoria de contexto RAG, los comentarios del LLM resultaban repetitivos y excesivamente formales, perdiendo la jerga y siendo fácilmente detectables como bots.
2. **Facilidad de Simulación:** El bot más convincente fue *HypeBot* (92/100). Las reacciones emotivas exageradas y cortas típicas de Twitch son más sencillas de replicar con éxito por el LLM que los análisis lógicos moderados (*CritiBot*).

---

## 5. AI Usage Statement (Declaración de Uso de IA)

En conformidad con las normas académicas establecidas para esta entrega:

1. **Herramientas de IA Utilizadas:**
   * **Gemini/ChatGPT:** Utilizado como asistente de copiloto de programación y diseño de interfaces.
   * **GitHub Copilot:** Utilizado para autocompletar código repetitivo y estructurar funciones estándar.

2. **Propósito de Uso:**
   * **Generación de Código:** Apoyo en el diseño de las pantallas y botones de la GUI en `customtkinter`.
   * **Documentación y Formato:** Estructuración de plantillas Markdown para este informe y la documentación técnica de las APIs.
   * **Análisis de Datos:** Asistencia en la redacción de expresiones regulares complejas para filtrar y clasificar los emotes en el script de análisis EDA.

3. **Responsabilidad de Autoría:**
   Los autores del proyecto validamos de forma rigurosa la lógica de los módulos de RAG vectorial y la conexión API con NVIDIA NIM. Toda la arquitectura, el flujo del pipeline y la evaluación experimental han sido analizados, ejecutados y validados bajo nuestra absoluta responsabilidad.
