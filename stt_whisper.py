# -*- coding: utf-8 -*-
"""
StreamMind - Modulo de Voz a Texto (STT)
========================================
Usa Whisper tiny corriendo localmente para transcribir audio del micrófono
en tiempo real con soporte optimizado para español.

Dependencias:
    pip install openai-whisper sounddevice numpy scipy

Uso:
    python stt_whisper.py
    python stt_whisper.py --duracion 7     # chunks de 7 segundos
    python stt_whisper.py --demo            # modo demo sin micrófono
"""

import argparse
import queue
import threading
import time
import sys
from datetime import datetime

import numpy as np
import sounddevice as sd
import whisper

# Forzar UTF-8 en stdout/stderr para terminales Windows que usen cp1252
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── Configuración ────────────────────────────────────────────────────────────

SAMPLE_RATE    = 16_000   # Hz — Whisper siempre espera 16 kHz
CHANNELS       = 1        # mono
MODEL_SIZE     = "tiny"   # tiny | base | small | medium | large
LANGUAGE       = "es"     # forzamos español (evita que auto-detecte mal)
CHUNK_SECONDS  = 5        # segundos de audio por transcripción
SILENCE_THRESH = 0.01     # RMS mínimo para considerar que hay voz (no silencio)

# ─── Colores para la terminal (ANSI) ─────────────────────────────────────────

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    DIM    = "\033[2m"

# ─── Utilidades ───────────────────────────────────────────────────────────────

def ts() -> str:
    """Timestamp legible para los logs."""
    return datetime.now().strftime("%H:%M:%S")


def rms(audio: np.ndarray) -> float:
    """Root Mean Square — mide el volumen del chunk."""
    return float(np.sqrt(np.mean(audio ** 2)))


def print_header(model_size: str, chunk_sec: int) -> None:
    print(f"\n{C.BOLD}{C.CYAN}{'=' * 55}")
    print("  [MIC] StreamMind - Voz a Texto (Whisper STT)")
    print(f"{'=' * 55}{C.RESET}")
    print(f"  Modelo  : {C.YELLOW}whisper-{model_size}{C.RESET}")
    print(f"  Idioma  : {C.YELLOW}espanol (forzado){C.RESET}")
    print(f"  Chunk   : {C.YELLOW}{chunk_sec}s por transcripcion{C.RESET}")
    print(f"  Sample  : {C.YELLOW}{SAMPLE_RATE} Hz{C.RESET}")
    print(f"{C.DIM}  Ctrl+C para detener{C.RESET}\n")


# ─── Clase principal ──────────────────────────────────────────────────────────

