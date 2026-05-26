# -*- coding: utf-8 -*-
"""
StreamMind — EDA (Exploratory Data Analysis) Fase 1
===================================================
Análisis exploratorio de los datos recolectados de Twitch IRC.

Genera:
- Distribuciones de longitudes
- Variación por categoría
- Detección de emotes y jerga
- Frecuencia de mensajes
- Reportes en JSON y gráficos

Uso:
    python eda_analysis.py
"""

import pandas as pd
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
import sys

# ─── Configuración ───────────────────────────────────────────────────────────

INPUT_FILE = "twitch_raw_data.csv"
OUTPUT_DIR = "eda_output"

# Emotes y jerga común en Twitch
TWITCH_EMOTES = ["Kappa", "PogU", "Hype", "WeirdChamp", "monkaS", "OMEGALUL", "LOL", "LULW"]
COMMON_SLANG = ["poggers", "pog", "hype", "f", "xd", "lol", "kek", "monka", "pepega", "sadge"]

# ─── Funciones de Análisis ───────────────────────────────────────────────────

def load_data(filename):
    """Carga los datos del CSV"""
    try:
        df = pd.read_csv(filename)
        print(f"[✓] Datos cargados: {len(df)} mensajes\n")
        return df
    except FileNotFoundError:
        print(f"[✗] Archivo no encontrado: {filename}")
        print("[*] Primero ejecuta: python twitch_irc_scraper.py")
        return None

def basic_stats(df):
    """Estadísticas básicas"""
    stats = {
        "total_messages": len(df),
        "unique_users": df["username"].nunique(),
        "unique_channels": df["channel"].nunique(),
        "date_range": f"{df['timestamp'].min()} a {df['timestamp'].max()}",
        "categories": df["stream_category"].unique().tolist()
    }
    return stats

def message_length_analysis(df):
    """Análisis de longitud de mensajes"""
    df["msg_length"] = df["message"].str.len()
    df["msg_words"] = df["message"].str.split().str.len()
    
    stats = {
        "avg_length": df["msg_length"].mean(),
        "median_length": df["msg_length"].median(),
        "min_length": df["msg_length"].min(),
        "max_length": df["msg_length"].max(),
        "avg_words": df["msg_words"].mean(),
        "median_words": df["msg_words"].median(),
        "percentiles": {
            "25%": df["msg_length"].quantile(0.25),
            "50%": df["msg_length"].quantile(0.50),
            "75%": df["msg_length"].quantile(0.75),
            "95%": df["msg_length"].quantile(0.95),
        }
    }
    return stats

def category_analysis(df):
    """Análisis por categoría"""
    category_stats = {}
    
    for category in df["stream_category"].unique():
        cat_df = df[df["stream_category"] == category]
        
        category_stats[category] = {
            "messages": len(cat_df),
            "unique_users": cat_df["username"].nunique(),
            "avg_msg_length": cat_df["message"].str.len().mean(),
            "avg_msg_words": cat_df["message"].str.split().str.len().mean(),
            "channels": cat_df["channel"].unique().tolist()
        }
    
    return category_stats

def detect_emotes_and_slang(df):
    """Detecta emotes y jerga en los mensajes"""
    all_messages = " ".join(df["message"].tolist()).lower()
    
    emote_counts = {}
    for emote in TWITCH_EMOTES:
        count = all_messages.count(emote.lower())
        if count > 0:
            emote_counts[emote] = count
    
    slang_counts = {}
    for slang in COMMON_SLANG:
        # Usar regex para palabra completa
        pattern = r"\b" + slang + r"\b"
        count = len(re.findall(pattern, all_messages))
        if count > 0:
            slang_counts[slang] = count
    
    # Top URLs
    url_pattern = r"https?://\S+"
    urls = re.findall(url_pattern, " ".join(df["message"].tolist()))
    url_counts = Counter(urls).most_common(10)
    
    return {
        "emotes": dict(sorted(emote_counts.items(), key=lambda x: x[1], reverse=True)),
        "slang": dict(sorted(slang_counts.items(), key=lambda x: x[1], reverse=True)),
        "top_urls": [{"url": url, "count": count} for url, count in url_counts]
    }

def user_activity_analysis(df):
    """Análisis de actividad de usuarios"""
    user_messages = df["username"].value_counts()
    
    return {
        "most_active_users": user_messages.head(10).to_dict(),
        "users_single_message": (user_messages == 1).sum(),
        "avg_messages_per_user": user_messages.mean(),
        "median_messages_per_user": user_messages.median()
    }

def channel_activity_analysis(df):
    """Análisis por canal"""
    channel_stats = {}
    
    for channel in df["channel"].unique():
        ch_df = df[df["channel"] == channel]
        
        channel_stats[channel] = {
            "messages": len(ch_df),
            "unique_users": ch_df["username"].nunique(),
            "avg_msg_length": ch_df["message"].str.len().mean(),
            "category": ch_df["stream_category"].iloc[0]
        }
    
    return dict(sorted(channel_stats.items(), key=lambda x: x[1]["messages"], reverse=True))

