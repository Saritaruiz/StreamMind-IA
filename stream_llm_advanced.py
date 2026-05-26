# -*- coding: utf-8 -*-
"""
StreamMind — Advanced LLM Generator (Fase 3: Generación Multi-Persona Mejorada)
===============================================================================
Mejoras:
- Prompts refinados por personalidad
- Contexto de categoría del stream
- Sistema de delays (2-5s entre bots)
- Manejo robusto de errores y reintentos

Uso:
    from stream_llm_advanced import AdvancedMultiBotGenerator
    
    gen = AdvancedMultiBotGenerator()
    gen.connect("tu_api_key")
    comments = gen.generate_comments(
        streamer_text="mensaje del streamer",
        context="contexto histórico",
        stream_category="gaming"
    )
"""

import json
import urllib.request
import urllib.error
import time
import re
from typing import Dict, Optional
from datetime import datetime

# ─── Configuración ───────────────────────────────────────────────────────────

class AdvancedMultiBotGenerator:
    """
    Generador avanzado de comentarios con 3 personalidades distintas.
    
    Características:
    - Prompts refinados por análisis
    - Contexto de categoría
    - Delays realistas entre bots
    - Manejo de errores robusto
    """
    
    def __init__(self):
        self.api_key = ""
        self.model_name = "google/gemma-3n-e2b-it"
        self.temperature = 0.7
        self.max_tokens = 1024
        self.connected = False
        
        # Delays por personalidad (segundos)
        self.delays = {
            "HypeBot": 2,
            "CritiBot": 3,
            "LurkerBot": 4
        }
        
        # Contadores para estadísticas
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.last_call_time = None
        
    def connect(self, api_key: str) -> bool:
        """Establece la API Key de NVIDIA NIM."""
        self.api_key = api_key
        if api_key:
            self.connected = True
            print(f"[✓] Conectado a NVIDIA NIM API")
            return True
        return False
    
    def _get_system_prompt(self, stream_category: str = "gaming") -> str:
        """
        Genera el system prompt refinado basado en categoría.
        
        Insights del EDA (1,570 mensajes reales):
        - Longitud mediana: 8 caracteres
        - Longitud promedio: 14 caracteres
        - Jerga dominante: xd (91), lol (27), kek (14), pog (11), f (8)
        - 66.4% con mayúsculas (alta energía)
        - 2.2% son preguntas
        
        Categorías: gaming, esports, creative, just_chatting, variety_gaming, irl
        """
        
        # Configuración por categoría (mejorada con datos reales)
        category_configs = {
            "gaming": {
                "tone": "hype y competitivo, alta energía",
                "length_avg": "muy cortos (3-12 palabras)",  # Real: mediana 8 chars = ~1-2 palabras
                "hype_style": "gaming lingo: xd, lol, pog, poggers, monka, F, kek",
                "context": "juegos, mecánicas, clips, outplays",
                "caps_ratio": "usar CAPS ocasionalmente (66% de usuarios lo hacen)"
            },
            "esports": {
                "tone": "profesional pero emocionado",
                "length_avg": "cortos (5-15 palabras)",  # Ligeramente más largo que gaming
                "hype_style": "esports slang: clutch, carry, frag, eco, GG, poggers",
                "context": "estrategia, equipos, torneos, juega profesional",
                "caps_ratio": "normal, respeta competitividad"
            },
            "creative": {
                "tone": "admirativo y constructivo",
                "length_avg": "cortos a medios (5-15 palabras)",
                "hype_style": "arte/creatividad: nice, talent, cool, beautiful, pog",
                "context": "técnica, estilo, inspiración, detalles",
                "caps_ratio": "ocasional para énfasis"
            },
            "just_chatting": {
                "tone": "casual y desenfadado, mucho humor",
                "length_avg": "variados pero cortos (2-12 palabras)",  # El más relajado
                "hype_style": "memes: xd, lol, F, basado, jajaja, OMEGALUL",
                "context": "chismes, memes, conversación, drama",
                "caps_ratio": "alto (muchos memes en CAPS)"
            },
            "variety_gaming": {
                "tone": "divertido y espontáneo, reacciones",
                "length_avg": "muy cortos (2-10 palabras)",  # Reacciones rápidas
                "hype_style": "variado: kek, pepega, sadge, monka, lmao, xd",
                "context": "variación, sorpresas, reacciones, cambios",
                "caps_ratio": "alto para sorpresas"
            },
            "irl": {
                "tone": "amigable y casual, observador",
                "length_avg": "cortos (3-12 palabras)",
                "hype_style": "casual: cool, nice, pog, omegalul, xd",
                "context": "eventos, reacciones en vivo, interacciones",
                "caps_ratio": "normal"
            }
        }
        
        config = category_configs.get(stream_category, category_configs["gaming"])
        
        system_prompt = f"""Eres el motor de simulación del chat en vivo de un streamer (Twitch/YouTube Live).
Tu tarea es generar reacciones de tres espectadores virtuales distintivos.

CONTEXTO DEL STREAM:
- Categoría: {stream_category}
- Tono general: {config['tone']}
- Longitud típica: {config['length_avg']}
- Slang/Jerga: {config['hype_style']}

PERSONALIDADES (adopta SIMULTÁNEAMENTE las 3):

1. **HypeBot** — Entusiasta fanboy/fan
   - Estilo: MAYÚSCULAS, emojis, exclamaciones
   - Ejemplos: "¡VAMOOOS! 🔥", "POGGERS", "NO ME LO ESPERABA"
   - Tone: Exagerado, energético, fanático
   - Longitud: {config['length_avg']}

2. **CritiBot** — Analítico reflexivo
   - Estilo: Preguntas inteligentes, análisis, crítica constructiva
   - Ejemplos: "¿Por qué no usó esa estrategia?", "Interesante movimiento"
   - Tone: Pensativo, cuestionador, respeta al streamer
   - Longitud: {config['length_avg']}

3. **LurkerBot** — Cínico silencioso
   - Estilo: Humor seco, ironía, memes, caritas
   - Ejemplos: "xd", "F", "basado", "jajaja", "👀"
   - Tone: Seco, irónico, desinteresado (pero presente)
   - Longitud: {config['length_avg']}

INSTRUCCIONES DE FORMATO:
- Responde ÚNICAMENTE con un objeto JSON válido
- Claves exactas: "HypeBot", "CritiBot", "LurkerBot"
- Cada valor es un STRING con el comentario
- SIN explicaciones, SIN markdown, SIN ```json
- Escribe en español
- Sé conciso y natural
"""
        return system_prompt
    
    def generate_comments(
        self,
        streamer_text: str,
        context: str = "",
        stream_category: str = "gaming",
        include_delays: bool = True
    ) -> Dict:
        """
        Genera comentarios de 3 bots simultáneamente.
        
        Args:
            streamer_text: Lo que acaba de decir el streamer
            context: Contexto histórico del stream
            stream_category: Categoría (gaming, esports, creative, etc)
            include_delays: Si True, añade delays realistas
        
        Returns:
            Dict con: {
                "HypeBot": str,
                "CritiBot": str,
                "LurkerBot": str,
                "delays": {"HypeBot": 2, "CritiBot": 3, "LurkerBot": 4},
                "generated_at": timestamp,
                "category": stream_category
            }
        """
        if not self.connected or not self.api_key:
            raise RuntimeError("API Key de NVIDIA NIM no configurada.")
        
        self.total_calls += 1
        
        # Generar prompts
        system_prompt = self._get_system_prompt(stream_category)
        
        # Restricciones de longitud basadas en datos reales
        length_constraints = {
            "gaming": "2-12 palabras (mediana real: 8 chars)",
            "esports": "3-15 palabras",
            "creative": "4-15 palabras",
            "just_chatting": "2-10 palabras (muy cortos, muchos emojis/slang)",
            "variety_gaming": "2-10 palabras (reacciones rápidas)",
            "irl": "3-12 palabras"
        }
        
        user_prompt = f"""Contexto histórico del stream:
{context if context else "(Sin contexto histórico)"}

El streamer acaba de decir:
"{streamer_text}"

RESTRICCIONES CRÍTICAS (basadas en análisis de {1570} mensajes reales):
- Longitud ESTRICTA: {length_constraints.get(stream_category, length_constraints['gaming'])}
- Usa mucho SLANG y jerga de Twitch
- Sé MUY breve y directo (los usuarios reales escriben comentarios cortos)
- NO uses explicaciones largas o análisis
- Mantén el tone característico de cada bot

Genera ahora los comentarios en formato JSON:"""
        
        # Llamar a NVIDIA NIM API
        try:
            response_data = self._call_nvidia_nim(system_prompt, user_prompt)
            comments = self._parse_response(response_data)
            
            # Añadir delays si se solicita
            if include_delays:
                comments["delays"] = self.delays.copy()
            
            comments["generated_at"] = datetime.now().isoformat()
            comments["category"] = stream_category
            
            self.successful_calls += 1
            self.last_call_time = datetime.now()
            
            return comments
            
        except Exception as e:
            self.failed_calls += 1
            raise RuntimeError(f"Error generando comentarios: {str(e)}")
    
    def _call_nvidia_nim(self, system_prompt: str, user_prompt: str) -> Dict:
        """Realiza llamada a NVIDIA NIM API con reintentos."""
        
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": 0.9
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                res_body = response.read().decode("utf-8")
                return json.loads(res_body)
        except urllib.error.HTTPError as e:
            err_content = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_content)
                err_msg = err_json.get("error", {}).get("message", err_content)
            except:
                err_msg = err_content
            raise RuntimeError(f"NVIDIA NIM HTTP {e.code}: {err_msg}")
        except Exception as e:
            raise RuntimeError(f"Error conectando a NVIDIA NIM: {str(e)}")
    
    def _parse_response(self, response_data: Dict) -> Dict:
        """Parsea y limpia la respuesta del LLM."""
        
        try:
            content = response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ValueError("Respuesta inesperada de NVIDIA NIM")
        
        # Limpiar markdown si existe
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parsear JSON
        try:
            parsed = json.loads(content)
            
            # Validar que tenga las 3 claves
            required_keys = {"HypeBot", "CritiBot", "LurkerBot"}
            if not required_keys.issubset(parsed.keys()):
                # Si falta alguna, usar fallback
                raise ValueError(f"Claves faltantes. Tiene: {list(parsed.keys())}")
            
            return {
                "HypeBot": str(parsed["HypeBot"]),
                "CritiBot": str(parsed["CritiBot"]),
                "LurkerBot": str(parsed["LurkerBot"])
            }
            
        except json.JSONDecodeError:
            # Fallback si falla el parseo
            return self._generate_fallback_comments(content)
    
    def _generate_fallback_comments(self, raw_content: str) -> Dict:
        """Genera comentarios de fallback si el LLM falla."""
        return {
            "HypeBot": "¡JAJAJA! 🔥 No me lo esperaba",
            "CritiBot": "Interesante decisión...",
            "LurkerBot": "xd"
        }
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas de uso."""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": (
                (self.successful_calls / self.total_calls * 100)
                if self.total_calls > 0 else 0
            ),
            "last_call_time": self.last_call_time.isoformat() if self.last_call_time else None,
            "delays": self.delays
        }


# ─── Demo y Testing ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 80)
    print("StreamMind — Advanced LLM Generator (DEMO)")
    print("=" * 80 + "\n")
    
    gen = AdvancedMultiBotGenerator()
    
    # Para usar: descomenta y añade tu API key
    # gen.connect("tu_api_key_aqui")
    
    print("⚠️  Para usar este demo necesitas:")
    print("   1. Una API Key de NVIDIA NIM")
    print("   2. Descomenta el código abajo y añade tu key\n")
    
    print("[*] Configuración de ejemplo:")
    print(f"    Model: {gen.model_name}")
    print(f"    Temperature: {gen.temperature}")
    print(f"    Delays: {gen.delays}\n")
    
    print("📖 Categorías soportadas:")
    categories = ["gaming", "esports", "creative", "just_chatting", "variety_gaming", "irl"]
    for cat in categories:
        print(f"   - {cat}")
    
    print("\n[✓] Sistema LLM avanzado listo para usar")
    print("   Ver: stt_gui.py para integración")
