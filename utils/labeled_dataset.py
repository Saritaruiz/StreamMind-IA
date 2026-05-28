# -*- coding: utf-8 -*-
"""
StreamMind — Labeled Dataset Generator (Fase 1)
===============================================
Genera dataset de 50 comentarios reales etiquetados (es_humano = 1)
para usar en evaluación final.

Uso:
    python labeled_dataset.py
"""

import pandas as pd
import numpy as np
import random
import json
from datetime import datetime

# ─── Configuración ───────────────────────────────────────────────────────────

INPUT_FILE = "data/twitch_raw_data.csv"
OUTPUT_FILE = "data/evaluation_labeled_dataset.csv"
OUTPUT_JSON = "data/evaluation_labeled_dataset.json"

SAMPLE_SIZE = 50  # 50 comentarios reales etiquetados

# ─── Funciones ───────────────────────────────────────────────────────────────

def load_data(filename):
    """Carga datos recolectados"""
    try:
        df = pd.read_csv(filename)
        print(f"[OK] Datos cargados: {len(df)} mensajes disponibles\n")
        return df
    except FileNotFoundError:
        print(f"[ERROR] Archivo no encontrado: {filename}")
        return None

def filter_quality_messages(df):
    """
    Filtra mensajes de calidad basado en análisis EDA.
    
    Criterios (relajados):
    - Longitud mínima: 2 caracteres (para capturar 'xd', 'lol', 'F')
    - Longitud máxima: 250 caracteres (mediana real: 8, promedio: 14)
    - URLs: máximo 1 por mensaje
    - Excluir bots conocidos
    
    Nota: El dataset real mostró 1,570 mensajes con longitud mediana de 8 chars.
    """
    
    # Eliminar mensajes vacíos o 1 char (mantenemos 2+ para 'xd', 'lol', 'F', etc)
    df = df[df["message"].str.len() >= 2].copy()
    
    # Eliminar mensajes muy largos (copy-pasta, spam)
    # Límite: 250 chars (máximo encontrado fue 168)
    df = df[df["message"].str.len() <= 250].copy()
    
    # Eliminar mensajes con muchas URLs (spamers)
    df = df[df["message"].str.count(r"http") <= 1].copy()
    
    # Eliminar bots conocidos
    bot_names = ["moobot", "nightbot", "streamelements", "streamlabs", "botfactory"]
    for bot in bot_names:
        df = df[~df["username"].str.lower().str.contains(bot, na=False)]
    
    print(f"[OK] Después de filtrado: {len(df)} mensajes de calidad\n")
    return df

def select_diverse_sample(df, sample_size=SAMPLE_SIZE):
    """
    Selecciona muestra diversa por categoría.
    
    Nota: Si hay pocas categorías, aumenta por canal/usuario
    para asegurar diversidad.
    """
    
    samples = []
    categories = df["stream_category"].unique()
    
    # Primera estrategia: distribuir por categoría
    samples_per_category = sample_size // len(categories)
    remainder = sample_size % len(categories)
    
    print(f"[INFO] Seleccionando {sample_size} mensajes diversos:\n")
    print(f"  Estrategia: Por categoría (distribución uniforme)\n")
    
    total_collected = 0
    
    for i, category in enumerate(categories):
        cat_df = df[df["stream_category"] == category]
        
        # Asignar extra muestra al último si hay remainder
        n_samples = samples_per_category + (remainder if i == len(categories) - 1 else 0)
        n_samples = min(n_samples, len(cat_df))
        
        if len(cat_df) >= n_samples:
            cat_sample = cat_df.sample(n=n_samples, random_state=42)
            samples.append(cat_sample)
            total_collected += n_samples
            print(f"  {category}: {n_samples} mensajes")
    
    # Si no tenemos suficientes, expandir muestreo a nivel de usuario/canal
    if total_collected < sample_size:
        # Samplear del resto sin limite de categoría
        all_sampled = pd.concat(samples, ignore_index=True)
        remaining_needed = sample_size - total_collected
        remaining_df = df[~df.index.isin(all_sampled.index)]
        
        if len(remaining_df) > 0:
            extra_samples = remaining_df.sample(
                n=min(remaining_needed, len(remaining_df)),
                random_state=42
            )
            samples.append(extra_samples)
            total_collected += len(extra_samples)
            print(f"\n  Expansión (por diversidad): {len(extra_samples)} mensajes adicionales")
    
    result = pd.concat(samples, ignore_index=True)
    print(f"\n[OK] Total seleccionados: {len(result)} mensajes\n")
    
    return result

def create_labeled_dataset(df):
    """
    Crea dataset final etiquetado.
    
    Args:
        df: DataFrame con mensajes reales de Twitch
        
    Returns:
        DataFrame con columnas de etiquetas (es_humano, quality_score, etc.)
    """
    
    dataset = df.copy()
    
    # Añadir columna es_humano = 1 (todos son reales)
    dataset["es_humano"] = 1
    dataset["is_real_human_comment"] = True
    dataset["generated_by"] = "real_twitch_user"
    dataset["quality_score"] = 5  # 5 = real human
    
    # Reordenar y renombrar columnas
    dataset = dataset[[
        "username",
        "message",
        "timestamp",
        "channel",
        "stream_category",
        "es_humano",
        "is_real_human_comment",
        "generated_by",
        "quality_score"
    ]].copy()
    
    # Renombrar para claridad
    dataset.columns = [
        "user",
        "comment",
        "timestamp",
        "channel",
        "category",
        "es_humano",
        "is_real",
        "source",
        "quality_score"
    ]
    
    return dataset.reset_index(drop=True)

