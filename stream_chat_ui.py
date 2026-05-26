# -*- coding: utf-8 -*-
"""
StreamMind — Advanced Chat UI Component
========================================

Panel de chat mejorado con:
- Colores distintos por bot (HypeBot rojo, CritiBot verde, LurkerBot púrpura)
- Display de delays en tiempo real
- Auto-scroll inteligente
- Timestamps formateados
- Animaciones sutiles

Uso:
    from stream_chat_ui import ChatPanel
    
    chat = ChatPanel(parent_frame)
    chat.add_message("HypeBot", "¡JAJAJA!", delay=2)
    chat.show_delay_indicator("CritiBot", 3)
"""

import customtkinter as ctk
from datetime import datetime
import threading

# ─── Configuración de Colores ───────────────────────────────────────────────

COLOR_BG_INNER = "#1c1c1e"        # Fondo de cajas
COLOR_BG_CARD = "#252529"         # Fondo de cards
COLOR_TEXT_PRIMARY = "#ffffff"    # Texto principal
COLOR_TEXT_SECONDARY = "#86868b"  # Texto secundario

# Colores de bots (personalizados)
COLOR_HYPE = "#ff453a"    # Rojo (HypeBot)
COLOR_CRITI = "#30d158"   # Verde (CritiBot)
COLOR_LURKER = "#bf5af2"  # Púrpura (LurkerBot)

BOT_COLORS = {
    "HypeBot": COLOR_HYPE,
    "CritiBot": COLOR_CRITI,
    "LurkerBot": COLOR_LURKER
}

BOT_EMOJIS = {
    "HypeBot": "[HYPE]",
    "CritiBot": "[CRITI]",
    "LurkerBot": "[LURK]"
}


class ChatMessageBubble(ctk.CTkFrame):
    """
    Un único mensaje de chat con formato y colores.
    
    Estructura:
    ┌─────────────────────────────────────────┐
    │ 🔥 HypeBot    14:32:55                  │
    │ "¡JAJAJA NOOOO! 🔥 Increíble..."      │
    │ ↳ Enviando en 2s...                     │
    └─────────────────────────────────────────┘
    """
    
    def __init__(self, parent, bot_name: str, text: str, timestamp: str = "", delay: int = 0):
        super().__init__(parent, fg_color=COLOR_BG_CARD, corner_radius=10)
        
        self.bot_name = bot_name
        self.text = text
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        self.delay = delay
        self.grid_columnconfigure(0, weight=1)
        
        # ── HEADER (Bot + Timestamp) ──
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Bot name con emoji y color
        bot_color = BOT_COLORS.get(bot_name, COLOR_TEXT_PRIMARY)
        bot_emoji = BOT_EMOJIS.get(bot_name, "•")
        
        bot_label = ctk.CTkLabel(
            header_frame,
            text=f"{bot_emoji} {bot_name}",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=bot_color
        )
        bot_label.grid(row=0, column=0, sticky="w")
        
        # Timestamp
        time_label = ctk.CTkLabel(
            header_frame,
            text=self.timestamp,
            font=ctk.CTkFont(family="SF Pro Text", size=10),
            text_color=COLOR_TEXT_SECONDARY
        )
        time_label.grid(row=0, column=1, sticky="e", padx=(8, 0))
        
        # ── MENSAJE ──
        msg_label = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=COLOR_TEXT_PRIMARY,
            wraplength=350,
            justify="left"
        )
        msg_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        
        # ── DELAY INDICATOR (si aplica) ──
        if delay > 0:
            self.delay_label = ctk.CTkLabel(
                self,
                text=f"↳ Enviando en {delay}s...",
                font=ctk.CTkFont(family="SF Pro Text", size=10),
                text_color=bot_color
            )
            self.delay_label.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 10))
            self.delay = delay
        else:
            self.delay_label = None
        
        self.pack_propagate(False)