def sentiment_indicators(df):
    """Indicadores simples de sentimiento (emojis, puntuación)"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F700-\U0001F77F"  # alchemical symbols
        u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001FA00-\U0001FA6F"  # Chess Symbols
        u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+", flags=re.UNICODE)
    
    messages_with_emoji = 0
    messages_with_caps = 0
    messages_with_exclamation = 0
    messages_with_question = 0
    
    for msg in df["message"]:
        if emoji_pattern.search(msg):
            messages_with_emoji += 1
        if any(c.isupper() for c in msg):
            messages_with_caps += 1
        if "!" in msg:
            messages_with_exclamation += 1
        if "?" in msg:
            messages_with_question += 1
    
    total = len(df)
    
    return {
        "messages_with_emoji": {
            "count": messages_with_emoji,
            "percentage": (messages_with_emoji / total) * 100
        },
        "messages_with_caps": {
            "count": messages_with_caps,
            "percentage": (messages_with_caps / total) * 100
        },
        "messages_with_exclamation": {
            "count": messages_with_exclamation,
            "percentage": (messages_with_exclamation / total) * 100
        },
        "messages_with_question": {
            "count": messages_with_question,
            "percentage": (messages_with_question / total) * 100
        }
    }

def generate_report(df):
    """Genera reporte completo"""
    print("[*] Generando análisis...\n")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "basic_stats": basic_stats(df),
        "message_length_analysis": message_length_analysis(df),
        "category_analysis": category_analysis(df),
        "channel_activity": channel_activity_analysis(df),
        "user_activity": user_activity_analysis(df),
        "emotes_and_slang": detect_emotes_and_slang(df),
        "sentiment_indicators": sentiment_indicators(df)
    }
    
    return report

# ─── Visualizaciones y Salida ─────────────────────────────────────────────────

def print_report_summary(report):
    """Imprime resumen del reporte"""
    print("\n" + "=" * 80)
    print("RESUMEN DEL ANÁLISIS EXPLORATORIO (EDA)")
    print("=" * 80)
    
    # Estadísticas básicas
    stats = report["basic_stats"]
    print(f"\n📊 ESTADÍSTICAS BÁSICAS:")
    print(f"  Total mensajes: {stats['total_messages']}")
    print(f"  Usuarios únicos: {stats['unique_users']}")
    print(f"  Canales: {stats['unique_channels']}")
    print(f"  Categorías: {', '.join(stats['categories'])}")
    
    # Longitud de mensajes
    msg_len = report["message_length_analysis"]
    print(f"\n📝 LONGITUD DE MENSAJES:")
    print(f"  Promedio: {msg_len['avg_length']:.1f} caracteres")
    print(f"  Mediana: {msg_len['median_length']:.1f} caracteres")
    print(f"  Rango: {msg_len['min_length']} - {msg_len['max_length']} caracteres")
    print(f"  Promedio palabras: {msg_len['avg_words']:.1f}")
    
    # Análisis por categoría
    cat_stats = report["category_analysis"]
    print(f"\n🎮 ANÁLISIS POR CATEGORÍA:")
    for cat, stats in cat_stats.items():
        print(f"  {cat}: {stats['messages']} msgs, "
              f"promedio {stats['avg_msg_length']:.0f} chars")
    
    # Top usuarios
    print(f"\n👥 TOP USUARIOS:")
    for user, count in list(report["user_activity"]["most_active_users"].items())[:5]:
        print(f"  {user}: {count} mensajes")
    
    # Top canales
    print(f"\n📺 TOP CANALES:")
    for channel, stats in list(report["channel_activity"].items())[:5]:
        print(f"  #{channel}: {stats['messages']} mensajes")
    
    # Emotes y jerga
    print(f"\n😂 EMOTES MÁS COMUNES:")
    emotes = report["emotes_and_slang"]["emotes"]
    for emote, count in list(emotes.items())[:5]:
        print(f"  {emote}: {count}")
    
    print(f"\n💬 JERGA MÁS COMÚN:")
    slang = report["emotes_and_slang"]["slang"]
    for word, count in list(slang.items())[:5]:
        print(f"  {word}: {count}")
    
    # Indicadores de sentimiento
    sentiment = report["sentiment_indicators"]
    print(f"\n😊 INDICADORES DE SENTIMIENTO:")
    print(f"  Con emojis: {sentiment['messages_with_emoji']['percentage']:.1f}%")
    print(f"  Con mayúsculas: {sentiment['messages_with_caps']['percentage']:.1f}%")
    print(f"  Con exclamaciones: {sentiment['messages_with_exclamation']['percentage']:.1f}%")
    print(f"  Con preguntas: {sentiment['messages_with_question']['percentage']:.1f}%")
    
    print("\n" + "=" * 80)

def save_report_json(report, filename="eda_report.json"):
    """Guarda reporte como JSON"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[✓] Reporte JSON guardado: {filename}")
        return True
    except Exception as e:
        print(f"[✗] Error al guardar reporte: {e}")
        return False

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 80)
    print("StreamMind — EDA (Exploratory Data Analysis) Fase 1")
    print("=" * 80)
    
    # Cargar datos
    df = load_data(INPUT_FILE)
    if df is None:
        sys.exit(1)
    
    # Generar análisis
    report = generate_report(df)
    
    # Mostrar resumen
    print_report_summary(report)
    
    # Guardar reporte
    save_report_json(report)
    
    print("\n[✓] Análisis completado exitosamente")
