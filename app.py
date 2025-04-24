from flask import Flask, render_template, jsonify, request
import requests, json, threading, asyncio
from collections import defaultdict
from datetime import datetime
import websockets

app = Flask(__name__)
RANGO = 500
liquidaciones_por_rango = defaultdict(float)

def agrupar_por_rango(precio):
    base = int(float(precio) // RANGO * RANGO)
    return f"{base}-{base + RANGO}"

def iniciar_websocket(symbol):
    async def recibir_liquidaciones():
        url = f"wss://fstream.binance.com/ws/{symbol.lower()}@forceOrder"
        async with websockets.connect(url) as ws:
            while True:
                mensaje = await ws.recv()
                data = json.loads(mensaje)
                orden = data.get("o", {})
                precio = float(orden.get("ap", 0))
                cantidad = float(orden.get("q", 0))
                rango = agrupar_por_rango(precio)
                liquidaciones_por_rango[rango] += cantidad
    asyncio.run(recibir_liquidaciones())

def lanzar_hilo_liquidaciones():
    threading.Thread(target=iniciar_websocket, args=("BTCUSDT",), daemon=True).start()

lanzar_hilo_liquidaciones()

@app.route('/api/liquidaciones')
def get_liquidaciones():
    ordenadas = sorted(liquidaciones_por_rango.items(), key=lambda x: int(x[0].split('-')[0]))
    return jsonify([{"price_range": r, "qty": round(q, 3)} for r, q in ordenadas if q > 0])

@app.route('/')
def home():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
