# -*- coding: utf-8 -*-
"""
Demo: StreamMind Fase 5 - Sistema Completo de Evaluación
=========================================================

Demuestra:
1. Evaluación automática con LLM-as-Judge
2. Comparación real vs generado
3. Interfaz de test ciego para humanos
"""

from llm_as_judge import LLMJudge
from datetime import datetime

def demo_automatic_evaluation():
    """Demuestra evaluación automática."""
    
    print("\n" + "="*80)
    print("FASE 5 — EVALUACIÓN AUTOMÁTICA (LLM-as-Judge)")
    print("="*80 + "\n")
    
    judge = LLMJudge()
    
    # Ejemplo de evaluación individual
    print("📝 Evaluando comentario individual...\n")
    
    comment = "¡JAJAJA NOOOO! 🔥 ¡ESO FUE INCREÍBLE!"
    evaluation = judge.evaluate_comment(comment, "HypeBot")
    
    print(f"Comentario: '{comment}'")
    print(f"Personalidad: HypeBot")
    print(f"\n🔍 Rúbrica de Evaluación:")
    print(f"  • Naturalidad: {evaluation['criteria']['naturalidad']}/100")
    print(f"  • Coherencia: {evaluation['criteria']['coherencia']}/100")
    print(f"  • Longitud: {evaluation['criteria']['longitud']}/100")
    print(f"  • Jerga/Emotes: {evaluation['criteria']['jerga']}/100")
    print(f"  • Personalidad: {evaluation['criteria']['personalidad']}/100")
    print(f"\n📊 Resultado Final:")
    print(f"  Humanness Score: {evaluation['humanness_score']}/100")
    print(f"  Veredicto: {evaluation['verdict']}")
    print(f"  Confianza: {evaluation['confidence']:.0f}%")
    print(f"  Razonamiento: {evaluation['reasoning']}")
    
    # Comparación masiva
    print("\n" + "-"*80)
    print("📊 Comparando 50 reales vs 50 generados...\n")
    
    REAL_50 = [
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
        "lol",
        "jajaja",
        "WTF",
        "NOOOO",
        "YESSS",
        "¿QUÉ?",
        "Imposible",
        "Sin palabras",
        "Hermano",
        "Así es",
        "Amen",
        "True",
        "Facts",
        "Mira eso",
        "Épico",
        "Legendario",
        "Histórico",
        "Del año",
        "No me esperaba",
        "Sorprendente",
        "Inesperado",
        "Wow",
        "Omg",
        "Lmao",
        "Rofl",
    ]
    
    GENERATED_50 = [
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
        "lol hermano eso fue brutal",
        "jajaja no me lo esperaba para nada",
        "WTF ese clip va viral",
        "NOOOO CÓMO PUEDE SER POSIBLE",
        "YESSS QUÉ VICTORIA",
        "¿QUÉ ACABO DE VER AQUÍ?",
        "Imposible ese nivel de juego",
        "Sin palabras para esto",
        "Hermano eso fue legendario",
        "Así es la cosa hermano",
        "Amen a eso",
        "True ese es el nivel",
        "Facts no hay otra explicación",
        "Mira eso que jugador",
        "Épico definitivamente épico",
        "Legendario para los libros de historia",
        "Histórico este es un momentazo",
        "Del año sin dudas",
        "No me esperaba este nivel",
        "Sorprendente de verdad",
        "Inesperado completamente",
        "Wow qué jugada",
        "Omg increíble hermano",
        "Lmao no aguanto",
        "Rofl eso fue muy bueno",
    ]
    
    comparison = judge.compare_real_vs_generated(REAL_50, GENERATED_50, "gaming")
    
    print(f"[OK] Comentarios REALES (50):")
    print(f"  Humanness Score promedio: {comparison['real_avg_score']}/100")
    
    print(f"\n[INFO] Comentarios GENERADOS (50):")
    print(f"  Humanness Score promedio: {comparison['generated_avg_score']}/100")
    
    print(f"\n[STATS] ANALISIS COMPARATIVO:")
    print(f"  Tasa de Error (Humanos engañados): {comparison['misclassification_rate']:.1f}%")
    print(f"  Veredicto: {comparison['verdict']}")
    print(f"  Análisis: {comparison['analysis']}")
    
    # Estadísticas
    print(f"\n[STATS] ESTADISTICAS TOTALES:")
    stats = judge.get_stats()
    print(f"  Total de evaluaciones: {stats['total_evaluations']}")
    print(f"  Humanness Score promedio: {stats['avg_humanness']}/100")
    print(f"  Rango: {stats['min_humanness']}-{stats['max_humanness']}")
    print(f"  Clasificados como REAL: {stats['real_count']}")
    print(f"  Clasificados como GENERADO: {stats['generated_count']}")
    
    print("\n" + "="*80)
    print("[RESULT] CONCLUSION:")
    if comparison['misclassification_rate'] > 30:
        print(f"  [OK] EXITO - Los comentarios generados son INDISTINGUIBLES de los reales")
        print(f"  [OK] {comparison['misclassification_rate']:.1f}% de humanos fueron engañados")
        print("  [OK] El objetivo de Fase 5 fue ALCANZADO")
    else:
        print(f"  [!] Necesita mejora - Solo {comparison['misclassification_rate']:.1f}% confusión")
        print("  [!] Objetivo (>30%) no alcanzado - Refinar prompts")
    print("="*80 + "\n")


def demo_interfaces():
    """Muestra información de interfaces disponibles."""
    
    print("\n" + "="*80)
    print("INTERFACES DISPONIBLES PARA FASE 5")
    print("="*80 + "\n")
    
    print("1️⃣ EVALUACIÓN AUTOMÁTICA (llm_as_judge.py)")
    print("   Uso: from llm_as_judge import LLMJudge")
    print("   • Evaluación individual con rúbrica de 5 criterios")
    print("   • Comparación masiva (real vs generado)")
    print("   • Cálculo de tasa de error y humanness score")
    print("   • Integrable en pipelines de producción")
    
    print("\n2️⃣ TEST CIEGO PARA HUMANOS (blind_test_interface.py)")
    print("   Uso: python blind_test_interface.py")
    print("   • Interfaz GUI interactiva")
    print("   • 100 comentarios (50 reales + 50 generados)")
    print("   • Test aleatorizado")
    print("   • Resultados guardados en JSON")
    print("   • Meta: >30% tasa de error")
    
    print("\n3️⃣ INTEGRACIÓN EN stt_gui.py")
    print("   • Botón para ejecutar evaluación automática")
    print("   • Mostrar scores en panel de estadísticas")
    print("   • Guardar historial de evaluaciones")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    print("\n🚀 StreamMind — FASE 5: SISTEMA COMPLETO DE EVALUACIÓN\n")
    
    # Demo automático
    demo_automatic_evaluation()
    
    # Info interfaces
    demo_interfaces()
    
    print("[INFO] Para probar el test ciego:")
    print("  $ python blind_test_interface.py")
    print("\n[INFO] Para usar el juez automático:")
    print("  $ from llm_as_judge import LLMJudge")
    print("  $ judge = LLMJudge()")
    print("  $ score = judge.evaluate_comment('¡JAJAJA!', 'HypeBot')")
