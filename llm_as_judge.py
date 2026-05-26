# -*- coding: utf-8 -*-
"""
StreamMind — LLM-as-Judge Evaluation System (Fase 5)
=====================================================

Sistema de evaluación automática de comentarios:
- Rúbrica de calidad (naturalidad, coherencia, jerga, etc)
- Comparación entre comentarios reales vs generados
- Puntuación de humanidad por comentario
- Análisis estadístico de similitud

Uso:
    from llm_as_judge import LLMJudge
    
    judge = LJudge(api_key)
    score = judge.evaluate_comment("¡JAJAJA NOOOO! 🔥", bot_personality="HypeBot")
    comparison = judge.compare_real_vs_generated(real_comments, llm_comments)
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict

# ─── LLM Judge Configuration ─────────────────────────────────────────────────

class LLMJudge:
    """
    Evaluador automático usando LLM con rúbrica de calidad.
    
    Rúbrica:
    - Naturalidad (¿suena como un humano real?): 0-100
    - Coherencia (¿tiene sentido en contexto?): 0-100
    - Longitud (¿es apropiada?): 0-100
    - Jerga/Emotes (¿usa apropiadamente?): 0-100
    - Personalidad (¿mantiene el estilo?): 0-100
    
    Score Final = Promedio ponderado de los 5 criterios
    """
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.model_name = "google/gemma-3n-e2b-it"
        self.temperature = 0.3  # Más determinístico para evaluación
        self.connected = bool(api_key)
        
        self.evaluation_history = []
        self.comparison_results = []
        
    def connect(self, api_key: str) -> bool:
        """Establece API Key."""
        self.api_key = api_key
        self.connected = bool(api_key)
        return self.connected
    
    def evaluate_comment(
        self,
        text: str,
        bot_personality: str = "HypeBot",
        context: str = "",
        is_real_human: bool = None
    ) -> Dict:
        """
        Evalúa un comentario usando rúbrica LLM.
        
        Args:
            text: Comentario a evaluar
            bot_personality: HypeBot, CritiBot, o LurkerBot
            context: Contexto del stream (opcional)
            is_real_human: Si se sabe que es real (para comparación)
        
        Returns:
            Dict con:
            {
                "text": str,
                "bot_personality": str,
                "criteria": {
                    "naturalidad": 0-100,
                    "coherencia": 0-100,
                    "longitud": 0-100,
                    "jerga": 0-100,
                    "personalidad": 0-100
                },
                "humanness_score": 0-100,
                "verdict": "REAL" o "GENERADO" (predicción),
                "confidence": 0-100,
                "reasoning": str,
                "evaluated_at": timestamp
            }
        """
        
        if not self.connected or not self.api_key:
            # Evaluación sin API (heurística local)
            return self._evaluate_local(text, bot_personality, context)
        
        system_prompt = """Eres un juez experto en streaming y contenido de chat en vivo.
Tu tarea es evaluar comentarios de espectadores usando una rúbrica de 5 criterios.

Personalidades esperadas:
- HypeBot: Entusiasta, mayúsculas, emojis, "¡JAJAJA!", "POGGERS", "🔥"
- CritiBot: Analítico, preguntas, "Interesante...", "¿Por qué...?"
- LurkerBot: Cínico, seco, memes, "xd", "F", "👀", "basado"

Debes evaluar cada criterio del 0-100 y proporcionar un veredicto."""
        
        user_prompt = f"""Evalúa este comentario del chat en vivo:

PERSONALIDAD ESPERADA: {bot_personality}
CONTEXTO DEL STREAM: {context if context else "(Sin contexto)"}
COMENTARIO: "{text}"

Criterios a evaluar (0-100 cada uno):
1. **Naturalidad**: ¿Suena como un humano real de Twitch?
2. **Coherencia**: ¿Tiene sentido en el contexto?
3. **Longitud**: ¿Es una longitud típica para esta personalidad?
4. **Jerga/Emotes**: ¿Usa apropiadamente emotes y jerga de Twitch?
5. **Personalidad**: ¿Mantiene coherencia con la personalidad esperada?

