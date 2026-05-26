# -*- coding: utf-8 -*-
"""
StreamMind IA — Premium UI Dashboard
=====================================
Interfaz futurista y elegante para simulación de engagement en streams.
Diseño inspirado en dashboards de IA modernos con glassmorphism y tecnología.

Paleta de colores premium:
- Sapphire: #3C507D (azul profundo)
- Royal Blue: #112250 (azul oscuro)
- Quicksand: #E0C58F (dorado elegante)
- Swan Wing: #F5F0E9 (blanco crema)
- Shellstone: #D9CBC2 (beige suave)

Características:
- Dark mode minimalista
- Glassmorphism sutil
- Sombras suaves y glow azul
- Tipografía futurista
- Animaciones smooth
- Sistema multiagente IA en tiempo real
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime
from typing import Optional, Dict, List
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ═══════════════════════════════════════════════════════════════════════════════
# PALETA DE COLORES PREMIUM
# ═══════════════════════════════════════════════════════════════════════════════

class PremiumColors:
    """Paleta de colores premium para StreamMind IA"""
    
    # Colores principales
    SAPPHIRE = "#3C507D"           # Azul profundo (botones, acentos)
    ROYAL_BLUE = "#112250"         # Azul oscuro (background)
    QUICKSAND = "#E0C58F"          # Dorado elegante (highlights)
    SWAN_WING = "#F5F0E9"          # Blanco crema (texto principal)
    SHELLSTONE = "#D9CBC2"         # Beige suave (texto secundario)
    
    # Colores derivados (basados en EDA)
    HYPE_BOT = "#FF6B6B"           # Rojo energético (HypeBot)
    CRITI_BOT = "#51CF66"          # Verde inteligente (CritiBot)
    LURKER_BOT = "#A78BFA"         # Púrpura misterioso (LurkerBot)
    
    # Neutrales
    BG_DARK = "#0A0E27"            # Fondo más oscuro
    BG_CARD = "#1A2145"            # Fondo de tarjetas
    BORDER_GLOW = "#3C507D"        # Brillo de bordes
    
    # Tonos de estado
    SUCCESS = "#51CF66"
    WARNING = "#FFD93D"
    ERROR = "#FF6B6B"
    INFO = "#4ECDC4"


class PremiumTheme:
    """Tema visual premium con glassmorphism y glow"""
    
    @staticmethod
    def configure_ctk():
        """Configura CustomTkinter con tema premium"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
    
    @staticmethod
    def card_style() -> Dict:
        """Estilo para tarjetas premium"""
        return {
            "fg_color": PremiumColors.BG_CARD,
            "border_color": PremiumColors.SAPPHIRE,
            "border_width": 1,
            "corner_radius": 16,
        }
    
    @staticmethod
    def button_primary() -> Dict:
        """Botón primario (azul brillante)"""
        return {
            "fg_color": PremiumColors.SAPPHIRE,
            "hover_color": "#5A7FB5",
            "text_color": PremiumColors.SWAN_WING,
            "border_width": 0,
            "corner_radius": 10,
            "font": ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        }
    
    @staticmethod
    def button_accent() -> Dict:
        """Botón acentuado (dorado)"""
        return {
            "fg_color": PremiumColors.QUICKSAND,
            "hover_color": "#F5D9A8",
            "text_color": PremiumColors.ROYAL_BLUE,
            "border_width": 0,
            "corner_radius": 10,
            "font": ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENTES PREMIUM
# ═══════════════════════════════════════════════════════════════════════════════

class PremiumCard(ctk.CTkFrame):
    """Tarjeta premium con glassmorphism y glow sutil"""
    
    def __init__(self, parent, title: str = "", **kwargs):
        super().__init__(parent, **PremiumTheme.card_style(), **kwargs)
        
        self.title = title
        
        # Crear estructura interna
        if title:
            self._create_header()
        
        # Contenedor para contenido
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=12)
    
    def _create_header(self):
        """Crea header con título y línea decorativa"""
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.pack(fill="x", padx=16, pady=(12, 8))
        
        # Título
        title_label = ctk.CTkLabel(
            header,
            text=self.title,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=PremiumColors.QUICKSAND,
        )
        title_label.pack(anchor="w")
        
        # Línea decorativa
        line = ctk.CTkFrame(
            header,
            fg_color=PremiumColors.SAPPHIRE,
            height=2,
        )
        line.pack(fill="x", pady=(4, 0))


