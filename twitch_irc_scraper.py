# -*- coding: utf-8 -*-
"""
StreamMind — Twitch IRC Scraper (Fase 1: Recolección de Datos)
==============================================================
Conecta a Twitch IRC (justinfan - anónimo) y recolecta mensajes de múltiples canales.
Guarda: username, message, timestamp, channel, stream_category

Uso:
    python twitch_irc_scraper.py
    
Nota: No requiere login. Usa justinfan (conexión anónima IRC).
"""

import socket
import threading
import time
import csv
import re
import sys
from datetime import datetime
from collections import defaultdict

# ─── Configuración ───────────────────────────────────────────────────────────

TWITCH_IRC_SERVER = "irc.chat.twitch.tv"
TWITCH_IRC_PORT = 6667
NICKNAME = "justinfan123456"  # Usuario anónimo

# Canales populares a scrapear (variados: gaming, esports, chat, creative)
CHANNELS = {
    "xqcow": "variety_gaming",          # Streamers de variety
    "pokimane": "gaming",                # Gaming femenino popular
    "valorant": "esports",               # Torneo oficial
    "leagueoflegends": "esports",        # League esports
    "just_chatting": "just_chatting",    # Categoría de chat
    "sykkuno": "gaming",                 # Streamer gaming
    "ibai": "variety_gaming",            # Español popular
    "rubius": "gaming",                  # Español gaming
    "auronplay": "variety_gaming",       # Español variety
    "creative": "creative",              # Categoría creativa
}

# Parámetros de recolección
MESSAGES_PER_CHANNEL = 500  # Mensajes por canal (total ~5000)
TIMEOUT_PER_CHANNEL = 300   # Timeout por canal (5 minutos)

# Salida
OUTPUT_FILE = "twitch_raw_data.csv"

# ─── Clase Scraper ───────────────────────────────────────────────────────────

