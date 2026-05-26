# Integration Guide — Premium UI + Backend Systems

## Descripción General

Este documento proporciona la **hoja de ruta técnica** para conectar `stt_gui_premium.py` con los sistemas existentes de RAG, LLM, Chat y Evaluación.

---

## 🎯 Arquitectura de Integración

```
┌─────────────────────────────────────────────────────────────────┐
│                   stt_gui_premium.py                            │
│              (UI Layer — Presentation)                          │
├─────────────────────────────────────────────────────────────────┤
│
│  Interfaz visual ───────────────────────→ Event handlers
│  (Cards, Buttons, Terminal)                 (Button clicks)
│
│  Data display ←─────────────────────── Backend results
│  (Stats, Chat messages)                  (Async updates)
│
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ (Import + instantiate)
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌──────────────────┐   ┌──────────────────┐
        │  RAG System      │   │  LLM Generator   │
        │  (stream_rag_    │   │  (stream_llm_    │
        │   advanced.py)   │   │   advanced.py)   │
        └──────────────────┘   └──────────────────┘
                │                       │
                └───────────┬───────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌──────────────────┐   ┌──────────────────┐
        │  Chat Display    │   │  Evaluation      │
        │  (stream_chat_   │   │  (llm_as_judge   │
        │   ui.py)         │   │   .py)           │
        └──────────────────┘   └──────────────────┘
```

---

## 📋 Checklist de Integración

### Fase 1: Importaciones Base
- [ ] Agregar imports en `stt_gui_premium.py`:
  ```python
  from stream_rag_advanced import AdvancedStreamRAG
  from stream_llm_advanced import AdvancedMultiBotGenerator
  from stream_chat_ui import ChatPanel
  from llm_as_judge import LLMJudge
  from faster_whisper import WhisperModel
  ```

### Fase 2: Inicialización de Componentes
- [ ] En `__init__` de `StreamMindAIPremium`:
  ```python
  self.rag_system = AdvancedStreamRAG()
  self.llm_generator = AdvancedMultiBotGenerator()
  self.evaluator = LLMJudge()
  self.whisper_model = WhisperModel("base")
  ```

### Fase 3: Conexión de Botones
- [ ] "Iniciar Simulación" → trigger `on_start_simulation()`
- [ ] "Test Ciego" → trigger `on_blind_test()`
- [ ] "Evaluar" → trigger `on_evaluate()`

### Fase 4: Flujo de Datos en Tiempo Real
- [ ] STT (Whisper) → TranscriptionTerminal
- [ ] RAG query → StatCard (RAG Memory)
- [ ] LLM generation → BotMessage (Chat IA Simulado)
- [ ] Evaluation → StatCard (Humanness Score)

### Fase 5: Validación y Testing
- [ ] Test end-to-end con audio real
- [ ] Verificar rendimiento (latencia <500ms)
- [ ] Validar actualización de UI en tiempo real

---

## 🔌 Conexiones Específicas

### 1. STT (Speech-to-Text) → Terminal

**Componente**: `TranscriptionTerminal`
**Fuente de datos**: `faster-whisper` + `pyaudio`

**Flujo**:
```python
# En on_start_simulation():
def on_start_simulation(self):
    # 1. Iniciar grabación
    self.audio_stream = self.start_recording()
    
    # 2. Transcribir con Whisper
    transcription = self.whisper_model.transcribe(self.audio_stream)
    
    # 3. Actualizar terminal (async)
    self.transcription_terminal.append_line(
        "[WHISPER] " + transcription['text']
    )
    
    # 4. Pasar a RAG
    await self.on_transcription_complete(transcription)
```

**UI Update Method**:
```python
def update_terminal(self, new_line):
    """Agregar línea a terminal sin bloquear UI"""
    self.transcription_terminal.add_text(new_line)
    self.transcription_terminal.scroll_to_bottom()
    self.window.update()  # Refresh UI
```

**Terminal Methods Needed**:
```python
# En TranscriptionTerminal class:
def append_line(self, text):
    """Add line to terminal display"""
    self.textbox.insert("end", text + "\n")
    self.scroll_to_bottom()

def scroll_to_bottom(self):
    """Auto-scroll to latest message"""
    self.textbox.see("end")

def clear(self):
    """Clear all text"""
    self.textbox.delete("1.0", "end")
```

