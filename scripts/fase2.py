import time

import numpy as np

from model.genetico import Genetico
import csv
import multiprocessing as mp
import os
import datetime

from utils.utils import Utils


# Este script ejecuta una carga computacional muy elevada durante un periodo prolongado.
# ⚠️ Tiempo estimado de ejecución: más de 30 horas.
# Utiliza todos los recursos disponibles del sistema, incluyendo núcleos de CPU y memoria RAM.
# Se recomienda ejecutar en un entorno dedicado o servidor de alto rendimiento.


seleccion = ["torneo"]
cruce = ["uniforme"]
sustitucion = ["reemplazo","elitismo","truncamiento"]

poblacion = [100,300,500]
generaciones = [50,80,100]
mutacion_elemento = [0.00009]
mutacion_teoria = [0.0005,0.005,0.05]
mutacion_practica = [0.0005,0.005,0.05]
t_torneo = [10,20,50]

def iteracion(ejecucion_id, poblacion, generaciones, mutacion_elemento, mutacion_teoria, mutacion_practica, t_torneo, seleccion, cruce, sustitucion, t_total, resultados_totales, lock, carpeta):
    algoritmo_genetico = Genetico(
        poblacion, generaciones, seleccion, cruce, sustitucion,
        mutacion_elemento, mutacion_teoria, mutacion_practica,
        t_torneo, carpeta, True
    )
    solucion = algoritmo_genetico.ejecutar(lambda: False, True)
    resultados = [["Generacion", "Fitness", "Solapes", "Cohesion Teoria", "Equilibrio",
                   "Cohesion Practicas", "Preferencias", "Fitness(μ)", "Fitness(σ)", "Tiempo"]]

    for i, g in enumerate(solucion, 1):
        fitness = [f.fitness for f in g[0]]
        f_max = max(g[0], key=lambda f: f.fitness)
        max_fitness_split = str(f_max).split(" ")
        mean_fitness = np.mean(fitness)
        std_dev = np.sqrt(np.var(fitness, ddof=1))
        time_str = Utils.str_time(g[1])

        resultados.append([
            i,
            f"{f_max.fitness:.4f}",
            max_fitness_split[2],
            max_fitness_split[3],
            max_fitness_split[4],
            max_fitness_split[5],
            max_fitness_split[6],
            f"{mean_fitness:.4f}",
            f"{std_dev:.4f}",
            time_str
        ])

    with open(f"{carpeta}/{seleccion}-{cruce}-{sustitucion}.csv", mode='w', newline='', encoding='utf-8') as archivo_csv:
        csv.writer(archivo_csv).writerows(resultados)

    with lock:
        t_total.value += algoritmo_genetico.time
        fitness_resumen = algoritmo_genetico.max_fitness

        resultados_totales.append([
            ejecucion_id,
            f"{poblacion}-{generaciones}-{mutacion_elemento}-{mutacion_teoria}-{mutacion_practica}-{t_torneo}",
            f"({seleccion} {cruce} {sustitucion})",
            algoritmo_genetico.max_generacion,
            fitness_resumen,
            Utils.str_time(round(algoritmo_genetico.time, 2))
        ])