Responde EXACTAMENTE en este formato JSON:
{{
    "naturalidad": 0-100,
    "coherencia": 0-100,
    "longitud": 0-100,
    "jerga": 0-100,
    "personalidad": 0-100,
    "veredicto": "REAL" o "GENERADO",
    "confianza": 0-100,
    "razonamiento": "Explicación breve"
}}
"""
        
        try:
            response_data = self._call_nvidia_nim(system_prompt, user_prompt)
            evaluation = self._parse_evaluation(response_data)
            evaluation["text"] = text
            evaluation["bot_personality"] = bot_personality
            evaluation["is_real_human"] = is_real_human
            evaluation["evaluated_at"] = datetime.now().isoformat()
            
            self.evaluation_history.append(evaluation)
            return evaluation
            
        except Exception as e:
            return self._evaluate_local(text, bot_personality, context)
    
    def _evaluate_local(self, text: str, bot_personality: str, context: str) -> Dict:
        """
        Evaluación heurística local (sin API).
        
        Basada en características simples del texto.
        """
        
        criteria = {
            "naturalidad": self._score_naturalidad(text, bot_personality),
            "coherencia": self._score_coherencia(text),
            "longitud": self._score_longitud(text, bot_personality),
            "jerga": self._score_jerga(text, bot_personality),
            "personalidad": self._score_personalidad(text, bot_personality)
        }
        
        humanness = sum(criteria.values()) / len(criteria)
        
        result = {
            "text": text,
            "bot_personality": bot_personality,
            "criteria": criteria,
            "humanness_score": round(humanness, 1),
            "verdict": "REAL" if humanness > 60 else "GENERADO",
            "confidence": min(90, abs(humanness - 50) * 1.8),
            "reasoning": self._generate_reasoning(criteria, text, bot_personality),
            "evaluated_at": datetime.now().isoformat(),
            "method": "local_heuristic"
        }
        
        # Añadir al historial
        self.evaluation_history.append(result)
        return result
    
    def _score_naturalidad(self, text: str, bot: str) -> float:
        """¿Suena como humano real?"""
        score = 50
        
        # Características naturalidad
        if len(text) < 3:  # Muy corto
            score -= 20
        if "ERROR" in text or "Error" in text or "error" in text:
            score -= 30
        if text.count(" ") > 30:  # Muy largo
            score -= 10
        if "generado" in text.lower() or "ia" in text.lower():
            score -= 40
        
        # Emojis y caracteres especiales (natural en Twitch)
        emoji_count = len([c for c in text if ord(c) > 127])
        if emoji_count > 0 and emoji_count < 5:
            score += 15
        
        # Typos/variaciones (más natural)
        if any(c.lower() == 'x' and c == 'x' for c in text):
            score += 5
        
        return max(0, min(100, score))
    
    def _score_coherencia(self, text: str) -> float:
        """¿Tiene sentido?"""
        score = 60
        
        # Sin coherencia
        if len(text) < 2:
            score = 20
        elif len(text) > 100:
            score -= 10  # Puede ser menos coherente si es muy largo
        
        # Palabras comunes de Twitch
        twitch_words = ["jajaja", "lol", "xd", "f", "poggers", "monka", "sadge", "basado"]
        if any(w in text.lower() for w in twitch_words):
            score += 10
        
        # Preguntas (CritiBot típicamente hace preguntas)
        if "?" in text:
            score += 5
        
        return max(0, min(100, score))
    
    def _score_longitud(self, text: str, bot: str) -> float:
        """¿Es una longitud apropiada?"""
        length = len(text)
        
        if bot == "HypeBot":
            # 5-30 caracteres típicamente
            if 5 <= length <= 30:
                return 85
            elif 3 <= length <= 50:
                return 70
            else:
                return 40
        elif bot == "CritiBot":
            # 15-60 caracteres
            if 15 <= length <= 60:
                return 85
            elif 10 <= length <= 80:
                return 70
            else:
                return 40
        else:  # LurkerBot
            # 1-20 caracteres (muy corto)
            if 1 <= length <= 20:
                return 85
            elif 1 <= length <= 40:
                return 70
            else:
                return 40
    
    def _score_jerga(self, text: str, bot: str) -> float:
        """¿Usa apropiadamente emotes y jerga?"""
        score = 50
        
        text_lower = text.lower()
        
        # Jerga Twitch general
        general_slang = ["xd", "lol", "jaja", "f", "basado", "pog", "monka", "sadge"]
        slang_count = sum(1 for s in general_slang if s in text_lower)
        score += slang_count * 8
        
        if bot == "HypeBot":
            hype_words = ["vamooos", "increíble", "jajaja", "🔥", "poggers", "no me lo esperaba"]
            if any(w in text_lower for w in hype_words):
                score += 20
            if text.isupper() and len(text) > 3:  # MAYÚSCULAS
                score += 15
        
        elif bot == "CritiBot":
            criti_words = ["interesante", "¿", "crees", "consideraste", "estrategia", "análisis"]
            if any(w in text_lower for w in criti_words):
                score += 20
            if "?" in text:
                score += 10
        
        else:  # LurkerBot
            lurker_words = ["xd", "👀", "f", "jaja", "basado", "hermano"]
            if any(w in text_lower for w in lurker_words):
                score += 20
        
        return max(0, min(100, score))
    
    def _score_personalidad(self, text: str, bot: str) -> float:
        """¿Mantiene consistencia con personalidad?"""
        score = 50
        
        if bot == "HypeBot":
            # Debe tener energía
            if any(c.isupper() for c in text) and text.count("!") > 0:
                score += 25
            if any(emoji in text for emoji in ["🔥", "🚀", "💯", "😂"]):
                score += 10
        
        elif bot == "CritiBot":
            # Debe parecer reflexivo
            if "?" in text or any(w in text.lower() for w in ["pero", "aunque", "sin embargo"]):
                score += 25
            if len(text) > 15:  # Más elaborado
                score += 10
        
        else:  # LurkerBot
            # Debe ser corto e irónico
            if len(text) < 15:
                score += 20
            if any(w in text.lower() for w in ["xd", "👀", "f"]):
                score += 15
        
        return max(0, min(100, score))
    
    def _generate_reasoning(self, criteria: Dict, text: str, bot: str) -> str:
        """Genera explicación de la evaluación."""
        avg = sum(criteria.values()) / len(criteria)
        
        reasons = []
        for criterion, score in criteria.items():
            if score < 40:
                reasons.append(f"⚠️ {criterion} baja ({score})")
            elif score > 80:
                reasons.append(f"✓ {criterion} excelente ({score})")
        
        if not reasons:
            reasons.append(f"Comentario aceptable ({avg:.0f}/100)")
        
        return " | ".join(reasons[:2])
    
    def _call_nvidia_nim(self, system_prompt: str, user_prompt: str) -> Dict:
        """Llamada a NVIDIA NIM API."""
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
            "max_tokens": 512
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=20) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    
    def _parse_evaluation(self, response_data: Dict) -> Dict:
        """Parsea respuesta del LLM."""
        try:
            content = response_data["choices"][0]["message"]["content"]
            
            # Limpiar markdown
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            parsed = json.loads(content)
            
            return {
                "criteria": {
                    "naturalidad": parsed.get("naturalidad", 50),
                    "coherencia": parsed.get("coherencia", 50),
                    "longitud": parsed.get("longitud", 50),
                    "jerga": parsed.get("jerga", 50),
                    "personalidad": parsed.get("personalidad", 50)
                },
                "humanness_score": round(
                    sum([
                        parsed.get("naturalidad", 50),
                        parsed.get("coherencia", 50),
                        parsed.get("longitud", 50),
                        parsed.get("jerga", 50),
                        parsed.get("personalidad", 50)
                    ]) / 5, 1
                ),
                "verdict": parsed.get("veredicto", "GENERADO"),
                "confidence": parsed.get("confianza", 50),
                "reasoning": parsed.get("razonamiento", "")
            }
        except:
            return self._fallback_evaluation()
    
    def _fallback_evaluation(self) -> Dict:
        """Evaluación de fallback si falla parseo."""
        return {
            "criteria": {
                "naturalidad": 60,
                "coherencia": 60,
                "longitud": 60,
                "jerga": 60,
                "personalidad": 60
            },
            "humanness_score": 60,
            "verdict": "INDETERMINADO",
            "confidence": 30,
            "reasoning": "Evaluación fallida - usando valores por defecto"
        }
    
    def compare_real_vs_generated(
        self,
        real_comments: List[str],
        generated_comments: List[str],
        bot_personality: str = "HypeBot"
    ) -> Dict:
        """
        Compara comentarios reales vs generados.
        
        Returns:
            {
                "real_avg_score": 0-100,
                "generated_avg_score": 0-100,
                "similarity_ratio": 0-100,
                "misclassification_rate": 0-100 (% humanos engañados),
                "verdict": "INDISTINGUIBLES" o "DISTINGUIBLES",
                "analysis": str
            }
        """
        
        real_evaluations = [
            self.evaluate_comment(c, bot_personality, is_real_human=True)
            for c in real_comments
        ]
        
        generated_evaluations = [
            self.evaluate_comment(c, bot_personality, is_real_human=False)
            for c in generated_comments
        ]
        
        real_avg = sum(e["humanness_score"] for e in real_evaluations) / len(real_evaluations)
        generated_avg = sum(e["humanness_score"] for e in generated_evaluations) / len(generated_evaluations)
        
        # Tasa de error: cuántos generados se confunden con reales
        misclassification_count = sum(
            1 for e in generated_evaluations if e["verdict"] == "REAL"
        )
        misclassification_rate = (misclassification_count / len(generated_evaluations)) * 100
        
        result = {
            "real_avg_score": round(real_avg, 1),
            "generated_avg_score": round(generated_avg, 1),
            "misclassification_rate": round(misclassification_rate, 1),
            "total_real": len(real_comments),
            "total_generated": len(generated_comments),
            "verdict": "INDISTINGUIBLES" if misclassification_rate > 30 else "DISTINGUIBLES",
            "analysis": f"Humanos engañados en {misclassification_rate:.1f}% de casos. " +
                       ("✓ Éxito" if misclassification_rate > 30 else "✗ Necesita mejora")
        }
        
        self.comparison_results.append(result)
        return result
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas de evaluaciones."""
        if not self.evaluation_history:
            return {
                "total_evaluations": 0,
                "avg_humanness": 0,
                "min_humanness": 0,
                "max_humanness": 0,
                "real_count": 0,
                "generated_count": 0,
                "indeterminate_count": 0,
                "comparisons": 0
            }
        
        scores = [e["humanness_score"] for e in self.evaluation_history]
        verdicts = [e["verdict"] for e in self.evaluation_history]
        
        return {
            "total_evaluations": len(self.evaluation_history),
            "avg_humanness": round(sum(scores) / len(scores), 1),
            "min_humanness": min(scores),
            "max_humanness": max(scores),
            "real_count": sum(1 for v in verdicts if v == "REAL"),
            "generated_count": sum(1 for v in verdicts if v == "GENERADO"),
            "indeterminate_count": sum(1 for v in verdicts if v == "INDETERMINADO"),
            "comparisons": len(self.comparison_results)
        }


