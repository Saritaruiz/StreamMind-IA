# -*- coding: utf-8 -*-
"""
Demo: Advanced LLM Generator con Delays y Categorías
======================================================

Demuestra:
1. Generación de comentarios con 3 personalidades
2. Sistema de delays realista por bot
3. Soporte para diferentes categorías de stream
4. Validación de JSON y manejo de errores

Nota: Requiere API Key de NVIDIA NIM
"""

from stream_llm_advanced import AdvancedMultiBotGenerator
import json
from datetime import datetime

def demo_without_api():
    """Demo sin API Key (solo muestra estructura)."""
    
    print("=" * 80)
    print("StreamMind — Advanced LLM Generator (DEMO - Sin API)")
    print("=" * 80 + "\n")
    
    gen = AdvancedMultiBotGenerator()
    
    print("📋 Configuración del sistema:")
    print(f"   • Modelo: {gen.model_name}")
    print(f"   • Temperatura: {gen.temperature}")
    print(f"   • Delays configurados:")
    for bot, delay in gen.delays.items():
        print(f"      - {bot}: {delay}s")
    
    print("\n📌 Categorías de stream soportadas:")
    categories = {
        "gaming": "Juegos: CoD, Valorant, Fortnite (hype, emotes)",
        "esports": "Torneos profesionales (análisis, jerga competitiva)",
        "creative": "Arte, música, código (admirativo, constructivo)",
        "just_chatting": "Conversación y memes (casual, humor)",
        "variety_gaming": "Múltiples juegos (sorpresas, variado)",
        "irl": "Eventos en vivo (casual, reacciones inmediatas)"
    }
    for cat, desc in categories.items():
        print(f"   • {cat:20} → {desc}")
    
    print("\n🤖 Personalidades de bots:")
    personalities = {
        "HypeBot": "Entusiasta fanboy - MAYÚSCULAS, emojis, exclamaciones",
        "CritiBot": "Analítico reflexivo - preguntas inteligentes, crítica",
        "LurkerBot": "Cínico silencioso - humor seco, memes, ironía"
    }
    for bot, desc in personalities.items():
        print(f"   • {bot:12} → {desc}")
    
    print("\n📊 Estadísticas:")
    stats = gen.get_stats()
    print(f"   • Total de llamadas: {stats['total_calls']}")
    print(f"   • Llamadas exitosas: {stats['successful_calls']}")
    print(f"   • Llamadas fallidas: {stats['failed_calls']}")
    
    print("\n" + "=" * 80)
    print("EJEMPLO DE ESTRUCTURA JSON (respuesta esperada):")
    print("=" * 80 + "\n")
    
    example_response = {
        "HypeBot": "¡JAJAJA NOOOO! 🔥🔥 ¡ESO FUE UN CLUTCH INCREÍBLE!",
        "CritiBot": "Interesante estrategia... pero ¿crees que hubiera funcionado sin suerte?",
        "LurkerBot": "xd ese play no lo olvidamos",
        "delays": {
            "HypeBot": 2,
            "CritiBot": 3,
            "LurkerBot": 4
        },
        "generated_at": datetime.now().isoformat(),
        "category": "gaming"
    }
    
    print(json.dumps(example_response, indent=2, ensure_ascii=False))
    
    print("\n✅ Para usar con API:")
    print("   1. Obtén tu API Key de https://build.nvidia.com/")
    print("   2. En stt_gui.py, copia la key en el campo 'NVIDIA API Key'")
    print("   3. Los comentarios se generarán automáticamente\n")
    
    print("📚 Mejoras incluidas en esta versión:")
    improvements = [
        "✓ Prompts refinados por categoría de stream",
        "✓ Sistema de delays realista (2-5s entre bots)",
        "✓ Manejo robusto de errores y reintentos",
        "✓ Estadísticas de uso en tiempo real",
        "✓ Soporte para metadata de documentos",
        "✓ Integración completa con RAG avanzado"
    ]
    for imp in improvements:
        print(f"   {imp}")
    
    print("\n" + "=" * 80 + "\n")


def demo_with_api(api_key: str):
    """Demo con API Key (genera comentarios reales)."""
    
    print("=" * 80)
    print("StreamMind — Advanced LLM Generator (DEMO - Con API)")
    print("=" * 80 + "\n")
    
    gen = AdvancedMultiBotGenerator()
    gen.connect(api_key)
    
    # Ejemplos de diferentes categorías
    test_cases = [
        {
            "category": "gaming",
            "streamer_text": "¡Acabo de conseguir un triple kill!",
            "context": "Estamos jugando Valorant, el streak actual es 5 kills"
        },
        {
            "category": "just_chatting",
            "streamer_text": "¿Alguien quiere pizza?",
            "context": "Stream de conversación casual, el chat está hipeado"
        },
        {
            "category": "esports",
            "streamer_text": "Han perdido la ronda porque no hubo coordinación",
            "context": "Transmitiendo un torneo profesional de Valorant"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 TEST {i}/{len(test_cases)}: {test['category'].upper()}")
        print(f"   Streamer: {test['streamer_text']}")
        print(f"   Contexto: {test['context']}")
        print("\n   Generando comentarios...")
        
        try:
            comments = gen.generate_comments(
                test['streamer_text'],
                test['context'],
                stream_category=test['category'],
                include_delays=True
            )
            
            print(f"\n   ✅ Generados en tiempo real:")
            for bot, comment in comments.items():
                if bot not in ["delays", "generated_at", "category"]:
                    delay = comments.get("delays", {}).get(bot, "?")
                    print(f"      [{bot} → {delay}s]: {comment}")
            
        except Exception as e:
            print(f"\n   ❌ Error: {str(e)}")
    
    # Mostrar estadísticas finales
    print("\n" + "=" * 80)
    print("📊 ESTADÍSTICAS FINALES:")
    stats = gen.get_stats()
    print(f"   • Total de llamadas: {stats['total_calls']}")
    print(f"   • Exitosas: {stats['successful_calls']}")
    print(f"   • Fallidas: {stats['failed_calls']}")
    print(f"   • Tasa de éxito: {stats['success_rate']:.1f}%")
    print(f"   • Última llamada: {stats['last_call_time']}")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    import sys
    
    # Si se pasa API Key como argumento, usar demo con API
    if len(sys.argv) > 1 and sys.argv[1] != "--no-api":
        demo_with_api(sys.argv[1])
    else:
        demo_without_api()
    
    print("Para más información, ver: stream_llm_advanced.py")
