# planner_rutas_medellin.py 
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
import heapq
import argparse
import unicodedata
import json

# ========= Utilidades de normalización (sin tildes, trim, mayúsculas) =========
def norm(s: str) -> str:
    if s is None:
        return ""
    s = s.strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # quita tildes
    return s.upper()

# ===================== KB: Red Metro Medellín (aprox) =========================
RAW_EDGES: List[Dict] = [
    # LÍNEA A
    {"u": "Niquía",        "v": "Bello",         "line": "LineaA", "time_min": 3},
    {"u": "Bello",         "v": "Madera",        "line": "LineaA", "time_min": 3},
    {"u": "Madera",        "v": "Acevedo",       "line": "LineaA", "time_min": 3},
    {"u": "Acevedo",       "v": "Tricentenario", "line": "LineaA", "time_min": 3},
    {"u": "Tricentenario", "v": "Caribe",        "line": "LineaA", "time_min": 2},
    {"u": "Caribe",        "v": "Universidad",   "line": "LineaA", "time_min": 2},
    {"u": "Universidad",   "v": "Hospital",      "line": "LineaA", "time_min": 2},
    {"u": "Hospital",      "v": "Prado",         "line": "LineaA", "time_min": 2},
    {"u": "Prado",         "v": "Parque Berrío", "line": "LineaA", "time_min": 2},
    {"u": "Parque Berrío", "v": "San Antonio",   "line": "LineaA", "time_min": 2},
    {"u": "San Antonio",   "v": "Alpujarra",     "line": "LineaA", "time_min": 2},
    {"u": "Alpujarra",     "v": "Exposiciones",  "line": "LineaA", "time_min": 2},
    {"u": "Exposiciones",  "v": "Industriales",  "line": "LineaA", "time_min": 3},
    {"u": "Industriales",  "v": "Poblado",       "line": "LineaA", "time_min": 3},
    {"u": "Poblado",       "v": "Aguacatala",    "line": "LineaA", "time_min": 3},
    {"u": "Aguacatala",    "v": "Ayurá",         "line": "LineaA", "time_min": 3},
    {"u": "Ayurá",         "v": "Envigado",      "line": "LineaA", "time_min": 3},
    {"u": "Envigado",      "v": "Itagüí",        "line": "LineaA", "time_min": 3},
    {"u": "Itagüí",        "v": "Sabaneta",      "line": "LineaA", "time_min": 3},
    {"u": "Sabaneta",      "v": "La Estrella",   "line": "LineaA", "time_min": 3},
    # LÍNEA B
    {"u": "San Antonio", "v": "Cisneros",    "line": "LineaB", "time_min": 3},
    {"u": "Cisneros",    "v": "Suramericana","line": "LineaB", "time_min": 3},
    {"u": "Suramericana","v": "Estadio",     "line": "LineaB", "time_min": 2},
    {"u": "Estadio",     "v": "Floresta",    "line": "LineaB", "time_min": 2},
    {"u": "Floresta",    "v": "Santa Lucía", "line": "LineaB", "time_min": 3},
    {"u": "Santa Lucía", "v": "San Javier",  "line": "LineaB", "time_min": 3},
    # CABLE K
    {"u": "Acevedo",       "v": "Andalucía",    "line": "CableK", "time_min": 4},
    {"u": "Andalucía",     "v": "Popular",      "line": "CableK", "time_min": 4},
    {"u": "Popular",       "v": "Santo Domingo","line": "CableK", "time_min": 5},
    # CABLE J
    {"u": "San Javier", "v": "Juan XXIII", "line": "CableJ", "time_min": 4},
    {"u": "Juan XXIII", "v": "La Aurora",  "line": "CableJ", "time_min": 5},
]

def make_undirected(edges: List[Dict]) -> List[Dict]:
    out = []
    for e in edges:
        out.append(e)
        out.append({"u": e["v"], "v": e["u"], "line": e["line"], "time_min": e["time_min"]})
    return out

KB_EDGES = make_undirected(RAW_EDGES)

# ==== Índices de ayuda: set de estaciones y mapa slug->nombre canónico ====
def collect_nodes(edges: List[Dict]) -> Set[str]:
    nodes = set()
    for e in edges:
        nodes.add(e["u"])
        nodes.add(e["v"])
    return nodes

ALL_NODES = sorted(collect_nodes(KB_EDGES))
SLUG2CANON: Dict[str, str] = {}
for name in ALL_NODES:
    SLUG2CANON.setdefault(norm(name), name)  # primer canónico que vea

# ==================== Parámetros de la política =============================
TRANSFER_PENALTY_MIN = 4
DISALLOW_REPEATED_NODES = True

# ======================= Estructuras y Reglas ===============================
@dataclass(order=True)
class PrioritizedPath:
    priority: int
    cost_so_far: int = field(compare=False)
    node: str = field(compare=False)
    line: Optional[str] = field(compare=False)
    path: List[Tuple[str, Optional[str]]] = field(compare=False)