class BotMessage(ctk.CTkFrame):
    """Mensaje de bot con estilo Twitch moderno"""
    
    def __init__(self, parent, bot_name: str, message: str, color: str, timestamp: Optional[str] = None, **kwargs):
        super().__init__(parent, **PremiumTheme.card_style(), **kwargs)
        
        self.bot_name = bot_name
        self.message = message
        self.color = color
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        
        self._create_layout()
    
    def _create_layout(self):
        """Crea layout del mensaje"""
        # Header con bot info
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 4))
        
        # Indicador de color (bot)
        indicator = ctk.CTkFrame(header, fg_color=self.color, width=6, height=6)
        indicator.pack(side="left", padx=(0, 8))
        
        # Nombre del bot
        name_label = ctk.CTkLabel(
            header,
            text=f"{self.bot_name}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.color,
        )
        name_label.pack(side="left")
        
        # Timestamp
        time_label = ctk.CTkLabel(
            header,
            text=self.timestamp,
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=PremiumColors.SHELLSTONE,
        )
        time_label.pack(side="right")
        
        # Mensaje
        msg_label = ctk.CTkLabel(
            self,
            text=self.message,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=PremiumColors.SWAN_WING,
            wraplength=300,
            justify="left",
        )
        msg_label.pack(fill="both", expand=True, padx=12, pady=(0, 8))


class TranscriptionTerminal(ctk.CTkFrame):
    """Terminal moderna para transcripción en vivo"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **PremiumTheme.card_style(), **kwargs)
        
        # Textbox con scroll
        self.text_widget = ctk.CTkTextbox(
            self,
            fg_color=PremiumColors.ROYAL_BLUE,
            text_color=PremiumColors.QUICKSAND,
            font=ctk.CTkFont(family="Courier New", size=11),
            border_width=0,
            corner_radius=0,
        )
        self.text_widget.pack(fill="both", expand=True, padx=1, pady=1)
        
        self.cursor_visible = True
        self._animate_cursor()
    
    def add_text(self, text: str):
        """Añade texto a la terminal"""
        self.text_widget.insert("end", text + "\n")
        self.text_widget.see("end")
    
    def clear(self):
        """Limpia el contenido"""
        self.text_widget.delete("1.0", "end")
    
    def _animate_cursor(self):
        """Anima el cursor parpadeante"""
        if self.cursor_visible:
            self.text_widget.insert("end", "█")
            self.cursor_visible = False
        else:
            # Remover última línea (simulación)
            self.cursor_visible = True
        
        # Repetir cada 500ms
        self.after(500, self._animate_cursor)


class StatCard(ctk.CTkFrame):
    """Tarjeta de estadística con valor y métrica"""
    
    def __init__(self, parent, label: str, value: str, unit: str = "", **kwargs):
        super().__init__(parent, **PremiumTheme.card_style(), **kwargs)
        
        # Contenedor vertical
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=12)
        
        # Label
        label_widget = ctk.CTkLabel(
            container,
            text=label,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=PremiumColors.SHELLSTONE,
        )
        label_widget.pack(anchor="w")
        
        # Value
        value_text = f"{value} {unit}".strip()
        value_widget = ctk.CTkLabel(
            container,
            text=value_text,
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=PremiumColors.QUICKSAND,
        )
        value_widget.pack(anchor="w", pady=(4, 0))


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR PREMIUM
# ═══════════════════════════════════════════════════════════════════════════════

class PremiumSidebar(ctk.CTkFrame):
    """Sidebar con configuración y controles"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=PremiumColors.ROYAL_BLUE,
            width=280,
            **kwargs
        )
        self.pack_propagate(False)
        
        # Scroll frame
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=PremiumColors.ROYAL_BLUE,
            label_text="Configuración",
            label_font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        self._create_sections()
    
    def _create_sections(self):
        """Crea secciones de configuración"""
        
        # SECCIÓN 1: Logo y titulo
        self._create_section_header("StreamMind IA")
        
        # SECCIÓN 2: Modelos STT
        self._create_section("STT (Whisper)")
        self._create_dropdown(
            "Modelo Whisper",
            ["Tiny", "Base", "Small", "Medium", "Large"],
            default="Base"
        )
        
        # SECCIÓN 3: LLM
        self._create_section("LLM (NVIDIA NIM)")
        self._create_dropdown(
            "Modelo",
            ["gemma-3n-e2b-it", "otros"],
            default="gemma-3n-e2b-it"
        )
        self._create_text_input("API Key", placeholder="Introduce tu key...")
        self._create_slider("Temperatura", 0.0, 1.0, 0.7)
        
        # SECCIÓN 4: Módulos
        self._create_section("Módulos")
        self._create_toggle("Cámara", True)
        self._create_toggle("STT", True)
        self._create_toggle("Chat IA", True)
        self._create_toggle("RAG", True)
        
        # SECCIÓN 5: Estadísticas
        self._create_section("Sistema")
        stat1 = ctk.CTkLabel(
            self.scroll_frame,
            text="Mensajes procesados: 0",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=PremiumColors.SHELLSTONE,
        )
        stat1.pack(anchor="w", padx=12, pady=4)
        
        stat2 = ctk.CTkLabel(
            self.scroll_frame,
            text="Latencia: 0ms",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=PremiumColors.SHELLSTONE,
        )
        stat2.pack(anchor="w", padx=12, pady=4)
    
    def _create_section_header(self, title: str):
        """Crea header de sección decorativo"""
        header = ctk.CTkLabel(
            self.scroll_frame,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=PremiumColors.QUICKSAND,
        )
        header.pack(anchor="w", padx=12, pady=(16, 8))
    
    def _create_section(self, title: str):
        """Crea sección con título"""
        section = ctk.CTkLabel(
            self.scroll_frame,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=PremiumColors.QUICKSAND,
        )
        section.pack(anchor="w", padx=12, pady=(12, 6))
    
    def _create_dropdown(self, label: str, options: List[str], default: str = ""):
        """Crea dropdown"""
        label_widget = ctk.CTkLabel(
            self.scroll_frame,
            text=label,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=PremiumColors.SWAN_WING,
        )
        label_widget.pack(anchor="w", padx=12, pady=(4, 2))
        
        dropdown = ctk.CTkOptionMenu(
            self.scroll_frame,
            values=options,
            fg_color=PremiumColors.SAPPHIRE,
            button_color=PremiumColors.SAPPHIRE,
            dropdown_fg_color=PremiumColors.BG_CARD,
            text_color=PremiumColors.SWAN_WING,
            font=ctk.CTkFont(family="Segoe UI", size=10),
        )
        dropdown.set(default)
        dropdown.pack(fill="x", padx=12, pady=(0, 8))
    
    def _create_text_input(self, label: str, placeholder: str = ""):
        """Crea input de texto"""
        label_widget = ctk.CTkLabel(
            self.scroll_frame,
            text=label,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=PremiumColors.SWAN_WING,
        )
        label_widget.pack(anchor="w", padx=12, pady=(4, 2))
        
        entry = ctk.CTkEntry(
            self.scroll_frame,
            placeholder_text=placeholder,
            fg_color=PremiumColors.BG_CARD,
            border_color=PremiumColors.SAPPHIRE,
            text_color=PremiumColors.SWAN_WING,
            border_width=1,
        )
        entry.pack(fill="x", padx=12, pady=(0, 8))
    
    def _create_slider(self, label: str, min_val: float, max_val: float, default: float):
        """Crea slider"""
        label_widget = ctk.CTkLabel(
            self.scroll_frame,
            text=f"{label}: {default}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=PremiumColors.SWAN_WING,
        )
        label_widget.pack(anchor="w", padx=12, pady=(4, 2))
        
        slider = ctk.CTkSlider(
            self.scroll_frame,
            from_=min_val,
            to=max_val,
            number_of_steps=20,
            fg_color=PremiumColors.SAPPHIRE,
            progress_color=PremiumColors.QUICKSAND,
            button_color=PremiumColors.QUICKSAND,
        )
        slider.set(default)
        slider.pack(fill="x", padx=12, pady=(0, 8))
    
    def _create_toggle(self, label: str, default: bool = True):
        """Crea toggle switch"""
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=4)
        
        toggle = ctk.CTkSwitch(
            frame,
            text=label,
            text_color=PremiumColors.SWAN_WING,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            onvalue=1,
            offvalue=0,
        )
        toggle.pack(anchor="w")
        
        if default:
            toggle.select()