def add_metadata(dataset, df_original):
    """Añade metadatos del análisis"""
    
    metadata = {
        "dataset_name": "StreamMind Real Chat Dataset (Evaluation)",
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "total_comments": int(len(dataset)),  # Convertir a int nativo
        "real_human_comments": int(len(dataset)),
        "generated_comments": 0,
        "sources": list(dataset["channel"].unique()),
        "categories": list(dataset["category"].unique()),
        "stats": {
            "avg_comment_length": float(dataset["comment"].str.len().mean()),
            "min_comment_length": int(dataset["comment"].str.len().min()),
            "max_comment_length": int(dataset["comment"].str.len().max()),
            "unique_users": int(dataset["user"].nunique()),
            "unique_channels": int(dataset["channel"].nunique()),
        },
        "usage": {
            "purpose": "LLM evaluation - Humanness Score calculation",
            "labeling_method": "Extracted from real Twitch chat",
            "quality_criteria": [
                "No spam/bots",
                "2-250 characters (relajado para capturar 'xd', 'lol')",
                "Max 1 URL per comment",
                "Diverse by category and user"
            ]
        }
    }
    
    return metadata

def save_dataset(dataset, metadata, csv_filename=OUTPUT_FILE, json_filename=OUTPUT_JSON):
    """
    Guarda dataset en CSV y JSON con conversión de tipos.
    
    Nota: Convierte tipos numpy (int64) a Python nativos para
    compatibilidad con JSON serialization.
    """
    
    try:
        # Guardar CSV
        dataset.to_csv(csv_filename, index=False, encoding="utf-8")
        print(f"[OK] CSV guardado: {csv_filename}")
        
        # Preparar datos JSON con conversión segura de tipos
        records = dataset.to_dict(orient="records")
        
        # Convertir tipos numpy a Python nativos
        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                # Convertir tipos numpy a Python
                if pd.isna(value):
                    cleaned_record[key] = None
                elif hasattr(value, 'item'):  # int64, float64, etc
                    cleaned_record[key] = value.item()
                elif isinstance(value, (np.integer, np.floating)):
                    cleaned_record[key] = float(value) if isinstance(value, np.floating) else int(value)
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)
        
        data_json = {
            "metadata": metadata,
            "total_comments": len(cleaned_records),
            "comments": cleaned_records
        }
        
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(data_json, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] JSON guardado: {json_filename}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error al guardar: {e}")
        return False

def print_dataset_summary(dataset):
    """Imprime resumen del dataset"""
    
    print("\n" + "=" * 80)
    print("DATASET ETIQUETADO PARA EVALUACIÓN")
    print("=" * 80)
    
    print(f"\n📊 INFORMACIÓN GENERAL:")
    print(f"  Total comentarios: {len(dataset)}")
    print(f"  Usuarios únicos: {dataset['user'].nunique()}")
    print(f"  Canales: {dataset['channel'].nunique()}")
    print(f"  Categorías: {dataset['category'].nunique()}")
    
    print(f"\n📝 LONGITUD DE COMENTARIOS:")
    print(f"  Promedio: {dataset['comment'].str.len().mean():.1f} caracteres")
    print(f"  Rango: {dataset['comment'].str.len().min()}-{dataset['comment'].str.len().max()}")
    
    print(f"\n🏆 ETIQUETADO:")
    print(f"  es_humano = 1: {(dataset['es_humano'] == 1).sum()} comentarios")
    print(f"  Todos son comentarios reales de Twitch")
    
    print(f"\n🎮 DISTRIBUCIÓN POR CATEGORÍA:")
    for category, count in dataset["category"].value_counts().items():
        print(f"  {category}: {count}")
    
    print(f"\n📺 TOP CANALES:")
    for channel, count in dataset["channel"].value_counts().head(5).items():
        print(f"  #{channel}: {count}")
    
    print(f"\n💬 EJEMPLOS DE COMENTARIOS:")
    for idx, row in dataset.head(3).iterrows():
        print(f"\n  [{idx+1}] @{row['user']} ({row['channel']}):")
        print(f"      \"{row['comment']}\"")
        print(f"      Categoría: {row['category']}")
    
    print("\n" + "=" * 80)

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 80)
    print("StreamMind — Labeled Dataset Generator")
    print("=" * 80)
    
    # Cargar datos
    df = load_data(INPUT_FILE)
    if df is None:
        print("[✗] No se pueden cargar los datos. Ejecuta primero: python twitch_irc_scraper.py")
        exit(1)
    
    # Filtrar calidad
    print("[*] Filtrando mensajes de calidad...")
    df_filtered = filter_quality_messages(df)
    
    if len(df_filtered) < SAMPLE_SIZE:
        print(f"[⚠] Advertencia: Solo {len(df_filtered)} mensajes de calidad disponibles")
        print(f"    Necesitamos {SAMPLE_SIZE}. Aumentando muestra original...")
        SAMPLE_SIZE = min(SAMPLE_SIZE, len(df_filtered))
    
    # Seleccionar muestra diversa
    print("[*] Seleccionando muestra diversa...")
    dataset_sample = select_diverse_sample(df_filtered, sample_size=SAMPLE_SIZE)
    
    # Crear dataset etiquetado
    print("[*] Creando dataset etiquetado...")
    dataset_final = create_labeled_dataset(dataset_sample)
    
    # Metadatos
    metadata = add_metadata(dataset_final, df)
    
    # Guardar
    print("[*] Guardando dataset...")
    if save_dataset(dataset_final, metadata):
        print_dataset_summary(dataset_final)
        print("\n[✓] Dataset etiquetado completado")
        print(f"\n✨ Archivos generados:")
        print(f"   - {OUTPUT_FILE}")
        print(f"   - {OUTPUT_JSON}")
        print(f"\n📖 Listo para usar en: LLM-as-judge evaluation")
    else:
        print("[✗] Error al generar dataset")
        exit(1)
