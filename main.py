import time

import numpy as np

from model.genetico import Genetico
import csv
import multiprocessing as mp
import os
import datetime

from utils.utils import Utils

seleccion = ["torneo","fitness","rango"]
cruce = ["punto","varios_puntos","uniforme"]
sustitucion = ["reemplazo","elitismo","truncamiento"]

'''poblacion = 200
generaciones = 50
mutacion_elemento = 0.0005
mutacion_teoria = 0.005
mutacion_practica = 0.005
t_torneo = int(poblacion/40)'''

poblacion = 500
generaciones = 50
mutacion_elemento = 0.00009
mutacion_teoria = 0.0005
mutacion_practica = 0.0005
t_torneo = 10


def iteracion(seleccion, cruce, sustitucion, t_total, resultados_totales, lock, carpeta):
    algoritmo_genetico = Genetico(poblacion, generaciones, seleccion, cruce, sustitucion, mutacion_elemento, mutacion_teoria, mutacion_practica, t_torneo, carpeta, True)
    with lock:
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
    solucion = algoritmo_genetico.ejecutar()
    resultados = []
    resultados.append(
        ["Generacion", "Mejor_Fitness", "Promedio_Fitness", "Peor_Fitness", "Desviacion_Estandar", "Tiempo_Generacion"])
    i = 1
    for g in solucion:
        fitness = [f.fitness for f in g[0]]
        f_max = max(g[0], key=lambda f: f.fitness)
        max_fitness = f_max.fitness
        f_mix = min(g[0], key=lambda f: f.fitness)
        min_fitness = f_mix.fitness
        mean_fitness = np.mean(fitness)
        standard_desviation = np.sqrt(np.var(fitness, ddof=1))
        time = g[1]
        resultados.append(
            [i, f"{max_fitness:.4f}" + str(f_max), f"{mean_fitness:.4f}", f"{min_fitness:.4f}" + str(f_mix),
             f"{standard_desviation:.4f}", Utils.str_time(time)])
        i += 1
    with open(carpeta + f"/{seleccion}-{cruce}-{sustitucion}.csv", mode='w', newline='') as archivo_csv:
        escritor_csv = csv.writer(archivo_csv)
        escritor_csv.writerows(resultados)
    with lock:
        t_total.value+=algoritmo_genetico.time
        if len(resultados_totales) != 1:
            resultados_totales.pop(-1)
        resultados_totales.append([f"({seleccion}, {cruce}, {sustitucion})", algoritmo_genetico.max_generacion, algoritmo_genetico.max_fitness,Utils.str_time(algoritmo_genetico.time)])
        resultados_totales.append(["", "", "", Utils.str_time(t_total.value)])
        with open(carpeta+'/resumen.csv', mode='w', newline='') as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)
            # Escribir todas las filas en el archivo
            escritor_csv.writerows(resultados_totales)



if __name__ == '__main__':
    carpeta = f"{poblacion}-{generaciones}-{mutacion_elemento}-{mutacion_teoria}-{mutacion_practica}-{t_torneo}-{str(datetime.datetime.now())[:19].replace(':', '-')}"
    manager = mp.Manager()
    t_total = manager.Value('d', 0.0)
    resultados_totales = manager.list()
    resultados_totales.append(["(Selección,Cruce,Sustitucion)", "Mejor Generación", "Mejor Fitness", "Tiempo Total"])
    lock = manager.Lock()
    pool = mp.Pool(mp.cpu_count())
    async_results = []
    start_time = time.time()

    for s in seleccion:
        for c in cruce:
            for st in sustitucion:
                async_results.append(pool.apply_async(iteracion, args=(s, c, st, t_total, resultados_totales, lock, carpeta)))

    for result in async_results:
        result.get()

    pool.close()
    pool.join()

    end_time = time.time()

    total_time = end_time - start_time

    resultados_totales.append(["", "", "", Utils.str_time(total_time)])
    with open(carpeta+ '/resumen.csv', mode='w', newline='') as archivo_csv:
        escritor_csv = csv.writer(archivo_csv)
        escritor_csv.writerows(resultados_totales)