---

### 2. RAG (Retrieval-Augmented Generation) → Memory Card

**Componente**: `StatCard` (RAG Memory)
**Fuente de datos**: `AdvancedStreamRAG`

**Flujo**:
```python
async def on_transcription_complete(self, transcription):
    """After STT completes, query RAG system"""
    
    # 1. Retrieve context from RAG
    context_result = await self.rag_system.retrieve_context(
        query=transcription['text'],
        top_k=10
    )
    
    # 2. Extract metrics
    similarity_scores = [item['similarity'] for item in context_result['context']]
    avg_similarity = sum(similarity_scores) / len(similarity_scores)
    
    # 3. Update UI
    self.rag_stat_card.update_value(
        label="Similarity",
        value=f"{avg_similarity:.2f}",
        unit="avg"
    )
    
    # 4. Store context for LLM
    self.current_context = context_result['context']
    
    # 5. Continue pipeline
    await self.on_rag_complete(context_result)
```

**Metrics to Display**:
```python
{
    "documents": len(self.rag_system.index),  # 1,570
    "latency_ms": measure_latency(retrieve_context),
    "similarity_avg": avg_similarity,
    "top_doc": context_result['context'][0]['text'],
}
```

---

### 3. LLM Generation → Chat Display

**Componente**: `BotMessage` (Chat IA Simulado)
**Fuente de datos**: `AdvancedMultiBotGenerator` + `NVIDIA NIM API`

**Flujo**:
```python
async def on_rag_complete(self, rag_result):
    """After RAG retrieval, generate comments with LLM"""
    
    # 1. Prepare LLM input
    prompt_context = "\n".join([
        doc['text'] for doc in self.current_context[:5]
    ])
    
    # 2. Generate 3 bot comments
    comments = await self.llm_generator.generate_comments(
        category="gaming",
        context=prompt_context,
        num_comments=3
    )
    
    # 3. Display each bot comment
    for i, (bot_name, comment) in enumerate(comments.items()):
        bot_color = self.BOT_COLORS[bot_name]
        
        self.chat_display.add_message(
            BotMessage(
                bot_name=bot_name,
                message=comment,
                color=bot_color
            )
        )
        
        # Async delay for dramatic effect (optional)
        await asyncio.sleep(0.5)
    
    # 4. Continue to evaluation
    await self.on_generation_complete(comments)
```

**Bot Color Mapping**:
```python
BOT_COLORS = {
    "HypeBot": "#FF6B6B",    # Rojo
    "CritiBot": "#51CF66",   # Verde
    "LurkerBot": "#A78BFA"   # Púrpura
}
```

**Message Display Methods**:
```python
# En chat_card:
def add_message(self, bot_message):
    """Add new BotMessage to chat display"""
    bot_message.pack(fill="x", padx=8, pady=4)
    self.content_frame.update()

def clear_messages(self):
    """Clear all messages"""
    for widget in self.content_frame.winfo_children():
        widget.destroy()
```

---

### 4. Evaluation → Analytics Card

**Componente**: `StatCard` (Humanness Score)
**Fuente de datos**: `LLMJudge`

**Flujo**:
```python
async def on_generation_complete(self, generated_comments):
    """After LLM generation, evaluate comments"""
    
    # 1. Evaluate each generated comment
    evaluation_scores = []
    
    for bot_name, comment in generated_comments.items():
        score = await self.evaluator.evaluate_comment(
            comment=comment,
            criteria=['naturalidad', 'coherencia', 'jerga']
        )
        evaluation_scores.append(score)
    
    # 2. Calculate average humanness
    avg_humanness = sum(evaluation_scores) / len(evaluation_scores)
    
    # 3. Compare with real comments
    real_comment_score = self.evaluator.evaluate_comment(
        comment=self.current_real_comment,
        criteria=['naturalidad', 'coherencia', 'jerga']
    )
    
    # 4. Calculate error rate (misclassification)
    error_rate = abs(avg_humanness - real_comment_score) / 100 * 100
    
    # 5. Update UI
    self.humanness_stat_card.update_values({
        "Real": f"{real_comment_score:.1f}",
        "Generated": f"{avg_humanness:.1f}",
        "Error Rate": f"{error_rate:.0f}%"
    })
    
    # 6. Update status
    self.sidebar_status.update(f"✓ Simulación completada ({error_rate:.0f}% error)")
```