class ChatPanel(ctk.CTkFrame):
    """
    Panel de chat mejorado con scroll y animaciones.
    
    Características:
    - Colores distintos por bot
    - Auto-scroll al último mensaje
    - Display de delays
    - Limpieza automática de mensajes antiguos (max 50)
    """
    
    def __init__(self, parent, height=250):
        super().__init__(parent, fg_color=COLOR_BG_INNER, corner_radius=8)
        
        self.height = height
        self.message_bubbles = []
        self.max_messages = 50
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ── SCROLLABLE FRAME PARA MENSAJES ──
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_BG_INNER,
            corner_radius=8,
            scrollbar_button_color=COLOR_TEXT_SECONDARY,
            scrollbar_button_hover_color=COLOR_TEXT_PRIMARY
        )
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.message_row = 0
        
    def add_message(self, bot_name: str, text: str, delay: int = 0):
        """
        Añade un nuevo mensaje al chat.
        
        Args:
            bot_name: "HypeBot", "CritiBot", o "LurkerBot"
            text: Contenido del mensaje
            delay: Segundos de delay (0 si no aplica)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        bubble = ChatMessageBubble(
            self.scrollable_frame,
            bot_name,
            text,
            timestamp,
            delay
        )
        bubble.grid(row=self.message_row, column=0, sticky="ew", padx=8, pady=4)
        
        self.message_bubbles.append(bubble)
        self.message_row += 1
        
        # Limpiar mensajes antiguos si excedemos el límite
        if len(self.message_bubbles) > self.max_messages:
            old_bubble = self.message_bubbles.pop(0)
            old_bubble.grid_forget()
            old_bubble.destroy()
            self.message_row -= 1
        
        # Auto-scroll al final
        self.scrollable_frame.after(100, self._scroll_to_bottom)
        
        # Animar delay si existe
        if delay > 0:
            threading.Thread(
                target=self._animate_delay,
                args=(bubble, delay),
                daemon=True
            ).start()
    
    def show_delay_indicator(self, bot_name: str, remaining_delay: int):
        """
        Muestra un indicador de delay que va descontando.
        
        Útil para mostrar en tiempo real cuándo se enviará cada bot.
        """
        if self.message_bubbles:
            last_bubble = self.message_bubbles[-1]
            if last_bubble.bot_name == bot_name and last_bubble.delay_label:
                threading.Thread(
                    target=self._animate_delay,
                    args=(last_bubble, remaining_delay),
                    daemon=True
                ).start()
    
    def _animate_delay(self, bubble: ChatMessageBubble, initial_delay: int):
        """
        Anima el contador de delay de forma suave.
        
        Actualiza el label cada 0.5 segundos.
        """
        if not bubble.delay_label:
            return
        
        bot_color = BOT_COLORS.get(bubble.bot_name, COLOR_TEXT_PRIMARY)
        
        for remaining in range(initial_delay, 0, -1):
            try:
                bubble.delay_label.configure(
                    text=f"↳ Enviando en {remaining}s...",
                    text_color=bot_color
                )
            except:
                return  # Widget fue destruido
            
            # Esperar 1 segundo antes de actualizar
            import time
            time.sleep(1)
        
        # Mensaje enviado - cambiar a confirmación
        try:
            bubble.delay_label.configure(
                text="✓ Enviado",
                text_color="#34c759"
            )
            # Desaparecer después de 2 segundos
            import time
            time.sleep(2)
            bubble.delay_label.configure(text="")
        except:
            pass
    
    def _scroll_to_bottom(self):
        """Auto-scroll al último mensaje."""
        try:
            self.scrollable_frame._parent_canvas.yview_moveto(1.0)
        except:
            pass
    
    def add_system_message(self, text: str):
        """
        Añade un mensaje del sistema (no es de un bot).
        
        Útil para eventos como "Chat iniciado", "Error al conectar", etc.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Frame del sistema
        sys_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        sys_frame.grid(row=self.message_row, column=0, sticky="ew", padx=8, pady=6)
        sys_frame.grid_columnconfigure(0, weight=1)
        
        label = ctk.CTkLabel(
            sys_frame,
            text=f"[{timestamp}] ℹ️ {text}",
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=350,
            justify="center"
        )
        label.pack()
        
        self.message_row += 1
        
        if len(self.message_bubbles) > self.max_messages:
            self.message_row -= 1
        
        self._scroll_to_bottom()
    
    def clear_chat(self):
        """Limpia todos los mensajes del chat."""
        for bubble in self.message_bubbles:
            bubble.grid_forget()
            bubble.destroy()
        
        self.message_bubbles.clear()
        self.message_row = 0
        
        self.add_system_message("Chat vaciado")
    
    def get_stats(self) -> dict:
        """Retorna estadísticas del chat."""
        return {
            "total_messages": len(self.message_bubbles),
            "max_messages": self.max_messages,
            "by_bot": {
                "HypeBot": sum(1 for b in self.message_bubbles if b.bot_name == "HypeBot"),
                "CritiBot": sum(1 for b in self.message_bubbles if b.bot_name == "CritiBot"),
                "LurkerBot": sum(1 for b in self.message_bubbles if b.bot_name == "LurkerBot")
            }
        }


