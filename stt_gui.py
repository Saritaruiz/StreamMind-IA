# -*- coding: utf-8 -*-
"""
StreamMind — Panel de Control de Stream Inteligente
===================================================
Interfaz gráfica de estilo Apple ("modern & clean") construida con CustomTkinter.
Implementa el motor de transcripción en tiempo real (Stage 1) con volumen continuo y 
selección de entrada, memoria RAG (Stage 2), generación de comentarios con 
Google Gemma 3 en NVIDIA NIM (Stage 3), y un panel personalizable y responsivo.

Estructura del Proyecto:
- Stage 1: Transcripción de voz (WhisperSTTEngine) con volumen continuo y selección de entrada.
- Stage 2: Memoria Contextual RAG (StreamContextRAG) - Indexador virtual de transcripciones.
- Stage 3: Generación Multi-persona (MultiBotGenerator) - Integración real con NVIDIA NIM (Gemma 3).
- Stage 4: Chat e Interfaz en vivo (StreamMindSTTApp) - Dashboard con scroll inteligente.
"""

import queue
import threading
import time
import sys
import random
import json
import urllib.request
import urllib.error
from datetime import datetime

import numpy as np
import sounddevice as sd
import torch
import customtkinter as ctk

# Importar RAG y LLM avanzados
from stream_rag_advanced import AdvancedStreamRAG
from stream_llm_advanced import AdvancedMultiBotGenerator
from stream_chat_ui import ChatPanel

# ─── Configuración Estética Estilo Apple ──────────────────────────────────────

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Paleta de Colores Apple Dark
COLOR_BG_WINDOW = "#161617"       # Fondo de ventana principal
COLOR_BG_SIDEBAR = "#1d1d1f"      # Fondo de barra lateral
COLOR_BG_CARD = "#252529"         # Fondo de tarjetas/widgets
COLOR_BG_INNER = "#1c1c1e"        # Fondo de cajas de texto
COLOR_TEXT_PRIMARY = "#ffffff"    # Texto principal
COLOR_TEXT_SECONDARY = "#86868b"  # Texto secundario/silenciado
COLOR_ACCENT_BLUE = "#0a84ff"     # Azul brillante Apple
COLOR_BORDER = "#333336"          # Color de bordes finos

# Colores de Personalidades del Chat
COLOR_HYPE = "#ff453a"            # Rojo/Coral brillante para HypeBot
COLOR_CRITI = "#30d158"           # Verde brillante para CritiBot
COLOR_LURKER = "#bf5af2"          # Morado brillante para LurkerBot


# ─── STAGE 2: Memoria Contextual del Stream (RAG) — AVANZADO ──────────────────
# Ahora usamos AdvancedStreamRAG con FAISS + sentence-transformers
# (Ver stream_rag_advanced.py para detalles)


# ─── STAGE 3: Generación Multi-Persona con un solo LLM (NVIDIA NIM) ───────────

# ─── STAGE 3: Generación Multi-Persona con LLM Avanzado ─────────────────────

# Reemplazado por: AdvancedMultiBotGenerator (Ver stream_llm_advanced.py para detalles)
# Mejoras implementadas:
# - Prompts refinados por categoría de stream
# - Sistema de delays realista (2-5s entre bots)
# - Manejo robusto de errores y reintentos
# - Estadísticas de uso

# ─── STAGE 1: Motor STT (Faster-Whisper Engine) ───────────────────────────────