if __name__ == "__main__":
    print("=" * 80)
    print("StreamMind — LLM-as-Judge Evaluation System (DEMO)")
    print("=" * 80 + "\n")
    
    judge = LLMJudge()
    
    # Comentarios de prueba
    test_comments = {
        "HypeBot_real": [
            "¡JAJAJA NOOOO! 🔥",
            "POGGERS 🔥🔥🔥",
            "¡VAMOOOS!",
        ],
        "HypeBot_generated": [
            "¡JAJAJA! ¡ESO FUE INCREÍBLE!",
            "POGGERS el clutch",
            "¡QUÉ COSA MÁS HIPEANTE!",
        ],
        "CritiBot_real": [
            "Interesante estrategia pero se pudo hacer diferente",
            "¿Por qué no usó esa táctica?",
            "Buen movimiento ngl",
        ],
        "CritiBot_generated": [
            "Eso fue un movimiento interesante pero cuestionable",
            "¿Consideraste la alternativa?",
            "Buena decisión, aunque podría haber sido diferente",
        ],
        "LurkerBot_real": [
            "xd",
            "F",
            "👀 basado",
        ],
        "LurkerBot_generated": [
            "jajaja hermano xd",
            "Eso fue epico",
            "👀👀👀",
        ]
    }
    
    print("📊 Evaluando comentarios con heurística local...\n")
    
    for personality in ["HypeBot", "CritiBot", "LurkerBot"]:
        print(f"\n{'='*60}")
        print(f"Personalidad: {personality}")
        print('='*60)
        
        real_evals = [
            judge.evaluate_comment(c, personality, is_real_human=True)
            for c in test_comments.get(f"{personality}_real", [])
        ]
        
        gen_evals = [
            judge.evaluate_comment(c, personality, is_real_human=False)
            for c in test_comments.get(f"{personality}_generated", [])
        ]
        
        print(f"\n✓ Comentarios REALES:")
        for e in real_evals:
            print(f"  '{e['text'][:40]}' → {e['humanness_score']}/100")
        
        print(f"\n🤖 Comentarios GENERADOS:")
        for e in gen_evals:
            print(f"  '{e['text'][:40]}' → {e['humanness_score']}/100")
        
        # Comparación
        real_avg = sum(e["humanness_score"] for e in real_evals) / len(real_evals)
        gen_avg = sum(e["humanness_score"] for e in gen_evals) / len(gen_evals)
        
        print(f"\n📈 Resumen:")
        print(f"  Promedio Real: {real_avg:.1f}/100")
        print(f"  Promedio Generado: {gen_avg:.1f}/100")
        print(f"  Diferencia: {abs(real_avg - gen_avg):.1f} puntos")
    
    stats = judge.get_stats()
    print("\n" + "=" * 80)
    print("📊 ESTADÍSTICAS FINALES:")
    print(f"   Total de evaluaciones: {stats['total_evaluations']}")
    print(f"   Humanidad promedio: {stats['avg_humanness']}/100")
    print(f"   Rango: {stats['min_humanness']}-{stats['max_humanness']}")
    print("=" * 80 + "\n")