def movimientos_aplicables(nodo_actual: str) -> List[Dict]:
    return [e for e in KB_EDGES if e["u"] == nodo_actual]

def costo_transicion(linea_anterior: Optional[str], linea_siguiente: str, tiempo_base: int) -> int:
    if linea_anterior is None or linea_anterior == linea_siguiente:
        return tiempo_base
    return tiempo_base + TRANSFER_PENALTY_MIN

def heuristica(nodo: str, meta: str) -> int:
    return 0  # Dijkstra puro; puedes cambiar a A* si quieres

# ======================= Motor de Búsqueda ==================================
def mejor_ruta(origen: str, destino: str) -> Dict:
    # Normalizo entradas a canónico
    o_slug, d_slug = norm(origen), norm(destino)
    if o_slug not in SLUG2CANON:
        return {"ok": False, "error": f"Origen no reconocido: '{origen}'", "sugerencia": sugerir(origen)}
    if d_slug not in SLUG2CANON:
        return {"ok": False, "error": f"Destino no reconocido: '{destino}'", "sugerencia": sugerir(destino)}
    origen_canon = SLUG2CANON[o_slug]
    destino_canon = SLUG2CANON[d_slug]

    frontier: List[PrioritizedPath] = []
    inicial = PrioritizedPath(priority=0, cost_so_far=0, node=origen_canon, line=None, path=[(origen_canon, None)])
    heapq.heappush(frontier, inicial)

    mejor_costo: Dict[Tuple[str, Optional[str]], int] = {(origen_canon, None): 0}

    while frontier:
        actual = heapq.heappop(frontier)
        if actual.node == destino_canon:
            segmentos = []
            for i in range(len(actual.path) - 1):
                segmentos.append({
                    "from": actual.path[i][0],
                    "to": actual.path[i + 1][0],
                    "line": actual.path[i + 1][1]
                })
            transfers = sum(
                1 for i in range(1, len(actual.path) - 1)
                if actual.path[i][1] != actual.path[i + 1][1]
            )
            return {
                "ok": True,
                "total_time_min": actual.cost_so_far,
                "stops": [n for n, _ in actual.path],
                "segments": segmentos,
                "transfers": transfers
            }

        for e in movimientos_aplicables(actual.node):
            siguiente = e["v"]
            linea_sig = e["line"]
            base = e["time_min"]

            if DISALLOW_REPEATED_NODES and any(siguiente == n for n, _ in actual.path):
                continue

            paso = costo_transicion(actual.line, linea_sig, base)
            nuevo_costo = actual.cost_so_far + paso

            clave = (siguiente, linea_sig)
            if clave not in mejor_costo or nuevo_costo < mejor_costo[clave]:
                mejor_costo[clave] = nuevo_costo
                nueva_ruta = actual.path + [(siguiente, linea_sig)]
                prio = nuevo_costo + heuristica(siguiente, destino_canon)
                heapq.heappush(frontier, PrioritizedPath(
                    priority=prio,
                    cost_so_far=nuevo_costo,
                    node=siguiente,
                    line=linea_sig,
                    path=nueva_ruta
                ))
    return {"ok": False, "error": f"No encontré ruta de {origen} a {destino} con la KB actual."}

# ======================= Sugerencias de nombres ==============================
def sugerir(texto: str) -> Dict:
    slug = norm(texto)
    # coincidencias por prefijo o substring sobre slugs
    matches = [name for name in ALL_NODES if norm(name).startswith(slug) or slug in norm(name)]
    return {"coincidencias": matches, "estaciones_disponibles": ALL_NODES[:10] + (["..."] if len(ALL_NODES) > 10 else [])}

# ======================= CLI ================================================
def main():
    global TRANSFER_PENALTY_MIN

    parser = argparse.ArgumentParser(description="Planeador de rutas (Medellín) — Reglas + Dijkstra/A*")
    parser.add_argument("--from", dest="origen", help="Estación origen (con o sin tildes)")
    parser.add_argument("--to", dest="destino", help="Estación destino (con o sin tildes)")
    parser.add_argument("--penalty", dest="penalty", type=int, default=TRANSFER_PENALTY_MIN,
                        help="Penalización por transbordo en minutos (default: 4)")
    parser.add_argument("--list", dest="do_list", action="store_true",
                        help="Listar estaciones disponibles y salir")
    args = parser.parse_args()

    if args.do_list:
        print(json.dumps({"estaciones": ALL_NODES}, ensure_ascii=False, indent=2))
        return

    if not args.origen or not args.destino:
        print("Error: debes pasar --from ORIGEN y --to DESTINO (usa --list para ver estaciones).")
        return

    TRANSFER_PENALTY_MIN = args.penalty
    res = mejor_ruta(args.origen, args.destino)
    print(json.dumps(res, ensure_ascii=False, indent=2))  

if __name__ == "__main__":
    main()