# ═══════════════════════════════════════════════════════════════════════════════
# APLICACIÓN PRINCIPAL PREMIUM
# ═══════════════════════════════════════════════════════════════════════════════

class StreamMindAIPremium(ctk.CTk):
    """Aplicación principal StreamMind IA con interfaz premium"""
    
    def __init__(self):
        super().__init__()
        
        PremiumTheme.configure_ctk()
        
        # Configuración de ventana
        self.title("StreamMind IA — Premium Dashboard")
        self.geometry("1600x900")
        self.minsize(1400, 800)
        
        # Fondo
        self.configure(fg_color=PremiumColors.ROYAL_BLUE)
        
        # Crear layout
        self._create_layout()
    
    def _create_layout(self):
        """Crea layout principal con sidebar + contenido"""
        
        # Contenedor principal
        main_container = ctk.CTkFrame(self, fg_color=PremiumColors.ROYAL_BLUE)
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        sidebar = PremiumSidebar(main_container)
        sidebar.pack(side="left", fill="y", padx=0, pady=0)
        
        # Panel principal (scroll)
        main_panel = ctk.CTkScrollableFrame(
            main_container,
            fg_color=PremiumColors.ROYAL_BLUE,
        )
        main_panel.pack(side="right", fill="both", expand=True, padx=16, pady=16)
        
        # Título principal
        title = ctk.CTkLabel(
            main_panel,
            text="Dashboard Simulación de Engagement",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=PremiumColors.QUICKSAND,
        )
        title.pack(anchor="w", pady=(0, 16))
        
        # GRID DE TARJETAS
        self._create_cards_grid(main_panel)
    
    def _create_cards_grid(self, parent):
        """Crea grid de tarjetas principales"""
        
        # Fila 1: STT + Chat
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 16))
        
        # STT Card
        stt_card = PremiumCard(row1, title="Transcripción en Vivo (STT)", height=280)
        stt_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        self.terminal = TranscriptionTerminal(stt_card.content_frame)
        self.terminal.pack(fill="both", expand=True)
        
        # Demo: Agregar texto
        demo_texts = [
            "[SYSTEM] Sistema iniciado...",
            "[AUDIO] Escuchando micrófono...",
            "[WHISPER] Transcribiendo: 'Hola chat cómo están'",
            "[CONFIDENCE] 0.98",
        ]
        for text in demo_texts:
            self.terminal.add_text(text)
        
        # Chat Card
        chat_card = PremiumCard(row1, title="Chat IA Simulado", height=280)
        chat_card.pack(side="right", fill="both", expand=True, padx=(8, 0))
        
        # Mensajes de demo
        demo_messages = [
            ("HypeBot", "OMEGALUL QUÉ HACE", PremiumColors.HYPE_BOT),
            ("CritiBot", "Interesante estrategia", PremiumColors.CRITI_BOT),
            ("LurkerBot", "xd", PremiumColors.LURKER_BOT),
        ]
        
        for bot_name, msg, color in demo_messages:
            bot_msg = BotMessage(chat_card.content_frame, bot_name, msg, color)
            bot_msg.pack(fill="x", pady=(0, 8))
        
        # Fila 2: RAG + Analytics
        row2 = ctk.CTkFrame(parent, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 16))
        
        # RAG Card
        rag_card = PremiumCard(row2, title="Memoria Contextual (RAG)", height=250)
        rag_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        rag_info = ctk.CTkLabel(
            rag_card.content_frame,
            text="Documentos indexados: 1,570\nÚltima búsqueda: 127ms\nSimilaridad promedio: 0.78",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=PremiumColors.SWAN_WING,
            justify="left",
        )
        rag_info.pack(anchor="w")
        
        # Analytics Card
        analytics_card = PremiumCard(row2, title="Humanness Score & Métricas", height=250)
        analytics_card.pack(side="right", fill="both", expand=True, padx=(8, 0))
        
        analytics_grid = ctk.CTkFrame(analytics_card.content_frame, fg_color="transparent")
        analytics_grid.pack(fill="both", expand=True)
        
        # Mini stats
        stat1 = StatCard(analytics_grid, "Real Avg", "65.3", "/100")
        stat1.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        stat2 = StatCard(analytics_grid, "Generado Avg", "62.4", "/100")
        stat2.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        stat3 = StatCard(analytics_grid, "Tasa Error", "58", "%")
        stat3.pack(side="left", fill="both", expand=True, padx=0)
        
        # Fila 3: Botones de control
        control_row = ctk.CTkFrame(parent, fg_color="transparent")
        control_row.pack(fill="x", pady=(0, 16))
        
        btn_start = ctk.CTkButton(
            control_row,
            text="▶ Iniciar Simulación",
            command=self._on_start,
            width=150,
            **PremiumTheme.button_primary()
        )
        btn_start.pack(side="left", padx=(0, 8))
        
        btn_test = ctk.CTkButton(
            control_row,
            text="🎯 Test Ciego",
            command=self._on_blind_test,
            width=150,
            **PremiumTheme.button_primary()
        )
        btn_test.pack(side="left", padx=(0, 8))
        
        btn_eval = ctk.CTkButton(
            control_row,
            text="📊 Evaluar",
            command=self._on_evaluate,
            width=150,
            **PremiumTheme.button_accent()
        )
        btn_eval.pack(side="left")
    
    def _on_start(self):
        """Inicia la simulación"""
        self.terminal.clear()
        self.terminal.add_text("[START] Iniciando simulación...")
        self.terminal.add_text("[WHISPER] Cargando modelo...")
        self.terminal.add_text("[RAG] Recuperando contexto...")
        self.terminal.add_text("[LLM] Generando comentarios...")
    
    def _on_blind_test(self):
        """Abre el test ciego"""
        print("[INFO] Abriendo blind test interface...")
    
    def _on_evaluate(self):
        """Ejecuta evaluación"""
        self.terminal.clear()
        self.terminal.add_text("[EVAL] Evaluando calidad...")
        self.terminal.add_text("[JUDGE] Analizando 100 comentarios...")
        self.terminal.add_text("[RESULT] Humanness: 58%")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = StreamMindAIPremium()
    app.mainloop()