class TwitchIRCScraper:
    def __init__(self):
        self.socket = None
        self.messages = defaultdict(list)
        self.message_counts = defaultdict(int)
        self.is_running = False
        self.lock = threading.Lock()
        
    def connect(self):
        """Conecta a Twitch IRC"""
        print("[INFO] Conectando a Twitch IRC...")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((TWITCH_IRC_SERVER, TWITCH_IRC_PORT))
            
            # Enviar credenciales anónimas
            self.send_raw(f"NICK {NICKNAME}")
            self.send_raw(f"USER {NICKNAME} * * :{NICKNAME}")
            
            # Esperar a que se conecte
            time.sleep(1)
            print("[OK] Conectado a IRC de Twitch\n")
            return True
        except Exception as e:
            print(f"[ERROR] Error de conexión: {e}")
            return False

    def send_raw(self, msg):
        """Envía comando raw a IRC"""
        try:
            self.socket.send((msg + "\r\n").encode("utf-8"))
        except:
            pass

    def join_channel(self, channel):
        """Se une a un canal"""
        self.send_raw(f"JOIN #{channel}")
        print(f"[-->] Uniéndose a #{channel}...")

    def leave_channel(self, channel):
        """Sale de un canal"""
        self.send_raw(f"PART #{channel}")

    def receive_messages(self):
        """Lee mensajes del socket IRC"""
        try:
            while self.is_running:
                data = self.socket.recv(4096).decode("utf-8", errors="ignore")
                if not data:
                    break
                
                for line in data.split("\r\n"):
                    if line:
                        self._process_line(line)
        except Exception as e:
            print(f"[✗] Error recibiendo mensajes: {e}")

    def _process_line(self, line):
        """Procesa una línea IRC"""
        # Responder a PING para mantener conexión viva
        if line.startswith("PING"):
            self.send_raw(f"PONG {line.split()[1]}")
            return

        # Parsear mensajes PRIVMSG
        # Formato: :username!userid@userid.tmi.twitch.tv PRIVMSG #channel :message
        match = re.match(
            r":(\w+)!(\w+)@(\w+\.tmi\.twitch\.tv) PRIVMSG #(\w+) :(.+)",
            line
        )
        
        if match:
            username = match.group(1)
            channel = match.group(4).lower()
            message = match.group(5)
            timestamp = datetime.now().isoformat()
            
            # Guardar si el canal está en nuestra lista
            if channel in CHANNELS:
                with self.lock:
                    category = CHANNELS[channel]
                    self.messages[channel].append({
                        "username": username,
                        "message": message,
                        "timestamp": timestamp,
                        "channel": channel,
                        "stream_category": category
                    })
                    self.message_counts[channel] += 1
                    
                    # Mostrar progreso
                    count = self.message_counts[channel]
                    if count % 50 == 0:
                        print(f"[{channel}] {count}/{MESSAGES_PER_CHANNEL} mensajes")

    def scrape_all_channels(self):
        """Conecta y scrapeaá todos los canales"""
        if not self.connect():
            return False

        self.is_running = True

        # Iniciar thread de recepción
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()

        # Unirnos a todos los canales
        for channel in CHANNELS.keys():
            self.join_channel(channel)
            time.sleep(0.5)

        # Esperando a recolectar suficientes mensajes
        start_time = time.time()
        total_messages_target = len(CHANNELS) * MESSAGES_PER_CHANNEL

        print(f"\n[*] Recolectando mensajes (objetivo: {total_messages_target} mensajes)...")
        print(f"[*] Timeout: {TIMEOUT_PER_CHANNEL * len(CHANNELS)} segundos (~{len(CHANNELS) * TIMEOUT_PER_CHANNEL / 60:.1f} minutos)\n")

        while self.is_running:
            total_collected = sum(self.message_counts.values())
            
            # Mostrar progreso cada 5 segundos
            if int(time.time()) % 5 == 0:
                elapsed = time.time() - start_time
                remaining_channels = sum(1 for ch in CHANNELS if self.message_counts[ch] < MESSAGES_PER_CHANNEL)
                print(f"[{elapsed:.0f}s] Total: {total_collected}/{total_messages_target} mensajes "
                      f"({remaining_channels} canales activos)")

            # Condición de salida: todas los canales completos O timeout
            if total_collected >= total_messages_target:
                print(f"\n[✓] Objetivo alcanzado: {total_collected} mensajes")
                break
            elif (time.time() - start_time) > (TIMEOUT_PER_CHANNEL * len(CHANNELS)):
                print(f"\n[⏱] Timeout alcanzado con {total_collected} mensajes")
                break

            time.sleep(1)

        self.is_running = False
        time.sleep(0.5)
        self.disconnect()
        return True

    def disconnect(self):
        """Desconecta de IRC"""
        if self.socket:
            for channel in CHANNELS.keys():
                self.leave_channel(channel)
                time.sleep(0.2)
            self.socket.close()
        print("[OK] Desconectado de IRC")

    def save_to_csv(self, filename=OUTPUT_FILE):
        """Guarda los mensajes en CSV"""
        print(f"\n[INFO] Guardando {sum(len(msgs) for msgs in self.messages.values())} mensajes en {filename}...")
        
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["username", "message", "timestamp", "channel", "stream_category"]
                )
                writer.writeheader()
                
                for channel_messages in self.messages.values():
                    for msg in channel_messages:
                        writer.writerow(msg)
            
            print(f"[OK] Archivo guardado: {filename}")
            print(f"    Canales: {list(self.messages.keys())}")
            print(f"    Mensajes totales: {sum(len(msgs) for msgs in self.messages.values())}")
            return True
        except Exception as e:
            print(f"[ERROR] Error al guardar: {e}")
            return False


# ─── Ejecutar ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 80)
    print("StreamMind — Twitch IRC Scraper (Fase 1)")
    print("=" * 80)
    print(f"\nCanales: {', '.join(CHANNELS.keys())}")
    print(f"Objetivo: {MESSAGES_PER_CHANNEL} mensajes por canal ({len(CHANNELS) * MESSAGES_PER_CHANNEL} total)")
    print("=" * 80 + "\n")

    scraper = TwitchIRCScraper()
    
    try:
        if scraper.scrape_all_channels():
            scraper.save_to_csv()
            print("\n[OK] Recolección completada exitosamente")
        else:
            print("\n[ERROR] Error en recolección")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[WARNING] Interrupción del usuario")
        scraper.disconnect()
        scraper.save_to_csv()