class WhisperSTTEngine:
    def __init__(self):
        self.model_size = "tiny"
        self.language = "es"
        
        # Parámetros VAD en tiempo real
        self.silence_threshold = 0.010
        self.silence_duration_threshold = 1.5
        self.max_audio_duration = 15.0
        
        # Dispositivo de entrada de audio (None = predeterminado)
        self.device_index = None
        
        # Instancias de componentes
        self.rag = None  # Se inicializa después de cargar el modelo
        self.generator = AdvancedMultiBotGenerator()  # LLM avanzado con categorías y delays
        
        # Estado
        self.model = None
        self.running = False
        self.recording = False
        self.running_audio = False
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Colas
        self.audio_queue = queue.Queue()
        self.job_queue = queue.Queue()
        self.transcription_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.level_queue = queue.Queue()
        
        self.audio_thread = None
        self.transcribe_thread = None
        self.job_thread = None

    def load_model(self, model_size):
        """Carga el modelo de Faster-Whisper de fondo."""
        self.status_queue.put(("loading", f"Cargando whisper-{model_size} ({self.device.upper()})..."))
        try:
            from faster_whisper import WhisperModel
            self.model_size = model_size
            compute_type = "float16" if self.device == "cuda" else "int8"
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=compute_type)
            
            # Inicializar RAG avanzado con FAISS
            self.status_queue.put(("loading", "Inicializando Sistema RAG avanzado con FAISS..."))
            self.rag = AdvancedStreamRAG()
            self.status_queue.put(("ready", f"Modelo '{model_size}' listo ({self.device.upper()}) + RAG FAISS ✓"))
        except Exception as e:
            self.status_queue.put(("error", f"Error al cargar modelo: {str(e)}"))

    def start_audio_monitoring(self):
        """Inicia el bucle persistente del micrófono para el medidor de volumen."""
        if self.running_audio:
            return
        self.running_audio = True
        self.audio_thread = threading.Thread(target=self._audio_stream_loop, daemon=True)
        self.audio_thread.start()

    def stop_audio_monitoring(self):
        """Detiene completamente el micrófono al cerrar la aplicación."""
        self.running_audio = False
        if self.audio_thread:
            self.audio_thread.join(timeout=1.0)

    def start_recording(self):
        """Inicia el VAD y procesamiento de transcripción (el audio ya se lee de fondo)."""
        if not self.model:
            self.status_queue.put(("error", "Por favor, carga un modelo primero."))
            return
            
        if self.recording:
            return

        self.recording = True
        self.running = True
        
        # Limpiar colas
        while not self.audio_queue.empty():
            self.audio_queue.get()
        while not self.job_queue.empty():
            self.job_queue.get()
            
        # Iniciar hilos del VAD y del job worker
        self.job_thread = threading.Thread(target=self._job_worker, daemon=True)
        self.job_thread.start()

        self.transcribe_thread = threading.Thread(target=self._transcribe_loop, daemon=True)
        self.transcribe_thread.start()
        
        self.status_queue.put(("recording", "Escuchando... habla ahora"))

    def stop_recording(self):
        """Detiene los hilos de transcripción manteniendo el micrófono activo de fondo."""
        if not self.recording:
            return
            
        self.recording = False
        self.running = False
        
        if self.transcribe_thread:
            self.transcribe_thread.join(timeout=1.0)
        if self.job_thread:
            self.job_thread.join(timeout=1.0)
            
        self.status_queue.put(("ready", "Grabación finalizada."))

    def _audio_stream_loop(self):
        """Captura audio en tiempo real de forma persistente y calcula volumen (RMS)."""
        sample_rate = 16000
        blocksize = int(sample_rate * 0.1)
        
        def callback(indata, frames, time_info, status):
            if status:
                sys.stderr.write(f"Mic Status: {status}\n")
            
            # Siempre se calcula el nivel de sonido para el medidor visual
            rms_val = float(np.sqrt(np.mean(indata**2)))
            self.level_queue.put(rms_val)
            
            # Sólo encolamos audio si Whisper está transcribiendo
            if self.recording:
                self.audio_queue.put((indata.copy(), rms_val))

        while self.running_audio:
            try:
                current_device = self.device_index
                with sd.InputStream(
                    device=self.device_index,
                    samplerate=sample_rate,
                    channels=1,
                    dtype="float32",
                    blocksize=blocksize,
                    callback=callback
                ):
                    # Mantener el stream abierto mientras no cambie el dispositivo seleccionado
                    while self.running_audio and self.device_index == current_device:
                        time.sleep(0.05)
            except Exception as e:
                self.status_queue.put(("error", f"Error de audio: {str(e)}"))
                time.sleep(1.0)  # Esperar 1 segundo antes de reintentar si se desconecta

    def _transcribe_loop(self):
        """Procesa el flujo de audio con algoritmo de VAD inteligente para segmentación."""
        pre_roll_blocks = []
        max_pre_roll = int(0.5 / 0.1)
        
        audio_buffer = []
        is_speaking = False
        silence_timer = 0.0
        last_transcribe_time = 0.0
        
        while self.running and self.recording:
            try:
                item = self.audio_queue.get(timeout=0.1)
                block, rms_val = item
                
                if rms_val > self.silence_threshold:
                    if not is_speaking:
                        is_speaking = True
                        audio_buffer = list(pre_roll_blocks)
                    audio_buffer.append(block)
                    silence_timer = 0.0
                else:
                    if is_speaking:
                        audio_buffer.append(block)
                        silence_timer += 0.1
                    else:
                        pre_roll_blocks.append(block)
                        if len(pre_roll_blocks) > max_pre_roll:
                            pre_roll_blocks.pop(0)
                
                # Borrador en tiempo real (cada 0.4s si estamos hablando)
                if is_speaking and len(audio_buffer) > 0:
                    current_time = time.time()
                    if current_time - last_transcribe_time > 0.4:
                        draft_audio = np.concatenate([b.flatten() for b in audio_buffer])
                        self.job_queue.put(("draft", draft_audio))
                        last_transcribe_time = current_time
                        
                # Commit si se supera el umbral de silencio o la duración máxima
                if is_speaking and (silence_timer >= self.silence_duration_threshold or (len(audio_buffer) * 0.1) >= self.max_audio_duration):
                    final_audio = np.concatenate([b.flatten() for b in audio_buffer])
                    self.job_queue.put(("final", final_audio))
                    audio_buffer = []
                    is_speaking = False
                    silence_timer = 0.0
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.status_queue.put(("error", f"Error en VAD: {str(e)}"))
                
        if audio_buffer and len(audio_buffer) > int(0.5 / 0.1):
            final_audio = np.concatenate([b.flatten() for b in audio_buffer])
            self.job_queue.put(("final", final_audio))

    def _job_worker(self):
        """Procesa las tareas de transcripción y coordina RAG + LLM."""
        while self.running:
            try:
                job = self.job_queue.get(timeout=0.1)
                job_type, audio_data = job
                
                if job_type == "draft" and not self.job_queue.empty():
                    self.job_queue.task_done()
                    continue
                    
                if job_type == "draft":
                    self._process_draft(audio_data)
                elif job_type == "final":
                    self._process_final(audio_data)
                    
                self.job_queue.task_done()
            except queue.Empty:
                continue

    def _process_draft(self, audio_data):
        try:
            segments, info = self.model.transcribe(
                audio_data,
                language=self.language if self.language != "auto" else None,
                beam_size=1,
                temperature=0.0
            )
            text = " ".join([seg.text for seg in segments]).strip()
            self.transcription_queue.put(("draft", text))
        except Exception as e:
            pass

    def _process_final(self, audio_data):
        self.status_queue.put(("transcribing", "Transcribiendo..."))
        try:
            segments, info = self.model.transcribe(
                audio_data,
                language=self.language if self.language != "auto" else None,
                beam_size=3,
                temperature=0.0
            )
            text = " ".join([seg.text for seg in segments]).strip()
            
            if text:
                timestamp = datetime.now().strftime("%H:%M:%S")
                # 1. Enviar transcripción a la UI
                self.transcription_queue.put(("final", (text, timestamp)))
                
                # 2. RAG: Guardar en la base vectorial con metadata
                self.rag.add_document(
                    text,
                    metadata={"timestamp": timestamp, "type": "streamer_transcription"}
                )
                
                # 3. RAG: Buscar contexto (retorna dict con similitudes)
                context_data = self.rag.retrieve_context(text, top_k=3, include_metadata=True)
                context = context_data["context"]  # Obtener solo el texto del contexto
                self.transcription_queue.put(("rag_log", (text, context)))
                
                # 4. LLM: Generar comentarios con contexto y categoría
                try:
                    # Valores predeterminados (pueden ser configurables después)
                    stream_category = "gaming"  # TODO: hacer configurable en la GUI
                    comments = self.generator.generate_comments(
                        text, 
                        context,
                        stream_category=stream_category,
                        include_delays=True  # Añade delays realistas entre bots
                    )
                    self.transcription_queue.put(("comments", comments))
                except Exception as llm_err:
                    self.status_queue.put(("error", f"LLM Error: {str(llm_err)}"))
            else:
                self.transcription_queue.put(("clear_draft", ""))
                
            self.status_queue.put(("recording", "Escuchando... habla ahora"))
        except Exception as e:
            self.status_queue.put(("error", f"Error del sistema: {str(e)}"))
            self.status_queue.put(("recording", "Escuchando... habla ahora"))


# ─── STAGE 4: Interfaz Gráfica (CustomTkinter App Estilo Apple) ────────────────

class StreamMindSTTApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de Ventana
        self.title("StreamMind IA — Panel de Control y Chat de Stream")
        self.geometry("1240x760")
        self.minsize(1050, 680)
        self.configure(fg_color=COLOR_BG_WINDOW)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Instanciar el Motor de Transcripción
        self.engine = WhisperSTTEngine()
        
        # Obtener lista de micrófonos de entrada sin duplicados de nombre
        self.mic_devices = {}
        self.get_microphones()
        
        # Iniciar el monitoreo persistente de audio
        self.engine.start_audio_monitoring()
        
        # Estado local
        self.transcriptions = []
        self.current_draft = ""
        self.rag_logs = []
        self.camera_active = False
        self.camera_index = 0
        self.camera_thread = None
        self.camera_devices = {}

        # Crear Interfaz
        self._create_sidebar()
        self._create_main_panel()

        # Cargar API Key desde .env
        env_key = self.load_api_key_from_env()
        if env_key:
            self.engine.generator.connect(env_key)
            self.entry_api.insert(0, env_key)
            self.led_llm.configure(fg_color="#30d158") # Verde

        # Aplicar layout inicializado
        self.apply_layout()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.poll_queues()

    def load_api_key_from_env(self):
        """Lee manualmente el archivo .env para recuperar la API Key de NVIDIA."""
        try:
            import os
            if os.path.exists(".env"):
                with open(".env", "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            k = k.strip().replace("'", "").replace('"', '')
                            v = v.strip().replace("'", "").replace('"', '')
                            if k.upper() in ["NVIDIA-API", "NVIDIA_API"]:
                                return v
        except Exception:
            pass
        return None

    def get_microphones(self):
        """Obtiene la lista de micrófonos de entrada disponibles filtrando nombres duplicados."""
        try:
            devices = sd.query_devices()
            seen_names = set()
            for i, d in enumerate(devices):
                if d['max_input_channels'] > 0:
                    name = d['name'].strip()
                    # Ignorar duplicados de nombre para una lista limpia
                    if name not in seen_names:
                        seen_names.add(name)
                        # Truncar nombres muy largos
                        display_name = f"{name[:30]}"
                        self.mic_devices[display_name] = i
        except Exception as e:
            pass
            
        if not self.mic_devices:
            self.mic_devices = {"Predeterminado": None}

    def get_cameras(self):
        """Detecta las cámaras físicas reales conectadas al sistema usando pygrabber si está disponible,
        con fallback a la enumeración OpenCV estándar."""
        cameras = []
        self.camera_devices = {}
        
        # 1. Intentar usar pygrabber para obtener los nombres reales de los dispositivos
        try:
            from pygrabber.dshow_graph import FilterGraph
            graph = FilterGraph()
            devices = graph.get_input_devices()
            if devices:
                for idx, name in enumerate(devices):
                    display_name = f"{name} ({idx})"
                    self.camera_devices[display_name] = idx
                    cameras.append(display_name)
        except Exception:
            pass
            
        # 2. Fallback a OpenCV estándar si pygrabber falla o no encuentra nada
        if not cameras:
            try:
                import cv2
                for idx in range(5):
                    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW if sys.platform == "win32" else None)
                    if cap.isOpened():
                        display_name = f"Cámara {idx}"
                        self.camera_devices[display_name] = idx
                        cameras.append(display_name)
                        cap.release()
            except Exception:
                pass
                
        # 3. Fallback final simulado
        if not cameras:
            display_name = "Cámara 0 (Simulada)"
            self.camera_devices[display_name] = 0
            cameras = [display_name]
            
        return cameras

    def _create_sidebar(self):
        """Crea la barra lateral izquierda usando CTkScrollableFrame para evitar overflow vertical."""
        self.sidebar = ctk.CTkScrollableFrame(
            self, 
            width=300, 
            corner_radius=0, 
            fg_color=COLOR_BG_SIDEBAR,
            scrollbar_button_color=COLOR_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT_BLUE
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Título principal
        self.lbl_title = ctk.CTkLabel(
            self.sidebar, 
            text="StreamMind IA", 
            font=ctk.CTkFont(family="SF Pro Display", size=26, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.lbl_title.grid(row=0, column=0, padx=16, pady=(15, 4), sticky="w")

        self.lbl_subtitle = ctk.CTkLabel(
            self.sidebar, 
            text="Simulador de Engagement con IA", 
            font=ctk.CTkFont(family="SF Pro Text", size=13),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_subtitle.grid(row=1, column=0, padx=16, pady=(0, 15), sticky="w")

        self._add_separator(self.sidebar, 2)

        # ── CONFIGURACIÓN DE MODELOS ──
        self.lbl_section_config = ctk.CTkLabel(
            self.sidebar, 
            text="CONFIGURACIÓN GENERAL", 
            font=ctk.CTkFont(family="SF Pro Text", size=11, weight="bold"),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_section_config.grid(row=3, column=0, padx=16, pady=(12, 8), sticky="w")

        # Whisper Model Size
        self.lbl_whisper = ctk.CTkLabel(self.sidebar, text="Whisper Model (STT):", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_whisper.grid(row=4, column=0, padx=16, pady=(4, 2), sticky="w")
        
        self.var_model = ctk.StringVar(value="tiny")
        self.combo_model = ctk.CTkOptionMenu(
            self.sidebar,
            values=["tiny", "base", "small", "medium"],
            variable=self.var_model,
            fg_color=COLOR_BG_CARD,
            button_color=COLOR_BG_CARD,
            button_hover_color=COLOR_BORDER,
            dropdown_fg_color=COLOR_BG_CARD,
            dropdown_hover_color=COLOR_ACCENT_BLUE,
            font=ctk.CTkFont(size=12)
        )
        self.combo_model.grid(row=5, column=0, padx=16, pady=(0, 10), sticky="ew")

        # NVIDIA NIM API Key
        self.lbl_api = ctk.CTkLabel(self.sidebar, text="NVIDIA NIM API Key:", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_api.grid(row=6, column=0, padx=16, pady=(4, 2), sticky="w")
        
        self.entry_api = ctk.CTkEntry(
            self.sidebar,
            placeholder_text="Introduce tu API Key...",
            show="*",
            fg_color=COLOR_BG_INNER,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=8,
            font=ctk.CTkFont(size=12)
        )
        self.entry_api.grid(row=7, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.entry_api.bind("<KeyRelease>", self.update_api_key)

        # NVIDIA NIM Model
        self.lbl_llm_model = ctk.CTkLabel(self.sidebar, text="NVIDIA NIM Model:", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_llm_model.grid(row=8, column=0, padx=16, pady=(4, 2), sticky="w")
        
        self.var_llm_model = ctk.StringVar(value="google/gemma-3n-e2b-it")
        self.combo_llm_model = ctk.CTkOptionMenu(
            self.sidebar,
            values=["google/gemma-3n-e2b-it", "meta/llama-3.1-8b-instruct", "meta/llama-3.1-70b-instruct"],
            variable=self.var_llm_model,
            fg_color=COLOR_BG_CARD,
            button_color=COLOR_BG_CARD,
            button_hover_color=COLOR_BORDER,
            dropdown_fg_color=COLOR_BG_CARD,
            dropdown_hover_color=COLOR_ACCENT_BLUE,
            font=ctk.CTkFont(size=12),
            command=self.change_llm_model
        )
        self.combo_llm_model.grid(row=9, column=0, padx=16, pady=(0, 10), sticky="ew")

        # Cargar Tokens de Canales (tokens.txt)
        self.lbl_tokens = ctk.CTkLabel(self.sidebar, text="CONEXIÓN CHAT (Twitch/Kick):", font=ctk.CTkFont(family="SF Pro Text", size=11, weight="bold"), text_color=COLOR_TEXT_SECONDARY)
        self.lbl_tokens.grid(row=10, column=0, padx=16, pady=(10, 4), sticky="w")
        
        self.btn_load_tokens = ctk.CTkButton(
            self.sidebar,
            text="📁 Subir tokens.txt",
            command=self.click_load_tokens,
            fg_color=COLOR_BG_CARD,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            corner_radius=10,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.btn_load_tokens.grid(row=11, column=0, padx=16, pady=(0, 3), sticky="ew")
        
        self.lbl_tokens_status = ctk.CTkLabel(
            self.sidebar, 
            text="Estado: tokens.txt no cargado", 
            font=ctk.CTkFont(size=11, slant="italic"), 
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w"
        )
        self.lbl_tokens_status.grid(row=12, column=0, padx=16, pady=(0, 10), sticky="ew")

        # Temperatura LLM
        self.lbl_temp = ctk.CTkLabel(self.sidebar, text="Temperatura del LLM: 0.70", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_temp.grid(row=13, column=0, padx=16, pady=(4, 2), sticky="w")
        
        self.slider_temp = ctk.CTkSlider(
            self.sidebar, 
            from_=0.0, 
            to=1.2, 
            number_of_steps=24,
            command=self.update_temp_label,
            progress_color=COLOR_ACCENT_BLUE
        )
        self.slider_temp.set(0.70)
        self.slider_temp.grid(row=14, column=0, padx=16, pady=(0, 10), sticky="ew")

        self._add_separator(self.sidebar, 15)

        # ── PERSONALIZAR PANEL ──
        self.lbl_section_custom = ctk.CTkLabel(
            self.sidebar, 
            text="PERSONALIZAR PANEL", 
            font=ctk.CTkFont(family="SF Pro Text", size=11, weight="bold"),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_section_custom.grid(row=16, column=0, padx=16, pady=(12, 6), sticky="w")

        self.lbl_layout = ctk.CTkLabel(self.sidebar, text="Organización / Layout:", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_layout.grid(row=17, column=0, padx=16, pady=(2, 2), sticky="w")

        self.var_layout = ctk.StringVar(value="Horizontal (Estándar)")
        self.combo_layout = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Horizontal (Estándar)", "Focus STT (Cámara + Chat Lateral)", "Focus Chat (Cámara + STT Lateral)"],
            variable=self.var_layout,
            fg_color=COLOR_BG_CARD,
            button_color=COLOR_BG_CARD,
            button_hover_color=COLOR_BORDER,
            dropdown_fg_color=COLOR_BG_CARD,
            dropdown_hover_color=COLOR_ACCENT_BLUE,
            font=ctk.CTkFont(size=11),
            command=self.apply_layout
        )
        self.combo_layout.grid(row=18, column=0, padx=16, pady=(0, 10), sticky="ew")

        # Switches para mostrar/ocultar paneles individuales
        self.switches_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.switches_frame.grid(row=19, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.switches_frame.grid_columnconfigure(0, weight=1)
        self.switches_frame.grid_columnconfigure(1, weight=1)

        self.sw_cam = ctk.CTkSwitch(self.switches_frame, text="Cámara", command=self.apply_layout, font=ctk.CTkFont(size=11), progress_color=COLOR_ACCENT_BLUE)
        self.sw_cam.select()
        self.sw_cam.grid(row=0, column=0, padx=(0, 5), pady=4, sticky="w")
        
        self.sw_stt = ctk.CTkSwitch(self.switches_frame, text="STT", command=self.apply_layout, font=ctk.CTkFont(size=11), progress_color=COLOR_ACCENT_BLUE)
        self.sw_stt.select()
        self.sw_stt.grid(row=0, column=1, padx=(5, 0), pady=4, sticky="w")
        
        self.sw_chat = ctk.CTkSwitch(self.switches_frame, text="Chat", command=self.apply_layout, font=ctk.CTkFont(size=11), progress_color=COLOR_ACCENT_BLUE)
        self.sw_chat.select()
        self.sw_chat.grid(row=1, column=0, padx=(0, 5), pady=4, sticky="w")
        
        self.sw_rag = ctk.CTkSwitch(self.switches_frame, text="RAG Logs", command=self.apply_layout, font=ctk.CTkFont(size=11), progress_color=COLOR_ACCENT_BLUE)
        self.sw_rag.select()
        self.sw_rag.grid(row=1, column=1, padx=(5, 0), pady=4, sticky="w")

        self._add_separator(self.sidebar, 20)

        # ── CONFIGURACIÓN DEL MICRÓFONO ──
        self.lbl_section_mic = ctk.CTkLabel(
            self.sidebar, 
            text="PARÁMETROS DE AUDIO (VAD)", 
            font=ctk.CTkFont(family="SF Pro Text", size=11, weight="bold"),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_section_mic.grid(row=21, column=0, padx=16, pady=(12, 8), sticky="w")

        # Umbral
        self.lbl_threshold = ctk.CTkLabel(self.sidebar, text="Umbral de Voz: 0.010", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_threshold.grid(row=22, column=0, padx=16, pady=(4, 2), sticky="w")
        
        self.slider_threshold = ctk.CTkSlider(self.sidebar, from_=0.002, to=0.040, number_of_steps=38, command=self.update_threshold_label, progress_color=COLOR_ACCENT_BLUE)
        self.slider_threshold.set(0.010)
        self.slider_threshold.grid(row=23, column=0, padx=16, pady=(0, 10), sticky="ew")

        # Selección de Micrófono
        self.lbl_mic_select = ctk.CTkLabel(self.sidebar, text="Seleccionar Micrófono:", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_PRIMARY)
        self.lbl_mic_select.grid(row=24, column=0, padx=16, pady=(4, 2), sticky="w")
        
        mic_options = list(self.mic_devices.keys())
        default_mic_name = mic_options[0] if mic_options else "Predeterminado"
        
        self.var_mic = ctk.StringVar(value=default_mic_name)
        self.combo_mic = ctk.CTkOptionMenu(
            self.sidebar,
            values=mic_options,
            variable=self.var_mic,
            fg_color=COLOR_BG_CARD,
            button_color=COLOR_BG_CARD,
            button_hover_color=COLOR_BORDER,
            dropdown_fg_color=COLOR_BG_CARD,
            dropdown_hover_color=COLOR_ACCENT_BLUE,
            font=ctk.CTkFont(size=12),
            command=self.change_microphone
        )
        self.combo_mic.grid(row=25, column=0, padx=16, pady=(0, 10), sticky="ew")

        # Nivel de Entrada Mic
        self.level_progressbar = ctk.CTkProgressBar(self.sidebar, progress_color=COLOR_ACCENT_BLUE, fg_color=COLOR_BORDER, height=6)
        self.level_progressbar.set(0.0)
        self.level_progressbar.grid(row=26, column=0, padx=16, pady=(0, 15), sticky="ew")

        # ── BOTONES PRINCIPALES DE CARGA Y CONTROL ──
        self.btn_load_model = ctk.CTkButton(
            self.sidebar, 
            text="Inicializar Whisper", 
            command=self.click_load_model,
            fg_color=COLOR_ACCENT_BLUE,
            hover_color="#0077ed",
            corner_radius=10,
            font=ctk.CTkFont(weight="bold")
        )
        self.btn_load_model.grid(row=27, column=0, padx=16, pady=(5, 6), sticky="ew")

        self.btn_record = ctk.CTkButton(
            self.sidebar,
            text="Iniciar Grabación",
            command=self.click_record,
            fg_color="#3a3a3c",
            hover_color="#48484a",
            state="disabled",
            corner_radius=10,
            font=ctk.CTkFont(weight="bold")
        )
        self.btn_record.grid(row=28, column=0, padx=16, pady=(0, 12), sticky="ew")

        # ── ESTADO DEL SISTEMA (LUCES LED) ──
        self.status_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_box.grid(row=29, column=0, padx=16, pady=(5, 5), sticky="ew")
        self.status_box.grid_columnconfigure(0, weight=1)

        self.led_stt = self._create_status_light(self.status_box, 0, "STT (Micrófono)", "#8e8e93")
        self.led_rag = self._create_status_light(self.status_box, 1, "RAG (Memoria)", "#8e8e93")
        self.led_llm = self._create_status_light(self.status_box, 2, "LLM (NVIDIA NIM)", "#8e8e93")

        # Texto de Estado General
        self.lbl_status = ctk.CTkLabel(
            self.sidebar, 
            text="Modelo no cargado", 
            font=ctk.CTkFont(size=12, slant="italic"), 
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w"
        )
        self.lbl_status.grid(row=30, column=0, padx=16, pady=(0, 15), sticky="ew")

    def _create_status_light(self, parent, row, label_text, color):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="w", pady=4)
        
        led = ctk.CTkFrame(frame, width=10, height=10, corner_radius=5, fg_color=color)
        led.grid(row=0, column=0, padx=(0, 10))
        
        lbl = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_SECONDARY)
        lbl.grid(row=0, column=1)
        return led

    def _add_separator(self, parent, row):
        sep = ctk.CTkFrame(parent, height=1, fg_color=COLOR_BORDER)
        sep.grid(row=row, column=0, padx=12, pady=0, sticky="ew")

    def _create_main_panel(self):
        """Crea el área de visualización principal estilo dashboard."""
        self.main_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self.main_panel.grid_rowconfigure(1, weight=1)
        self.main_panel.grid_rowconfigure(2, weight=0) # RAG log abajo
        self.main_panel.grid_columnconfigure(0, weight=1)

        # ── CABECERA ──
        self.header = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.header.grid_columnconfigure(0, weight=1)

        self.lbl_head_title = ctk.CTkLabel(
            self.header, 
            text="Panel de Control del Stream", 
            font=ctk.CTkFont(family="SF Pro Display", size=22, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.lbl_head_title.grid(row=0, column=0, sticky="w")

        self.btn_clear = ctk.CTkButton(
            self.header, 
            text="Vaciar Pantallas", 
            command=self.clear_all_history,
            fg_color="#3a3a3c",
            hover_color="#48484a",
            width=130,
            corner_radius=8,
            font=ctk.CTkFont(size=12)
        )
        self.btn_clear.grid(row=0, column=1, sticky="e")

        # ── CONTENEDOR DE CÁMARA, TRANSCRIPCIÓN Y CHAT (FILA 1) ──
        self.split_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        self.split_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 16))

        # 📹 TARJETA DE CÁMARA
        self.card_camera = ctk.CTkFrame(self.split_frame, fg_color=COLOR_BG_CARD, border_width=1, border_color=COLOR_BORDER, corner_radius=12)
        self.card_camera.grid_rowconfigure(1, weight=1)
        self.card_camera.grid_columnconfigure(0, weight=1)

        self.lbl_camera_title = ctk.CTkLabel(
            self.card_camera, 
            text="📹 Cámara del Streamer", 
            font=ctk.CTkFont(family="SF Pro Text", size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.lbl_camera_title.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        # Contenedor para el feed de video
        self.video_container = ctk.CTkFrame(self.card_camera, fg_color=COLOR_BG_INNER, corner_radius=8)
        self.video_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))
        self.video_container.grid_rowconfigure(0, weight=1)
        self.video_container.grid_columnconfigure(0, weight=1)

        self.lbl_video_feed = ctk.CTkLabel(
            self.video_container,
            text="📹 Cámara Desactivada\n(Presiona Activar)",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_video_feed.grid(row=0, column=0, sticky="nsew")

        # Controles de la cámara
        self.camera_controls = ctk.CTkFrame(self.card_camera, fg_color="transparent")
        self.camera_controls.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.camera_controls.grid_columnconfigure(0, weight=1)
        self.camera_controls.grid_columnconfigure(1, weight=1)

        # Obtener lista real de cámaras conectadas
        camera_list = self.get_cameras()
        self.combo_camera = ctk.CTkOptionMenu(
            self.camera_controls,
            values=camera_list,
            fg_color=COLOR_BG_INNER,
            button_color=COLOR_BG_INNER,
            button_hover_color=COLOR_BORDER,
            dropdown_fg_color=COLOR_BG_CARD,
            dropdown_hover_color=COLOR_ACCENT_BLUE,
            font=ctk.CTkFont(size=11),
            command=self.change_camera_device
        )
        self.combo_camera.set(camera_list[0])
        self.combo_camera.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.btn_camera = ctk.CTkButton(
            self.camera_controls,
            text="Activar",
            command=self.toggle_camera,
            fg_color=COLOR_ACCENT_BLUE,
            hover_color="#0077ed",
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.btn_camera.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # 🎙️ TARJETA DE STREAMER
        self.card_stt = ctk.CTkFrame(self.split_frame, fg_color=COLOR_BG_CARD, border_width=1, border_color=COLOR_BORDER, corner_radius=12)
        self.card_stt.grid_rowconfigure(1, weight=1)
        self.card_stt.grid_columnconfigure(0, weight=1)

        self.lbl_stt_title = ctk.CTkLabel(
            self.card_stt, 
            text="🎙️ Transcripción en Vivo (Streamer)", 
            font=ctk.CTkFont(family="SF Pro Text", size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.lbl_stt_title.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        self.txt_stt = ctk.CTkTextbox(
            self.card_stt, 
            fg_color=COLOR_BG_INNER,
            border_width=0,
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            border_spacing=10
        )
        self.txt_stt.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.txt_stt.tag_config("draft", foreground="#e67e22")
        self.txt_stt.insert("1.0", "(Esperando inicio de grabación...)\n")
        self.txt_stt.configure(state="disabled")

        # 💬 TARJETA DEL CHAT MEJORADO
        self.card_chat = ctk.CTkFrame(self.split_frame, fg_color=COLOR_BG_CARD, border_width=1, border_color=COLOR_BORDER, corner_radius=12)
        self.card_chat.grid_rowconfigure(1, weight=1)
        self.card_chat.grid_columnconfigure(0, weight=1)

        self.lbl_chat_title = ctk.CTkLabel(
            self.card_chat, 
            text="💬 Chat en Vivo (Bots con Delays)", 
            font=ctk.CTkFont(family="SF Pro Text", size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.lbl_chat_title.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        # Panel de chat mejorado con colores y animaciones
        self.chat_panel = ChatPanel(self.card_chat, height=350)
        self.chat_panel.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.chat_panel.add_system_message("Chat inicializado. Presiona Grabar para comenzar.")

        # ── TARJETA DEL LOG DEL CONTEXTO RAG (FILA 2) ──
        self.card_rag = ctk.CTkFrame(self.main_panel, fg_color=COLOR_BG_CARD, border_width=1, border_color=COLOR_BORDER, corner_radius=12)
        self.card_rag.grid_rowconfigure(1, weight=1)
        self.card_rag.grid_columnconfigure(0, weight=1)

        self.lbl_rag_title = ctk.CTkLabel(
            self.card_rag, 
            text="🔍 Visor de Memoria RAG (Contexto Recuperado para el LLM)", 
            font=ctk.CTkFont(family="SF Pro Text", size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.lbl_rag_title.grid(row=0, column=0, padx=16, pady=(10, 4), sticky="w")

        self.txt_rag_log = ctk.CTkTextbox(
            self.card_rag,
            fg_color=COLOR_BG_INNER,
            border_width=0,
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            border_spacing=8,
            height=120
        )
        self.txt_rag_log.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.txt_rag_log.insert("1.0", "--- Las búsquedas del RAG aparecerán aquí cuando terminen las frases ---\n")
        self.txt_rag_log.configure(state="disabled")

    # ── Sincronizadores en Tiempo Real ──

    def update_threshold_label(self, val):
        self.lbl_threshold.configure(text=f"Umbral de Voz: {val:.3f}")
        self.engine.silence_threshold = val

    def update_temp_label(self, val):
        self.lbl_temp.configure(text=f"Temperatura del LLM: {val:.2f}")
        self.engine.generator.temperature = val

    def update_api_key(self, event):
        key = self.entry_api.get().strip()
        connected = self.engine.generator.connect(key)
        if connected:
            self.led_llm.configure(fg_color="#30d158")
            if hasattr(self, 'chat_panel'):
                self.chat_panel.add_system_message("API Key configurada - Bots habilitados")
        else:
            self.led_llm.configure(fg_color="#8e8e93")
            if hasattr(self, 'chat_panel'):
                self.chat_panel.add_system_message("API Key requerida para usar los bots")

    def change_microphone(self, display_name):
        """Actualiza el micrófono activo seleccionado."""
        device_idx = self.mic_devices.get(display_name, None)
        self.engine.device_index = device_idx

    def change_llm_model(self, model_name):
        """Cambia el modelo LLM usado en NVIDIA NIM."""
        self.engine.generator.model_name = model_name

    # ── Gestor de Layout Personalizado (Manejo Responsivo Estable) ──

    def apply_layout(self, *args):
        """Aplica la distribución y visibilidad de los paneles de forma fluida y sin flicker."""
        # 1. Ocultar todas las tarjetas primero
        self.card_camera.grid_forget()
        self.card_stt.grid_forget()
        self.card_chat.grid_forget()
        self.card_rag.grid_forget()
        
        # Resetear pesos y configuraciones de filas/columnas del split_frame
        for i in range(4):
            self.split_frame.grid_columnconfigure(i, weight=0, minsize=0)
            self.split_frame.grid_rowconfigure(i, weight=0, minsize=0)
            
        # Obtener valores de switches
        show_cam = self.sw_cam.get()
        show_stt = self.sw_stt.get()
        show_chat = self.sw_chat.get()
        show_rag = self.sw_rag.get()
        
        layout = self.var_layout.get()
        
        # Si no hay ningún panel principal seleccionado, salir
        if not (show_cam or show_stt or show_chat):
            return
            
        # Posicionar RAG logs abajo si está activo
        if show_rag:
            self.card_rag.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
            self.main_panel.grid_rowconfigure(2, weight=0)
        else:
            self.main_panel.grid_rowconfigure(2, weight=0)

        # --- APLICAR PRESET DE ORGANIZACIÓN ---
        if layout == "Horizontal (Estándar)":
            active_cols = []
            if show_cam:
                active_cols.append((self.card_camera, 280))
            if show_stt:
                active_cols.append((self.card_stt, 0))
            if show_chat:
                active_cols.append((self.card_chat, 0))
                
            for idx, (widget, minsize) in enumerate(active_cols):
                widget.grid(row=0, column=idx, sticky="nsew", padx=(0, 10 if idx < len(active_cols)-1 else 0), pady=0)
                # Dar peso a STT y Chat, Cámara mantiene tamaño mínimo fijo si es visible
                weight = 0 if widget == self.card_camera else 1
                self.split_frame.grid_columnconfigure(idx, weight=weight, minsize=minsize)
                
            self.split_frame.grid_rowconfigure(0, weight=1)
            
        elif layout == "Focus STT (Cámara + Chat Lateral)":
            # STT Izquierda grande, Cámara y Chat apilados a la derecha
            if show_stt:
                self.card_stt.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10), pady=0)
                self.split_frame.grid_columnconfigure(0, weight=2)
                
            right_row = 0
            if show_cam:
                self.card_camera.grid(row=right_row, column=1, sticky="nsew", padx=0, pady=(0, 10 if show_chat else 0))
                right_row += 1
            if show_chat:
                self.card_chat.grid(row=right_row, column=1, sticky="nsew", padx=0, pady=0)
                
            self.split_frame.grid_columnconfigure(1, weight=1)
            self.split_frame.grid_rowconfigure(0, weight=1)
            if right_row > 1:
                self.split_frame.grid_rowconfigure(1, weight=1)
                
        elif layout == "Focus Chat (Cámara + STT Lateral)":
            # Cámara y STT apilados a la izquierda, Chat derecha grande
            left_row = 0
            if show_cam:
                self.card_camera.grid(row=left_row, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10 if show_stt else 0))
                left_row += 1
            if show_stt:
                self.card_stt.grid(row=left_row, column=0, sticky="nsew", padx=(0, 10), pady=0)
                
            self.split_frame.grid_columnconfigure(0, weight=1, minsize=280 if show_cam else 0)
            
            if show_chat:
                self.card_chat.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=0, pady=0)
                self.split_frame.grid_columnconfigure(1, weight=2)
                
            self.split_frame.grid_rowconfigure(0, weight=1)
            if left_row > 1:
                self.split_frame.grid_rowconfigure(1, weight=1)

    # ── Acciones e Hilos de Control ──

    def click_load_tokens(self):
        """Maneja la carga del archivo tokens.txt para conexión de bots."""
        from tkinter import filedialog, messagebox
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo tokens.txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            import os
            filename = os.path.basename(file_path)
            self.lbl_tokens_status.configure(
                text=f"✓ {filename} cargado", 
                text_color="#30d158"
            )
            messagebox.showinfo(
                "Tokens de Chat Cargados", 
                f"Archivo '{filename}' seleccionado correctamente.\n\nEl sistema usará estos tokens de conexión para interactuar en Twitch o Kick automáticamente."
            )

    def click_load_model(self):
        model_size = self.var_model.get()
        self.btn_load_model.configure(state="disabled")
        self.combo_model.configure(state="disabled")
        
        t = threading.Thread(target=self.engine.load_model, args=(model_size,), daemon=True)
        t.start()

    def click_record(self):
        if not self.engine.recording:
            # Sincronizar parámetros
            self.engine.silence_threshold = self.slider_threshold.get()
            self.engine.generator.temperature = self.slider_temp.get()
            self.engine.generator.model_name = self.var_llm_model.get()
            self.engine.generator.connect(self.entry_api.get().strip())
            
            # Sincronizar micrófono seleccionado
            selected_mic = self.var_mic.get()
            self.engine.device_index = self.mic_devices.get(selected_mic, None)
            
            self.engine.start_recording()
        else:
            self.btn_record.configure(state="disabled", text="Deteniendo...")
            self.engine.stop_recording()

    # ── Cámara de Video (Real con OpenCV / Simulada con PIL) ──

    def change_camera_device(self, val):
        """Actualiza la cámara activa seleccionada."""
        idx = self.camera_devices.get(val, 0)
        self.camera_index = idx
            
        if self.camera_active:
            # Si ya está activa, reiniciar el feed con el nuevo índice
            self.camera_active = False
            self.after(200, self.toggle_camera)

    def toggle_camera(self):
        """Activa o desactiva la captura de la cámara en vivo."""
        if not self.camera_active:
            self.camera_active = True
            self.btn_camera.configure(text="Desactivar", fg_color="#ff453a", hover_color="#ff3b30")
            self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
            self.camera_thread.start()
        else:
            self.camera_active = False
            self.btn_camera.configure(text="Activar", fg_color=COLOR_ACCENT_BLUE, hover_color="#0077ed")
            self.lbl_video_feed.configure(image=None, text="📹 Cámara Desactivada\n(Presiona Activar)")

    def _camera_loop(self):
        """Captura frames de la cámara real si está instalada, de lo contrario simula la cámara."""
        try:
            import cv2
            from PIL import Image
            
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW if sys.platform == "win32" else None)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            
            if not cap.isOpened():
                raise RuntimeError("No se pudo abrir el dispositivo de cámara.")
                
            while self.camera_active:
                ret, frame = cap.read()
                if not ret:
                    break
                
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb_frame = cv2.flip(rgb_frame, 1) # Espejo
                
                img = Image.fromarray(rgb_frame)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 180))
                
                self.after(0, lambda img_obj=ctk_img: self.lbl_video_feed.configure(image=img_obj, text=""))
                time.sleep(0.03) # ~30 FPS
                
            cap.release()
            
        except Exception as e:
            # Fallback a cámara animada/simulada
            self._run_simulated_camera()

    def _run_simulated_camera(self):
        """Simula una transmisión de cámara con interfaz HUD cyberpunk (PIL)."""
        from PIL import Image, ImageDraw
        frame_num = 0
        while self.camera_active:
            img = Image.new("RGB", (320, 240), color="#1c1c1e")
            draw = ImageDraw.Draw(img)
            
            # Dibujar contorno y grid del visor
            draw.rectangle([10, 10, 310, 230], outline="#333336", width=2)
            draw.line([160, 10, 160, 230], fill="#252529", width=1)
            draw.line([10, 120, 310, 120], fill="#252529", width=1)
            
            # Esquinas del visor
            draw.line([25, 20, 15, 20, 15, 40], fill="#86868b", width=2)
            draw.line([295, 20, 305, 20, 305, 40], fill="#86868b", width=2)
            draw.line([15, 220, 15, 200, 25, 220], fill="#86868b", width=2)
            draw.line([295, 220, 305, 220, 305, 200], fill="#86868b", width=2)
            
            # Indicador de Grabación Parpadeante
            rec_color = "#ff453a" if (frame_num // 8) % 2 == 0 else "#48484a"
            draw.ellipse([25, 30, 37, 42], fill=rec_color)
            draw.text((45, 31), "LIVE - SIMULADO", fill="#ffffff")
            
            # Nivel de batería simulado
            draw.rectangle([265, 30, 290, 42], outline="#86868b", width=1)
            draw.rectangle([267, 32, 283, 40], fill="#30d158")
            draw.rectangle([290, 33, 292, 39], fill="#86868b")
            
            # Dibujar forma de onda en el centro para dar sensación de actividad
            points = []
            for x in range(50, 270):
                y = 120 + int(15 * np.sin((x + frame_num * 5) * 0.05) * np.cos((x - frame_num * 2) * 0.02))
                points.append((x, y))
            if len(points) > 1:
                draw.line(points, fill=COLOR_ACCENT_BLUE, width=2)
                
            # Nivel de audio del micrófono en la esquina inferior izquierda
            audio_h = 10 + int(30 * abs(np.sin(frame_num * 0.1)))
            draw.rectangle([25, 170, 32, 210], fill="#252529")
            draw.rectangle([25, 210 - audio_h, 32, 210], fill="#0a84ff")
            draw.text((40, 185), "MIC IN", fill="#86868b")
            
            # Convertir a CTkImage para que escale bien
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 180))
            self.after(0, lambda img_obj=ctk_img: self.lbl_video_feed.configure(image=img_obj, text=""))
            
            frame_num += 1
            time.sleep(0.04) # ~25 FPS

    # ── Simulación de Chat con Delays Artificiales (Stage 3 + 4) ──

    def schedule_comments(self, comments):
        """Planifica las apariciones de los bots en el chat usando delays del LLM."""
        # Usar delays del LLM si existen, sino usar defaults
        delays = comments.get("delays", {
            "HypeBot": 2,
            "CritiBot": 3,
            "LurkerBot": 4
        })
        
        # Convertir segundos a milisegundos para self.after()
        delay_hype_ms = delays.get("HypeBot", 2) * 1000
        delay_criti_ms = delays.get("CritiBot", 3) * 1000
        delay_lurker_ms = delays.get("LurkerBot", 4) * 1000

        # Programar apariciones con animación de delays
        self.after(delay_hype_ms, lambda: self.post_to_chat("HypeBot", comments["HypeBot"], delays["HypeBot"]))
        self.after(delay_criti_ms, lambda: self.post_to_chat("CritiBot", comments["CritiBot"], delays["CritiBot"]))
        self.after(delay_lurker_ms, lambda: self.post_to_chat("LurkerBot", comments["LurkerBot"], delays["LurkerBot"]))

    def post_to_chat(self, bot_name, message, delay=0):
        """Inserta un comentario en el chat con animación de delays."""
        # Usar el nuevo ChatPanel mejorado
        self.chat_panel.add_message(bot_name, message, delay=delay)

    # ── Manejo de Transcripciones y RAG logs ──

    def add_transcription(self, text, timestamp):
        self.transcriptions.append({"time": timestamp, "text": text})
        self.redraw_transcriptions()

    def add_rag_log(self, query, context):
        self.txt_rag_log.configure(state="normal")
        self.txt_rag_log.insert("end", f"\n[RAG Query]: '{query}'\n")
        self.txt_rag_log.insert("end", f"[Contexto Recuperado]:\n{context}\n")
        self.txt_rag_log.insert("end", "-" * 60 + "\n")
        self.txt_rag_log.configure(state="disabled")
        self.txt_rag_log.see("end")

    def redraw_transcriptions(self):
        self.txt_stt.configure(state="normal")
        self.txt_stt.delete("1.0", "end")

        for entry in self.transcriptions:
            self.txt_stt.insert("end", f"[{entry['time']}]  {entry['text']}\n\n")
        
        if self.current_draft:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.txt_stt.insert("end", f"[{timestamp}]  {self.current_draft} ...\n\n", "draft")

        self.txt_stt.configure(state="disabled")
        self.txt_stt.see("end")

    def clear_all_history(self):
        """Limpia todo el historial de la pantalla y el vector store virtual."""
        self.transcriptions = []
        self.current_draft = ""
        self.engine.rag.documents = []
        
        self.txt_stt.configure(state="normal")
        self.txt_stt.delete("1.0", "end")
        self.txt_stt.insert("1.0", "(Esperando grabación...)\n")
        self.txt_stt.configure(state="disabled")
        
        # Usar nuevo panel de chat
        self.chat_panel.clear_chat()

        self.txt_rag_log.configure(state="normal")
        self.txt_rag_log.delete("1.0", "end")
        self.txt_rag_log.insert("1.0", "--- Las búsquedas del RAG aparecerán aquí cuando terminen las frases ---\n")
        self.txt_rag_log.configure(state="disabled")

    # ── Gestión de Hilos y Estado (Polling) ──

    def poll_queues(self):
        """Bucle periódico en el hilo principal para actualizar la UI."""
        # 1. Indicador de volumen del micrófono
        latest_level = None
        while not self.engine.level_queue.empty():
            try:
                latest_level = self.engine.level_queue.get_nowait()
            except queue.Empty:
                break
        
        if latest_level is not None:
            display_val = min(latest_level / 0.05, 1.0)
            self.level_progressbar.set(display_val)
            if latest_level > self.engine.silence_threshold:
                self.level_progressbar.configure(progress_color="#e74c3c")
            else:
                self.level_progressbar.configure(progress_color=COLOR_ACCENT_BLUE)

        # 2. Actualizar estados del sistema
        while not self.engine.status_queue.empty():
            try:
                status_type, status_msg = self.engine.status_queue.get_nowait()
                self._update_ui_status(status_type, status_msg)
            except queue.Empty:
                break

        # 3. Procesar datos del pipeline
        has_stt_changes = False
        while not self.engine.transcription_queue.empty():
            try:
                msg_type, data = self.engine.transcription_queue.get_nowait()
                
                if len(self.transcriptions) == 0 and self.current_draft == "":
                    self.txt_stt.configure(state="normal")
                    self.txt_stt.delete("1.0", "end")
                    self.txt_stt.configure(state="disabled")
                
                if msg_type == "draft":
                    self.current_draft = data
                    has_stt_changes = True
                elif msg_type == "final":
                    text, timestamp = data
                    self.transcriptions.append({"time": timestamp, "text": text})
                    self.current_draft = ""
                    has_stt_changes = True
                elif msg_type == "clear_draft":
                    self.current_draft = ""
                    has_stt_changes = True
                elif msg_type == "rag_log":
                    query, context = data
                    self.add_rag_log(query, context)
                elif msg_type == "comments":
                    self.schedule_comments(data)
            except queue.Empty:
                break
                
        if has_stt_changes:
            self.redraw_transcriptions()

        self.after(40, self.poll_queues)

    def _update_ui_status(self, status_type, message):
        self.lbl_status.configure(text=message)

        if status_type == "loading":
            self.btn_load_model.configure(state="disabled", text="Cargando...")
            self.combo_model.configure(state="disabled")
            self.led_stt.configure(fg_color="#ffcc00")
            
        elif status_type == "ready":
            self.btn_load_model.configure(state="normal", text="Re-inicializar STT")
            self.combo_model.configure(state="normal")
            self.btn_record.configure(
                state="normal", 
                text="Iniciar Grabación", 
                fg_color=COLOR_ACCENT_BLUE, 
                hover_color="#0077ed"
            )
            self.led_stt.configure(fg_color="#30d158")
            self.led_rag.configure(fg_color="#30d158")
            
        elif status_type == "recording":
            self.btn_record.configure(
                state="normal", 
                text="Detener Grabación", 
                fg_color="#ff453a", 
                hover_color="#ff3b30"
            )
            self.led_stt.configure(fg_color="#ff453a")
            
        elif status_type == "transcribing":
            self.lbl_status.configure(text="Generando comentarios...")
            
        elif status_type == "error":
            self.btn_load_model.configure(state="normal", text="Reintentar Cargar")
            self.combo_model.configure(state="normal")
            self.btn_record.configure(state="disabled", fg_color="#3a3a3c")
            self.led_stt.configure(fg_color="#ff3b30")
            
            from tkinter import messagebox
            messagebox.showerror("Error del Sistema", message)

    def on_closing(self):
        self.camera_active = False
        self.engine.stop_audio_monitoring()
        if self.engine.recording:
            self.engine.stop_recording()
        self.destroy()


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    app = StreamMindSTTApp()
    app.mainloop()

if __name__ == "__main__":
    main()
