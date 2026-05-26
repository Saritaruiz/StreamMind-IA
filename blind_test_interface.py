# -*- coding: utf-8 -*-
"""
StreamMind — Blind Test Interface (Fase 5)
==========================================

Interfaz GUI para que humanos clasifiquen comentarios sin saber si son reales o generados.

Objetivo: >30% tasa de error (humanos engañados)

Uso:
    python blind_test_interface.py
    
Esto abre una ventana GUI con:
- 100 comentarios (50 reales + 50 generados, aleatorios)
- Pregunta: "¿Es un comentario real de un humano en Twitch?"
- Opciones: SÍ / NO
- Progreso visual
- Resultados finales
"""

import customtkinter as ctk
import random
from typing import List, Tuple, Dict
from datetime import datetime
import json
from pathlib import Path

# ─── Configuración de Tema ───────────────────────────────────────────────────

COLOR_BG_WINDOW = "#0a0a0b"
COLOR_BG_SIDEBAR = "#1c1c1e"
COLOR_BG_CARD = "#252529"
COLOR_BG_INNER = "#1c1c1e"
COLOR_TEXT_PRIMARY = "#ffffff"
COLOR_TEXT_SECONDARY = "#86868b"
COLOR_ACCENT_GREEN = "#30d158"  # Correcto
COLOR_ACCENT_RED = "#ff453a"    # Incorrecto
COLOR_BORDER = "#3a3a3c"

# Comentarios de ejemplo (en producción viendrian de datasets reales)
REAL_COMMENTS = [
    "¡JAJAJA NOOOO! 🔥",
    "POGGERS",
    "¡VAMOOOS!",
    "xd",
    "👀",
    "F",
    "Interesante movimiento",
    "¿Por qué hizo eso?",
    "Basado",
    "NO ME LO ESPERABA",
    "Jajajaja hermano",
    "Buen play ngl",
    "Monka",
    "Sadge",
    "El chat está hipeado",
    "¿Vieron eso?",
    "Jajaja qué locura",
    "Increíble",
    "Clutch",
    "Mejor que en la liga pro",
    "xd ese tipo",
    "Momento viral",
    "👏 👏 👏",
    "Digno de highlight",
    "Eso fue limpio",
]

GENERATED_COMMENTS = [
    "¡JAJAJA NOOOO! ¡ESO FUE INCREÍBLE! 🔥",
    "POGGERS el clutch monumental",
    "¡VAMOOOS! 🚀 QUÉ JUGADA",
    "jajaja hermano xd",
    "👀👀 ese momento",
    "F por la defensa",
    "Eso fue una estrategia interesante pero arriesgada",
    "¿Consideraste hacer lo contrario en esa situación?",
    "Muy basado ese análisis",
    "NO ME LO ESPERABA HERMANO JAJAJA",
    "Jajajaja qué tipo tan rápido",
    "Buen movimiento aunque podría haber sido diferente",
    "Monka ese juego",
    "Sadge moment hermano",
    "El chat debe estar hipeado en este instante",
    "¿Será que vieron esa jugada increíble?",
    "Jajaja qué cosa más loca",
    "¡Eso sí fue increíble!",
    "Ese fue un clutch real",
    "Mejor que muchos de la liga profesional",
    "xd ese tipo está chileno",
    "Momentazo digno de ir viral",
    "👏 👏 👏 excelente",
    "Una jugada digna de ser un highlight",
    "Eso fue muy limpio y eficiente",
]