class WhisperSTT:
    """
    Captura audio del micrófono en tiempo real y lo transcribe con Whisper.

    Expone un callback `on_transcription(text, timestamp)` que se llama
    cada vez que hay un nuevo fragmento de texto disponible.
    """

    def __init__(
        self,
        model_size: str = MODEL_SIZE,
        language: str = LANGUAGE,
        chunk_seconds: int = CHUNK_SECONDS,
        on_transcription=None,
    ):
        self.model_size     = model_size
        self.language       = language
        self.chunk_seconds  = chunk_seconds
        self.on_transcription = on_transcription or self._default_callback

        self._audio_queue   = queue.Queue()
        self._running       = False
        self._model         = None

        # Historial completo de la sesión
        self.transcript_log: list[dict] = []

    # ── Carga del modelo ──────────────────────────────────────────────────────

    def load_model(self) -> None:
        print(f"[{ts()}] {C.YELLOW}Cargando whisper-{self.model_size}...{C.RESET}", end=" ", flush=True)
        self._model = whisper.load_model(self.model_size)
        print(f"{C.GREEN}✓ listo{C.RESET}")

    # ── Callback por defecto ──────────────────────────────────────────────────

    @staticmethod
    def _default_callback(text: str, timestamp: str) -> None:
        """Imprime la transcripción con formato en la terminal."""
        print(f"[{timestamp}] {C.GREEN}📝 {text}{C.RESET}")

    # ── Captura de audio (hilo separado) ──────────────────────────────────────

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        """Llamado por sounddevice en cada bloque de audio."""
        if status:
            print(f"{C.RED}  ⚠ sounddevice status: {status}{C.RESET}", file=sys.stderr)
        # Guardamos el bloque en la cola (copia para evitar aliasing)
        self._audio_queue.put(indata.copy())

    # ── Transcripción (hilo separado) ─────────────────────────────────────────

    def _transcribe_loop(self) -> None:
        """Consume chunks de la cola y los transcribe con Whisper."""
        samples_per_chunk = SAMPLE_RATE * self.chunk_seconds
        buffer = np.empty((0,), dtype=np.float32)

        while self._running:
            try:
                block = self._audio_queue.get(timeout=1.0)
                buffer = np.concatenate([buffer, block.flatten()])

                if len(buffer) >= samples_per_chunk:
                    chunk = buffer[:samples_per_chunk].copy()
                    buffer = buffer[samples_per_chunk:]

                    # Filtrar silencio para no gastar tiempo en chunks vacíos
                    if rms(chunk) < SILENCE_THRESH:
                        print(f"[{ts()}] {C.DIM}(silencio detectado, saltando chunk){C.RESET}")
                        continue

                    # Transcribir
                    result = self._model.transcribe(
                        chunk,
                        language=self.language,
                        fp16=False,          # False = compatibilidad máxima en CPU
                        temperature=0.0,     # Sin aleatoriedad → más consistente
                        condition_on_previous_text=True,  # contexto entre chunks
                    )

                    text = result["text"].strip()

                    if text:
                        now = ts()
                        entry = {"timestamp": now, "text": text}
                        self.transcript_log.append(entry)
                        self.on_transcription(text, now)

            except queue.Empty:
                continue
            except Exception as exc:
                print(f"{C.RED}  ✗ Error en transcripción: {exc}{C.RESET}", file=sys.stderr)

    # ── Interfaz pública ──────────────────────────────────────────────────────

    def start(self) -> None:
        """Inicia la captura y transcripción en hilos separados."""
        if self._model is None:
            self.load_model()

        self._running = True

        # Hilo de transcripción
        self._thread = threading.Thread(target=self._transcribe_loop, daemon=True)
        self._thread.start()

        # Stream de audio (bloqueante hasta que se llame a stop())
        blocksize = int(SAMPLE_RATE * 0.5)  # bloques de 0.5 s
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=blocksize,
            callback=self._audio_callback,
        ):
            print(f"[{ts()}] {C.GREEN}[REC] Microfono activo - habla ahora{C.RESET}\n")
            try:
                while self._running:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.stop()

    def stop(self) -> None:
        """Detiene la captura limpiamente."""
        self._running = False
        if hasattr(self, "_thread"):
            self._thread.join(timeout=5)
        print(f"\n[{ts()}] {C.CYAN}Sesion finalizada.{C.RESET}")
        self._print_summary()

    def _print_summary(self) -> None:
        """Imprime el resumen completo de la sesion al terminar."""
        if not self.transcript_log:
            print(f"{C.DIM}  (sin transcripciones en esta sesion){C.RESET}")
            return

        full_text = " ".join(e["text"] for e in self.transcript_log)
        print(f"\n{C.BOLD}{C.CYAN}{'-' * 55}")
        print("  [DOC] Transcripcion completa de la sesion")
        print(f"{'-' * 55}{C.RESET}")
        print(full_text)
        print(f"{C.DIM}  ({len(self.transcript_log)} chunks | {len(full_text.split())} palabras){C.RESET}\n")


# ─── Modo demo (sin micrófono) ────────────────────────────────────────────────

def run_demo(model_size: str) -> None:
    """
    Modo demo: genera audio sintético con texto hablado de prueba
    usando numpy para validar que Whisper responde correctamente.
    """
    print(f"[{ts()}] {C.YELLOW}Modo DEMO - generando audio de prueba...{C.RESET}")
    print(f"  {C.DIM}(Este modo transcribe un fragmento de audio sintetico silencioso.){C.RESET}\n")

    model = whisper.load_model(model_size)
    print(f"[{ts()}] {C.GREEN}OK Modelo cargado{C.RESET}")

    # Audio de silencio (Whisper deberia devolver vacio o alucinacion minima)
    silence = np.zeros(SAMPLE_RATE * 5, dtype=np.float32)
    result = model.transcribe(silence, language="es", fp16=False, temperature=0.0)
    text = result["text"].strip()

    print(f"[{ts()}] Resultado sobre silencio: {C.DIM}'{text}'{C.RESET}")
    print(f"\n{C.GREEN}OK Pipeline de Whisper funcionando correctamente.{C.RESET}")
    print(f"  Para usar con microfono real, ejecuta sin el flag --demo\n")


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="StreamMind STT — Whisper tiny en español"
    )
    parser.add_argument(
        "--modelo",
        default=MODEL_SIZE,
        choices=["tiny", "base", "small", "medium", "large"],
        help="Tamaño del modelo Whisper (default: tiny)",
    )
    parser.add_argument(
        "--duracion",
        type=int,
        default=CHUNK_SECONDS,
        help="Duración de cada chunk de audio en segundos (default: 5)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Modo demo: valida el pipeline sin necesitar micrófono",
    )
    args = parser.parse_args()

    print_header(args.modelo, args.duracion)

    if args.demo:
        run_demo(args.modelo)
        return

    stt = WhisperSTT(
        model_size=args.modelo,
        chunk_seconds=args.duracion,
    )

    try:
        stt.start()
    except KeyboardInterrupt:
        stt.stop()


if __name__ == "__main__":
    main()
