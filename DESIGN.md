# StreamMind IA — Premium UI Design Guide

## Descripción General

Nueva interfaz futurista y elegante basada en dashboards de IA modernos. Diseño inspirado en NVIDIA, OpenAI y herramientas de streaming profesionales.

**Archivo**: `stt_gui_premium.py`

---

## Paleta de Colores Premium

### Colores Principales

```
┌─────────────────────────────────────────────────────────────┐
│                  PALETA COLOR STREAMIND IA                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Sapphire       #3C507D  ████████░  Azul profundo (botones)  │
│  Royal Blue     #112250  ████░░░░░  Azul oscuro (background) │
│  Quicksand      #E0C58F  ███████░░  Dorado elegante (accents)│
│  Swan Wing      #F5F0E9  ███████░░  Blanco crema (texto)     │
│  Shellstone     #D9CBC2  ███████░░  Beige suave (secundario) │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Colores de Bots (Basados en EDA):
  - HypeBot:    #FF6B6B  (Rojo energético)
  - CritiBot:   #51CF66  (Verde inteligente)
  - LurkerBot:  #A78BFA  (Púrpura misterioso)
```

### Psicología de Colores

| Color | Función | Psicología |
|-------|---------|-----------|
| **Sapphire** | Botones, acentos | Confianza, profesionalismo, tecnología |
| **Royal Blue** | Fondo principal | Calma, profesionalismo, sofisticación |
| **Quicksand** | Highlights, títulos | Lujo, elegancia, premium |
| **Swan Wing** | Texto principal | Legibilidad, claridad |
| **Shellstone** | Texto secundario | Subtletez, jerarquía visual |

---

## Componentes Premium

### 1. PremiumCard
Tarjeta base con glassmorphism sutil y bordes luminosos.