if __name__ == "__main__":
    # ── DEMO STANDALONE ──
    
    root = ctk.CTk()
    root.title("StreamMind — Chat UI Demo")
    root.geometry("500x600")
    root.configure(fg_color="#0a0a0b")
    
    # Panel de chat
    chat = ChatPanel(root, height=450)
    chat.pack(fill="both", expand=True, padx=12, pady=12)
    
    # Sistema de prueba
    import random
    from datetime import datetime
    
    messages = {
        "HypeBot": [
            "¡JAJAJA NOOOO! 🔥 ¡ESO FUE INCREÍBLE!",
            "¡VAMOOOS! 🚀 QUÉ CLUTCH",
            "NO ME LO ESPERABA HERMANO",
            "POGGERS 🔥🔥🔥",
        ],
        "CritiBot": [
            "Interesante estrategia... pero ¿hubiera funcionado sin suerte?",
            "Eso fue bien pensado, ngl",
            "¿Consideraste la alternativa?",
            "Buen movimiento, aunque podría haber sido diferente",
        ],
        "LurkerBot": [
            "xd",
            "👀",
            "F",
            "basado",
            "jajaja",
        ]
    }
    
    # Botones de prueba
    def add_random_message():
        bot = random.choice(["HypeBot", "CritiBot", "LurkerBot"])
        msg = random.choice(messages[bot])
        delay = random.randint(0, 3) if bot != "LurkerBot" else 0
        chat.add_message(bot, msg, delay)
    
    def clear_chat():
        chat.clear_chat()
    
    def show_stats():
        stats = chat.get_stats()
        print("\n📊 Chat Stats:", stats)
    
    button_frame = ctk.CTkFrame(root, fg_color="transparent")
    button_frame.pack(fill="x", padx=12, pady=12)
    
    btn_add = ctk.CTkButton(
        button_frame,
        text="Agregar Mensaje Aleatorio",
        command=add_random_message,
        fg_color="#30d158",
        hover_color="#26a841",
        corner_radius=8
    )
    btn_add.pack(side="left", padx=4)
    
    btn_clear = ctk.CTkButton(
        button_frame,
        text="Limpiar",
        command=clear_chat,
        fg_color="#ff453a",
        hover_color="#ff3b30",
        corner_radius=8
    )
    btn_clear.pack(side="left", padx=4)
    
    btn_stats = ctk.CTkButton(
        button_frame,
        text="Stats",
        command=show_stats,
        fg_color="#bf5af2",
        hover_color="#a855f7",
        corner_radius=8
    )
    btn_stats.pack(side="left", padx=4)
    
    root.mainloop()