**Evaluation Metrics**:
```python
{
    "real_score": 65.3,           # from labeled dataset
    "generated_score": 62.4,      # from LLM output
    "error_rate": 58,             # misclassification %
    "criteria_breakdown": {       # per-criterion scores
        "naturalidad": 64,
        "coherencia": 61,
        "jerga": 63,
        "longitud": 59,
        "personalidad": 62
    }
}
```

---

## 🔄 Async/Threading Considerations

### Problema
`stt_gui_premium.py` usa Tkinter, que requiere operaciones en el **thread principal**. Las llamadas a API y procesamiento son **I/O blocking**.

### Solución: Async Pattern

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class StreamMindAIPremium:
    def __init__(self, root):
        self.root = root
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.loop = asyncio.new_event_loop()
        
        # Start async event loop in background
        self.async_thread = threading.Thread(
            target=self._run_async_loop,
            daemon=True
        )
        self.async_thread.start()
    
    def _run_async_loop(self):
        """Run async event loop in background thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def schedule_coroutine(self, coro):
        """Schedule async operation without blocking UI"""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future
    
    def on_button_click(self):
        """Button handler (runs in main thread)"""
        # Schedule async work
        self.schedule_coroutine(self._async_work())
    
    async def _async_work(self):
        """Async work (runs in background)"""
        result = await self.llm_generator.generate_comments(...)
        
        # Update UI (must run in main thread)
        self.root.after(0, self._update_ui, result)
    
    def _update_ui(self, result):
        """Update UI (runs in main thread)"""
        self.chat_display.add_message(result)
```

### Arquitectura Recomendada

```
Main Thread (Tkinter)
    ├─ UI rendering
    ├─ Event handling
    └─ calls root.after() for updates

Background Thread (Async Event Loop)
    ├─ API calls (NVIDIA NIM)
    ├─ RAG queries
    ├─ LLM generation
    └─ Evaluation

Sync Pattern:
1. User clicks button (main thread)
2. Schedule async operation (executor)
3. Async op runs in background
4. Call root.after() to update UI
5. UI updates on main thread
```

---

## 📊 Data Structures for Integration

### STT Output
```python
{
    "text": "omegalul que funny el clip",
    "confidence": 0.87,
    "duration": 2.3,  # seconds
    "timestamp": "2024-05-15 14:32:10"
}
```

### RAG Output
```python
{
    "context": [
        {
            "text": "omegalul es slang para reírse",
            "similarity": 0.92,
            "source": "message_id_123",
            "category": "gaming"
        },
        ...  # up to 10 docs
    ],
    "latency_ms": 127,
    "query_embedding": [...512 dims...]
}
```

### LLM Output
```python
{
    "HypeBot": "OMEGALUL que funny xd",
    "CritiBot": "Análisis interesante del timing cómico",
    "LurkerBot": "xd"
}
```

### Evaluation Output
```python
{
    "comment": "OMEGALUL que funny xd",
    "scores": {
        "naturalidad": 75,      # 0-100
        "coherencia": 82,
        "jerga": 88,
        "longitud": 70,
        "personalidad": 80
    },
    "overall": 79,              # average
    "is_human_like": True,      # > threshold
    "confidence": 0.92
}
```

---

## 🛠️ Implementation Roadmap

### Sprint 1: Core Integration (2-3 horas)
- [ ] Add imports and class initialization
- [ ] Implement button event handlers
- [ ] Create data flow pipelines (methods)
- [ ] Add terminal update methods
- [ ] Test with mock data

### Sprint 2: Async/Threading (1-2 horas)
- [ ] Implement ThreadPoolExecutor
- [ ] Add asyncio event loop management
- [ ] Create schedule_coroutine() method
- [ ] Fix UI blocking issues
- [ ] Test with real API calls

### Sprint 3: Real API Integration (2-3 horas)
- [ ] Connect to Whisper STT
- [ ] Connect to NVIDIA NIM API
- [ ] Load FAISS RAG index
- [ ] Initialize evaluator
- [ ] End-to-end testing

### Sprint 4: Polish & Optimization (1-2 horas)
- [ ] Error handling & fallbacks
- [ ] Performance optimization
- [ ] UI refinement
- [ ] Comprehensive testing
- [ ] Documentation

**Tiempo Total Estimado**: 6-10 horas para integración completa

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] Each component initializes without errors
- [ ] Button handlers trigger callbacks
- [ ] Data structures serialize correctly
- [ ] Async operations complete

### Integration Tests
- [ ] STT → Terminal (end-to-end)
- [ ] RAG → Stats display
- [ ] LLM → Chat messages
- [ ] Evaluation → Analytics
- [ ] Full pipeline (start to finish)

### Performance Tests
- [ ] STT latency < 2 seconds
- [ ] RAG latency < 200ms
- [ ] LLM latency < 5 seconds
- [ ] Overall pipeline < 10 seconds
- [ ] UI remains responsive

### Visual Tests
- [ ] All cards render correctly
- [ ] Colors display accurately
- [ ] Terminal scrolls properly
- [ ] Messages align nicely
- [ ] No visual glitches

---

## 📝 Code Templates

### Template 1: Button Handler
```python
def on_button_clicked(self):
    """Handle button click event"""
    self.log_status("[INFO] Iniciando...")
    
    # Schedule async work
    future = self.schedule_coroutine(
        self._async_operation()
    )
    
    # Handle completion
    def on_complete(f):
        try:
            result = f.result()
            self._update_ui(result)
            self.log_status("[OK] Completado")
        except Exception as e:
            self.log_status(f"[ERROR] {str(e)}")
    
    future.add_done_callback(on_complete)

async def _async_operation(self):
    """Async work goes here"""
    result = await some_api_call()
    return result

def _update_ui(self, result):
    """Update UI with result"""
    # This runs on main thread
    self.some_widget.update_value(result)
```

### Template 2: Data Pipeline
```python
async def _pipeline_stagger_execution(self):
    """Execute pipeline phases sequentially with UI updates"""
    
    # Phase 1: STT
    self.log_status("[STT] Transcribiendo...")
    transcription = await self._transcribe()
    self.update_terminal(transcription)
    
    # Phase 2: RAG
    self.log_status("[RAG] Recuperando contexto...")
    context = await self._retrieve_context(transcription)
    self.update_rag_stats(context)
    
    # Phase 3: LLM
    self.log_status("[LLM] Generando comentarios...")
    comments = await self._generate_comments(context)
    self.update_chat_display(comments)
    
    # Phase 4: Evaluation
    self.log_status("[EVAL] Evaluando...")
    scores = await self._evaluate(comments)
    self.update_humanness_score(scores)
    
    self.log_status("[OK] Simulación completada")
```

---

## 🐛 Common Issues & Solutions

| Problema | Causa | Solución |
|----------|-------|----------|
| UI congelada | Blocking call en main thread | Use async/ThreadPoolExecutor |
| "NoneType" error | Componente no inicializado | Check init order |
| JSON error | numpy data types | Convert to Python native types |
| API timeout | Red lenta o servidor caído | Add retry logic + fallback |
| Terminal no actualiza | TextBox en thread diferente | Use root.after() |
| Mensajes duplicados | Append sin clear previo | Clear antes de agregar |

---

## 📚 Related Files

**Code Files**:
- `stt_gui_premium.py` - Main UI (modification target)
- `stream_rag_advanced.py` - RAG system
- `stream_llm_advanced.py` - LLM generator
- `llm_as_judge.py` - Evaluator
- `stream_chat_ui.py` - Chat component (reuse)

**Documentation**:
- `DESIGN.md` - UI design details
- `DOCUMENTATION.md` - Complete technical docs
- `INTERFACE_COMPARISON.md` - GUI comparison

---

## ✅ Success Criteria

- [x] Imports working without errors
- [x] Components initialize properly
- [ ] Buttons trigger handlers
- [ ] Data flows through pipeline
- [ ] UI updates in real-time
- [ ] No blocking/freezing
- [ ] Error handling robust
- [ ] All metrics display correctly
- [ ] Performance within targets
- [ ] End-to-end test passes

---

**Estado**: 📋 Planning complete, ready for implementation
**Versión**: Integration v1.0
**Fecha**: Mayo 2026