class BlindTestInterface(ctk.CTk):
    """
    Interfaz GUI para test ciego de humanos vs bots.
    
    Estructura:
    1. Mostrar comentario aleatorio (sin indicar origen)
    2. Pregunta: "¿Es real?"
    3. Usuario elige SÍ/NO
    4. Pasar al siguiente
    5. Al final: mostrar resultados
    """
    
    def __init__(self):
        super().__init__()
        
        self.title("StreamMind — Blind Test: ¿Real o Generado?")
        self.geometry("700x600")
        self.configure(fg_color=COLOR_BG_WINDOW)
        
        # Preparar conjunto de prueba
        self.test_set = self._prepare_test_set()
        self.current_index = 0
        self.responses = []
        
        # Variables de estado
        self.test_started = False
        self.test_completed = False
        
        # Crear interfaz
        self._create_widgets()
    
    def _prepare_test_set(self) -> List[Tuple[str, bool]]:
        """
        Prepara 100 comentarios: 50 reales + 50 generados, aleatorios.
        
        Returns:
            List[(comment_text, is_real)]
        """
        # 50 reales
        test_set = [(c, True) for c in random.sample(REAL_COMMENTS * 2, 50)]
        
        # 50 generados
        test_set += [(c, False) for c in random.sample(GENERATED_COMMENTS * 2, 50)]
        
        # Mezclar orden
        random.shuffle(test_set)
        
        return test_set
    
    def _create_widgets(self):
        """Crea los widgets de la interfaz."""
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ── CONTENEDOR PRINCIPAL ──
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        # ── TÍTULO ──
        title_label = ctk.CTkLabel(
            main_frame,
            text="StreamMind — Blind Test",
            font=ctk.CTkFont(family="SF Pro Display", size=28, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="¿Puedes diferenciar comentarios reales de los generados por IA?",
            font=ctk.CTkFont(family="SF Pro Text", size=13),
            text_color=COLOR_TEXT_SECONDARY
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(0, 24))
        
        # ── BARRA DE PROGRESO ──
        self.progress_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.progress_frame.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        self.progress_frame.grid_columnconfigure(1, weight=1)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Presiona 'Comenzar' para iniciar",
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.progress_label.grid(row=0, column=0, sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            fg_color=COLOR_BG_CARD,
            progress_color=COLOR_ACCENT_GREEN,
            height=6
        )
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self.progress_bar.set(0)
        
        # ── CARD DEL COMENTARIO ──
        self.comment_card = ctk.CTkFrame(
            main_frame,
            fg_color=COLOR_BG_CARD,
            border_width=2,
            border_color=COLOR_BORDER,
            corner_radius=12
        )
        self.comment_card.grid(row=3, column=0, sticky="nsew", pady=24)
        self.comment_card.grid_columnconfigure(0, weight=1)
        
        # Pregunta
        question_label = ctk.CTkLabel(
            self.comment_card,
            text="¿Es este comentario de un humano real o generado por IA?",
            font=ctk.CTkFont(family="SF Pro Text", size=13),
            text_color=COLOR_TEXT_SECONDARY
        )
        question_label.pack(padx=20, pady=(16, 8))
        
        # El comentario
        self.comment_label = ctk.CTkLabel(
            self.comment_card,
            text="...",
            font=ctk.CTkFont(family="SF Pro Text", size=16, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
            wraplength=500,
            justify="center"
        )
        self.comment_label.pack(padx=20, pady=24, fill="both", expand=True)
        
        # ── BOTONES DE RESPUESTA ──
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=4, column=0, sticky="ew", pady=(0, 20))
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)
        
        self.btn_real = ctk.CTkButton(
            buttons_frame,
            text="[YES] Es Real",
            command=lambda: self._respond(True),
            fg_color=COLOR_ACCENT_GREEN,
            hover_color="#26a841",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            state="disabled"
        )
        self.btn_real.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        
        self.btn_generated = ctk.CTkButton(
            buttons_frame,
            text="[NO] Es Generado",
            command=lambda: self._respond(False),
            fg_color=COLOR_ACCENT_RED,
            hover_color="#ff3b30",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            state="disabled"
        )
        self.btn_generated.grid(row=0, column=2, padx=(6, 0), sticky="ew")
        
        self.btn_skip = ctk.CTkButton(
            buttons_frame,
            text="Omitir",
            command=self._skip,
            fg_color=COLOR_BG_CARD,
            hover_color=COLOR_BORDER,
            font=ctk.CTkFont(size=11),
            corner_radius=8,
            state="disabled"
        )
        self.btn_skip.grid(row=0, column=1, padx=6, sticky="ew")
        
        # ── BOTONES DE CONTROL ──
        control_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        control_frame.grid(row=5, column=0, sticky="ew")
        control_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_start = ctk.CTkButton(
            control_frame,
            text="Comenzar Test",
            command=self._start_test,
            fg_color=COLOR_ACCENT_GREEN,
            hover_color="#26a841",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8
        )
        self.btn_start.grid(row=0, column=0, padx=(0, 8))
        
        self.btn_reset = ctk.CTkButton(
            control_frame,
            text="Reiniciar",
            command=self._reset,
            fg_color=COLOR_BG_CARD,
            hover_color=COLOR_BORDER,
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            state="disabled"
        )
        self.btn_reset.grid(row=0, column=2, padx=(8, 0))
    
    def _start_test(self):
        """Inicia el test ciego."""
        self.test_started = True
        self.btn_start.configure(state="disabled")
        self.btn_real.configure(state="normal")
        self.btn_generated.configure(state="normal")
        self.btn_skip.configure(state="normal")
        self.btn_reset.configure(state="normal")
        
        self.current_index = 0
        self.responses = []
        self._show_next_comment()
    
    def _show_next_comment(self):
        """Muestra el siguiente comentario."""
        if self.current_index >= len(self.test_set):
            self._finish_test()
            return
        
        comment, _ = self.test_set[self.current_index]
        self.comment_label.configure(text=f'"{comment}"')
        
        # Actualizar progreso
        progress = self.current_index / len(self.test_set)
        self.progress_bar.set(progress)
        self.progress_label.configure(
            text=f"Pregunta {self.current_index + 1}/{len(self.test_set)}"
        )
    
    def _respond(self, user_says_real: bool):
        """Registra la respuesta del usuario."""
        if self.current_index >= len(self.test_set):
            return
        
        _, is_real = self.test_set[self.current_index]
        correct = (user_says_real == is_real)
        
        self.responses.append({
            "index": self.current_index,
            "user_answer": user_says_real,
            "correct_answer": is_real,
            "correct": correct,
            "comment": self.test_set[self.current_index][0]
        })
        
        self.current_index += 1
        self._show_next_comment()
    
    def _skip(self):
        """Omite la pregunta actual."""
        self.current_index += 1
        self._show_next_comment()
    
    def _finish_test(self):
        """Termina el test y muestra resultados."""
        self.test_completed = True
        self.btn_real.configure(state="disabled")
        self.btn_generated.configure(state="disabled")
        self.btn_skip.configure(state="disabled")
        
        # Calcular resultados
        results = self._calculate_results()
        self._show_results(results)
        
        # Guardar a disco
        self._save_results(results)
    
    def _calculate_results(self) -> Dict:
        """Calcula estadísticas del test."""
        total_answered = len(self.responses)
        total_correct = sum(1 for r in self.responses if r["correct"])
        total_incorrect = total_answered - total_correct
        
        # Tasa de error = qué porcentaje de las generadas fueron clasificadas como reales
        # (Esto es lo que queremos: humanos engañados)
        generated_responses = [
            r for r in self.responses if not r["correct_answer"]
        ]
        misclassified = sum(
            1 for r in generated_responses if r["user_answer"] == True
        )
        misclassification_rate = (misclassified / len(generated_responses) * 100) if generated_responses else 0
        
        accuracy = (total_correct / total_answered * 100) if total_answered > 0 else 0
        
        return {
            "total_answered": total_answered,
            "total_correct": total_correct,
            "total_incorrect": total_incorrect,
            "accuracy": accuracy,
            "misclassification_rate": misclassification_rate,
            "success": misclassification_rate > 30,  # Objetivo: >30%
            "timestamp": datetime.now().isoformat(),
            "detailed_responses": self.responses
        }
    
    def _show_results(self, results: Dict):
        """Muestra una ventana con los resultados."""
        result_window = ctk.CTkToplevel(self)
        result_window.title("Resultados del Test")
        result_window.geometry("600x500")
        result_window.configure(fg_color=COLOR_BG_WINDOW)
        
        result_window.grid_columnconfigure(0, weight=1)
        result_window.grid_rowconfigure(1, weight=1)
        
        # ── TÍTULO ──
        title = ctk.CTkLabel(
            result_window,
            text="📊 Resultados del Test",
            font=ctk.CTkFont(family="SF Pro Display", size=20, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        title.pack(padx=20, pady=(20, 12))
        
        # ── CONTENIDO ──
        content_frame = ctk.CTkScrollableFrame(
            result_window,
            fg_color=COLOR_BG_CARD,
            corner_radius=8
        )
        content_frame.pack(fill="both", expand=True, padx=20, pady=12)
        
        # Resultados principales
        accuracy = results["accuracy"]
        misclass_rate = results["misclassification_rate"]
        success = results["success"]
        
        verdict_color = COLOR_ACCENT_GREEN if success else COLOR_ACCENT_RED
        verdict_text = "[OK] EXITO - Humanos engañados!" if success else "[!] Necesita mejora"
        
        # Estadísticas
        stats_text = f"""
{verdict_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ESTADISTICAS GENERALES:

Preguntas respondidas: {results['total_answered']}/100
Respuestas correctas: {results['total_correct']}
Respuestas incorrectas: {results['total_incorrect']}
Precisión general: {accuracy:.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

METRICA CLAVE (Tasa de Error):

Humanos que confundieron IA con real: {misclass_rate:.1f}%

Meta: >30% {'[OK] ALCANZADA' if success else '[!] No alcanzada'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Interpretación:
- >50%: IA casi perfecta, humanos muy engañados
- 30-50%: IA muy buena, cumple objetivo
- 10-30%: IA promedio, necesita mejora
- <10%: IA distinguible, problemas claros

Los comentarios generados son {'INDISTINGUIBLES' if success else 'DISTINGUIBLES'} de los reales.
        """
        
        stats_label = ctk.CTkLabel(
            content_frame,
            text=stats_text,
            font=ctk.CTkFont(family="Monospace", size=11),
            text_color=COLOR_TEXT_PRIMARY,
            justify="left",
            wraplength=500
        )
        stats_label.pack(padx=16, pady=16, anchor="w")
        
        # ── BOTONES ──
        btn_frame = ctk.CTkFrame(result_window, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        btn_frame.grid_columnconfigure(0, weight=1)
        
        close_btn = ctk.CTkButton(
            btn_frame,
            text="Cerrar",
            command=result_window.destroy,
            fg_color=COLOR_BORDER,
            hover_color=COLOR_BG_CARD,
            corner_radius=8
        )
        close_btn.grid(row=0, column=0, sticky="ew")
    
    def _reset(self):
        """Reinicia el test."""
        self.test_set = self._prepare_test_set()
        self.current_index = 0
        self.responses = []
        self.test_started = False
        self.test_completed = False
        
        self.btn_start.configure(state="normal")
        self.btn_real.configure(state="disabled")
        self.btn_generated.configure(state="disabled")
        self.btn_skip.configure(state="disabled")
        self.btn_reset.configure(state="disabled")
        
        self.comment_label.configure(text="...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Presiona 'Comenzar' para iniciar")
    
    def _save_results(self, results: Dict):
        """Guarda los resultados a un archivo JSON."""
        try:
            filename = f"blind_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = Path(filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"[OK] Resultados guardados en: {filepath}")
        except Exception as e:
            print(f"[WARNING] Error guardando resultados: {e}")


if __name__ == "__main__":
    app = BlindTestInterface()
    app.mainloop()