**Características**:
- Borde de 1px con glow Sapphire
- Bordes redondeados (16px)
- Fondo semitransparente (#1A2145)
- Header opcional con título dorado

**Uso**:
```python
card = PremiumCard(parent, title="Mi Tarjeta")
card.pack(fill="both", expand=True)
```

### 2. BotMessage
Mensaje de bot estilo Twitch moderno.

**Componentes**:
- Indicador de color (bot identity)
- Nombre del bot coloreado
- Timestamp gris
- Texto del mensaje

**Colores Dinámicos**:
- HypeBot: Rojo (#FF6B6B)
- CritiBot: Verde (#51CF66)
- LurkerBot: Púrpura (#A78BFA)

### 3. TranscriptionTerminal
Terminal moderna para transcripción en vivo.

**Características**:
- Fuente Courier New (monoespaciada)
- Color texto: Dorado Quicksand
- Fondo: Azul Royal oscuro
- Cursor parpadeante animado

**Simula**:
- Experiencia de consola IA
- Transcripción en tiempo real
- Estados del sistema

### 4. StatCard
Tarjeta de estadística compacta.

**Elementos**:
- Label (texto pequeño gris)
- Valor grande (dorado)
- Unidad opcional

**Uso típico**:
```python
stat = StatCard(parent, label="Real Avg", value="65.3", unit="/100")
```

### 5. PremiumSidebar
Barra lateral con controles y configuración.

**Secciones**:
1. Logo "StreamMind IA"
2. Modelos STT (Whisper)
3. Configuración LLM (NVIDIA NIM)
4. Toggles de módulos
5. Estadísticas del sistema

**Controles**:
- Dropdowns (modelos)
- Text inputs (API keys)
- Sliders (temperatura)
- Toggle switches (módulos)

---

## Estructura Visual Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER: StreamMind IA — Premium Dashboard                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  SIDEBAR (280px)      │      MAIN PANEL (Scroll)                │
│  ─────────────────    │  ──────────────────────────────────────  │
│                       │                                          │
│  [StreamMind IA]      │  Dashboard Simulación de Engagement     │
│                       │  ────────────────────────────────────    │
│  STT (Whisper)        │                                          │
│  ┌─────────────────┐  │  ┌──────────────────┬──────────────────┐ │
│  │ Modelo: Base    │  │  │ TRANSCRIPCIÓN    │ CHAT IA SIMULADO │ │
│  └─────────────────┘  │  │ (Terminal)       │ (Mensajes)       │ │
│                       │  │                  │                  │ │
│  LLM (NIM)            │  │ [SYSTEM] Sistema │ [HYPE] OMEGALUL │ │
│  ┌─────────────────┐  │  │ iniciado...      │ [CRITI] Clever  │ │
│  │ Modelo: gemma   │  │  │ [WHISPER] Trans. │ [LURK] xd       │ │
│  │ API Key: ****   │  │  └──────────────────┴──────────────────┘ │
│  │ Temp: 0.7       │  │                                          │
│  └─────────────────┘  │  ┌──────────────────┬──────────────────┐ │
│                       │  │ MEMORIA (RAG)    │ HUMANNESS SCORE  │ │
│  Módulos              │  │ Docs: 1,570      │ Real: 65.3/100   │ │
│  ☑ Cámara            │  │ Latencia: 127ms  │ Gen:  62.4/100   │ │
│  ☑ STT               │  │ Similitud: 0.78  │ Error: 58%       │ │
│  ☑ Chat IA           │  └──────────────────┴──────────────────┘ │
│  ☑ RAG               │                                          │
│                       │  ┌────────────────────────────────────┐  │
│  Sistema              │  │ ▶ Iniciar  🎯 Test  📊 Evaluar    │  │
│  Mensajes: 0          │  └────────────────────────────────────┘  │
│  Latencia: 0ms        │                                          │
│                       │                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Características Visuales Premium

### Glassmorphism
- Bordes semi-transparentes
- Fondo con gradientes suaves
- Efecto de profundidad sin solidez excesiva

### Glow Azul
- Bordes con brillo Sapphire
- Efecto luminoso alrededor de tarjetas
- Acentos dorados en interactive elements

### Tipografía
- **Títulos**: Segoe UI Bold, 14-20px, Quicksand
- **Contenido**: Segoe UI Regular, 11-12px, Swan Wing
- **Terminal**: Courier New Regular, 11px, Quicksand
- **Códigos**: Courier New, monoespaciada

### Animaciones
- Cursor parpadeante en terminal (500ms)
- Transiciones smooth en interacciones
- Hover effects en botones y controles

---

## Flujo Visual del Proceso

```
Usuario → Configura (Sidebar) → Inicia (Botón) → Visualiza Flujo:

    ENTRADA (Micrófono/Audio)
           ↓
    [STT - Transcripción] (Terminal)
           ↓
    [RAG - Recuperación] (Memoria Contextual)
           ↓
    [LLM - Generación] (Procesamiento)
           ↓
    [CHAT - Display] (Chat IA Simulado)
           ↓
    [EVAL - Evaluación] (Humanness Score)
```

Cada etapa se visualiza en **tarjetas independientes** con:
- Título descriptivo (Dorado)
- Contenido dinámico
- Indicadores de estado
- Información complementaria

---

## Tokens y Espaciado

### Padding/Margin Estándar
```
Exterior (window → sidebar):      0px
Sidebar ancho:                    280px
Área contenido padx/pady:         16px
Tarjetas internas padx/pady:      12px-16px
Entre tarjetas:                   8px
Entre elementos:                  4-8px
```

### Tamaños de Componentes

| Elemento | Alto | Ancho |
|----------|------|-------|
| Header | 40px | 100% |
| Card mínima | 100px | 100% |
| Terminal | 280px | flexible |
| Chat card | 280px | flexible |
| Stat card | 150px | 33% |
| Botón | 40px | 150px |
| Sidebar | fullscreen | 280px |

---

## Estados Visuales

### Normal
- Fondo: BG_CARD (#1A2145)
- Borde: Sapphire (#3C507D), 1px
- Texto: Swan Wing (#F5F0E9)

### Hover (Botones)
- Fondo: Más claro (+15% luminosidad)
- Cursor: pointer
- Sombra: Suave glow

### Activo (Toggles)
- Fondo: Quicksand (#E0C58F)
- Texto: Royal Blue (#112250)
- Animación: Suave transición

### Disabled
- Opacidad: 50%
- Color: Gris neutro

---

## Paleta Alternativa (Modo Claro - No implementado aún)

Si en futuro se necesita light mode:

```
Fondo principal:     #F5F0E9  (Swan Wing)
Tarjetas:           #FFFFFF  (Blanco)
Texto principal:    #112250  (Royal Blue)
Acentos:            #3C507D  (Sapphire)
Highlights:         #E0C58F  (Quicksand)
```

---

## Guía de Extensión

### Agregar Nueva Tarjeta

```python
# Crear tarjeta premium
new_card = PremiumCard(parent, title="Mi Nueva Tarjeta")
new_card.pack(fill="both", expand=True, padx=8, pady=8)

# Contenido personalizado dentro de content_frame
label = ctk.CTkLabel(
    new_card.content_frame,
    text="Contenido aquí",
    text_color=PremiumColors.SWAN_WING,
)
label.pack()
```

### Agregar Nuevo Bot al Chat

```python
bot_msg = BotMessage(
    chat_card.content_frame,
    bot_name="MyBot",
    message="Mi mensaje",
    color="custom_color"
)
bot_msg.pack(fill="x", pady=4)
```

### Agregar Estadística

```python
stat = StatCard(
    parent,
    label="Métrica",
    value="42",
    unit="unidad"
)
stat.pack(fill="both", expand=True)
```

---

## Respuesta a Requisitos de Diseño

### ✓ Minimalista
- Espacios negativos amplios
- Solo elementos esenciales
- Tipografía limpia

### ✓ Tecnológica
- Fuente Segoe UI (moderna)
- Terminal monoespaciada
- Colores tech (azules/dorados)

### ✓ Sofisticada
- Paleta limitada y consistente
- Glassmorphism sutil
- Bordes redondeados modernos

### ✓ Cinematográfica
- Glow azul elegante
- Colores premium (dorado)
- Profundidad visual

### ✓ Dark Mode
- Fondo azul oscuro (#112250)
- Texto claro (blanco crema)
- Contraste optimizado

### ✓ Sistema Multiagente
- 3 bots con colores distintivos
- Chat Twitch-style
- Identidades visuales claras

### ✓ Dashboard IA
- RAG visualization
- Humanness Score metrics
- Terminal STT

---

## Archivos Relacionados

- **stt_gui_premium.py**: Interfaz principal premium
- **stream_chat_ui.py**: Componente chat (integrable)
- **Documentation.md**: Docs técnicas completas
- **README.md**: Guía general

---

**Estado**: ✅ Implementado y funcional
**Versión**: 1.0 Premium
**Última actualización**: Mayo 2026