if __name__ == '__main__':
    carpeta = f"../{str(datetime.datetime.now())[:19].replace(':', '-') }"
    os.makedirs(carpeta, exist_ok=True)

    manager = mp.Manager()
    t_total = manager.Value('d', 0.0)
    resultados_totales = manager.list()

    lock = manager.Lock()
    pool = mp.Pool(mp.cpu_count())
    async_results = []

    start_time = time.time()

    for i in range(5):
        ncarpeta = f"{carpeta}/Ejecucion{i + 1}"
        os.makedirs(ncarpeta, exist_ok=True)
        for p in poblacion:
            for g in generaciones:
                for me in mutacion_elemento:
                    for mt in mutacion_teoria:
                        for mpv in mutacion_practica:
                            for t in t_torneo:
                                for s in seleccion:
                                    for c in cruce:
                                        for st in sustitucion:
                                            supcarpeta = f"{p}-{g}-{me}-{mt}-{mpv}-{t}"
                                            os.makedirs(ncarpeta + "/" + supcarpeta, exist_ok=True)
                                            async_results.append(pool.apply_async(
                                                iteracion, args=(i, p, g, me, mt, mpv, t, s, c, st, t_total, resultados_totales, lock, ncarpeta + "/" + supcarpeta)
                                            ))

    for result in async_results:
        result.get()

    pool.close()
    pool.join()

    end_time = time.time()
    total_time = end_time - start_time

    # Crear resumen.csv por ejecución
    ejecuciones = {}
    for r in resultados_totales:
        ejecucion_id = r[0]
        fila = r[1:]
        if ejecucion_id not in ejecuciones:
            ejecuciones[ejecucion_id] = []
        ejecuciones[ejecucion_id].append(fila)

    for ejecucion_id, filas in ejecuciones.items():
        resumen_path = f"{carpeta}/Ejecucion{ejecucion_id + 1}/resumen.csv"
        filas.sort(key=lambda f: (f[0], f[1]))  # Ordenar por hiperparámetros y métodos

        with open(resumen_path, mode='w', newline='', encoding='utf-8') as resumen_file:
            writer = csv.writer(resumen_file)
            writer.writerow([
                "(Poblacion Generaciones Mutacion Elemento Mutacion Teoria Mutacion Practica Torneo)",
                "(Selección Cruce Sustitucion)",
                "Mejor Generacion",
                "Mejor Fitness",
                "Tiempo"
            ])
            for fila in filas:
                writer.writerow(fila)

    # 2. Crear resumen_total.csv DESPUÉS de que todos los resumen.csv existan
    from collections import defaultdict

    agrupados = defaultdict(list)

    for ejecucion_id in range(len(ejecuciones)):
        resumen_path = f"{carpeta}/Ejecucion{ejecucion_id + 1}/resumen.csv"
        with open(resumen_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                hiperparametros = row[0]
                metodos = row[1]
                mejor_gen = int(row[2])
                fitness_str = row[3]
                tiempo_segundos = Utils.to_second(row[4])

                main_fit = float(fitness_str.split(" ")[0])
                objetivos = fitness_str.split("(")[1].replace(")", "").split()
                objetivos = list(map(float, objetivos))

                agrupados[(hiperparametros, metodos)].append((mejor_gen, main_fit, *objetivos, tiempo_segundos))

    resumen_total_path = f"{carpeta}/resumen.csv"
    with open(resumen_total_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "(Hiperparametros)",
            "(Selección Cruce Sustitucion)",
            "Mejor Generacion(μ)",
            "Mejor Fitness(μ)",
            "Fitness(σ)",
            "Tiempo(μ)"
        ])
        for (hparams, methods), valores in sorted(agrupados.items()):
            gens = [v[0] for v in valores]
            fits = [v[1] for v in valores]
            solapes = [v[2] for v in valores]
            cohesion_teoria = [v[3] for v in valores]
            equilibrio = [v[4] for v in valores]
            cohesion_practicas = [v[5] for v in valores]
            preferencias = [v[6] for v in valores]
            tiempos = [v[7] for v in valores]

            media_fitness = np.mean(fits)
            resumen_fitness = f"{media_fitness:.4f} ({round(np.mean(solapes))} {np.mean(cohesion_teoria):.4f} {np.mean(equilibrio):.4f} {np.mean(cohesion_practicas):.4f} {np.mean(preferencias):.4f})"

            writer.writerow([
                hparams,
                methods,
                f"{round(np.mean(gens))}",
                resumen_fitness,
                f"{np.std(fits, ddof=1):.4f}" if len(fits) > 1 else "0.0000",
                Utils.str_time(np.mean(tiempos))
            ])

        writer.writerow(["Tiempo Total", "", "", "", "", Utils.str_time(total_time)])
