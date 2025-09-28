# Planeador de Rutas del Metro de Medellín (IA)

Este proyecto es un sistema inteligente sencillo que hice como parte de mi curso de **Inteligencia Artificial Avanzada**.  
La idea fue implementar un **planificador de rutas** usando reglas lógicas y un algoritmo de búsqueda (Dijkstra/A*) para encontrar la mejor forma de moverse en el **Metro de Medellín**.

## Objetivo:
Representar el conocimiento de la red de transporte (estaciones, conexiones y tiempos aproximados) y aplicar un motor de búsqueda que calcule la ruta óptima entre un punto de origen y un destino.  
El sistema también tiene en cuenta los **transbordos** y les aplica una **penalización de minutos** para simular el tiempo adicional que se gasta al cambiar de línea.

## Cómo está hecho: 
- **Lenguaje:** Python 3
- **Conocimiento (KB):** listado de estaciones y conexiones de la Línea A, Línea B, Cable K y Cable J.
- **Motor de inferencia:** búsqueda tipo Dijkstra (si se activa heurística se comporta como A*).
- **Reglas principales:**
  1. Solo se puede avanzar por conexiones válidas.
  2. No se permiten ciclos (no volver atrás innecesariamente).
  3. Cada transbordo tiene un costo adicional configurable (`--penalty`).

## Cómo usarlo:
1. Clonar el repositorio y entrar a la carpeta:
   ```bash
   git clone <URL_REPO>
   cd planner_rutas_medellin