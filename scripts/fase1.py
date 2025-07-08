import time

import numpy as np

from model.genetico import Genetico
import csv
import multiprocessing as mp
import os
import datetime

from utils.utils import Utils


# Este script hace un uso intensivo de los recursos del sistema (CPU, RAM y disco),
# debido a la ejecución concurrente de múltiples procesos.
# ⚠️ Tiempo estimado de ejecución: más de 2 horas.
# Asegúrate de tener suficiente capacidad de cómputo disponible antes de iniciar.


seleccion = ["torneo","fitness","rango"]
cruce = ["punto","varios_puntos","uniforme"]
sustitucion = ["reemplazo","elitismo","truncamiento"]

poblacion = 10
generaciones = 4
mutacion_elemento = 0.00009
mutacion_teoria = 0.0005
mutacion_practica = 0.0005
t_torneo = 2


def iteracion(ejecucion_id, seleccion, cruce, sustitucion, t_total, resultados_totales, lock, carpeta):
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
        max_fitness_split = algoritmo_genetico.max_fitness.split(" ")
        resultados_totales.append([
            ejecucion_id,
            f"({seleccion} {cruce} {sustitucion})",
            algoritmo_genetico.max_generacion,
            max_fitness_split[2],
            max_fitness_split[3],
            max_fitness_split[4],
            max_fitness_split[5],
            max_fitness_split[6],
            max_fitness_split[0],
            round(algoritmo_genetico.time, 2)
        ])

def generar_resumenes(carpeta, resultados_totales, total_time):
    encabezado_resumen = [
        "(Seleccion Cruce Sustitucion)", "Generacion", "Solapes", "Cohesion Teoria",
        "Equilibrio", "Cohesion Practicas", "Preferencias", "Fitness", "Tiempo"
    ]

    encabezado_global = [
        "(Seleccion Cruce Sustitucion)", "Generacion(μ)", "Solapes(μ)", "Cohesion Teoria(μ)",
        "Equilibrio(μ)", "Cohesion Practicas(μ)", "Preferencias(μ)", "Fitness(μ)", "Fitness(σ)", "Tiempo(μ)"
    ]

    ejecuciones = {i: [] for i in range(10)}
    for fila in resultados_totales:
        ejecuciones[fila[0]].append(fila)

    tiempos_por_combinacion = {}
    fitness_por_combinacion = {}

    # Resumenes por ejecución
    for i in range(10):
        resumen_path = f"{carpeta}/Ejecucion{i + 1}/resumen.csv"
        with open(resumen_path, mode='w', newline='', encoding='utf-8') as archivo_csv:
            escritor = csv.writer(archivo_csv)
            escritor.writerow(encabezado_resumen)

            resumen_dict = {fila[1]: fila for fila in ejecuciones[i]}
            tiempo_total_ejecucion = 0.0

            for s in seleccion:
                for c in cruce:
                    for st in sustitucion:
                        clave = f"({s} {c} {st})"
                        if clave in resumen_dict:
                            fila = resumen_dict[clave]
                            tiempo_real_seg = float(fila[9])
                            tiempo_total_ejecucion += tiempo_real_seg
                            fila[9] = Utils.str_time(tiempo_real_seg)

                            # Guardar por clave
                            if clave not in tiempos_por_combinacion:
                                tiempos_por_combinacion[clave] = []
                            tiempos_por_combinacion[clave].append(tiempo_real_seg)

                            if clave not in fitness_por_combinacion:
                                fitness_por_combinacion[clave] = []
                            fitness_por_combinacion[clave].append(float(fila[8]))

                            escritor.writerow(fila[1:9] + [fila[9]])

            escritor.writerow(["", "", "", "", "", "", "", "", Utils.str_time(tiempo_total_ejecucion)])

    # Promedios globales
    resumen_promedio = {}
    contador = {}
    for fila in resultados_totales:
        clave = fila[1]
        if clave not in resumen_promedio:
            resumen_promedio[clave] = [0.0] * 7
            contador[clave] = 0

        resumen_promedio[clave][0] += int(fila[2])
        resumen_promedio[clave][1] += int(fila[3])
        for i in range(2, 7):
            resumen_promedio[clave][i] += float(fila[i + 2])
        contador[clave] += 1

    resumen_global = [encabezado_global]

    for s in seleccion:
        for c in cruce:
            for st in sustitucion:
                clave = f"({s} {c} {st})"
                if clave not in resumen_promedio:
                    continue
                suma = resumen_promedio[clave]
                n = contador[clave]

                std_fitness = np.std(fitness_por_combinacion.get(clave, []), ddof=1) if clave in fitness_por_combinacion else 0.0

                fila_media = [
                    clave,
                    str(round(suma[0] / n)),
                    str(round(suma[1] / n)),
                ]
                fila_media += [f"{suma[i] / n:.4f}" for i in range(2, 7)]
                fila_media += [f"{std_fitness:.4f}"]

                if clave in tiempos_por_combinacion:
                    tiempo_medio = sum(tiempos_por_combinacion[clave]) / len(tiempos_por_combinacion[clave])
                    fila_media.append(Utils.str_time(tiempo_medio))
                else:
                    fila_media.append("")

                resumen_global.append(fila_media)

    resumen_global.append(["Tiempo Total", "", "", "", "", "", "", "", "", Utils.str_time(total_time)])

    with open(f"{carpeta}/resumen.csv", mode='w', newline='', encoding='utf-8') as archivo_csv:
        csv.writer(archivo_csv).writerows(resumen_global)

def combinar_archivos_por_combinacion(carpeta):
    for s in seleccion:
        for c in cruce:
            for st in sustitucion:
                nombre_archivo = f"{s}-{c}-{st}.csv"
                combinacion_data = []
                for i in range(10):
                    ruta = os.path.join(carpeta, f"Ejecucion{i + 1}", nombre_archivo)
                    if os.path.exists(ruta):
                        with open(ruta, newline='', encoding='utf-8') as f:
                            lector = list(csv.reader(f))[1:]
                            combinacion_data.append(lector)

                if not combinacion_data:
                    continue

                generaciones = len(combinacion_data[0])
                promedio_por_generacion = []

                for g in range(generaciones):
                    acumulado = [[] for _ in range(9)]
                    for ejecucion in combinacion_data:
                        for j in range(9):
                            valor = ejecucion[g][j + 1]
                            if j == 8:
                                tiempo_segundos = Utils.to_second(valor)
                                acumulado[j].append(tiempo_segundos)
                            else:
                                acumulado[j].append(float(valor))

                    fila_media = [str(g + 1)] + [
                        f"{np.mean(col):.4f}" if j not in [1] else str(round(np.mean(col)))
                        for j, col in enumerate(acumulado[:8])
                    ] + [Utils.str_time(np.mean(acumulado[8]))]
                    fila_media.pop(7)
                    fila_media.pop(6)
                    promedio_por_generacion.append(fila_media)

                with open(os.path.join(carpeta, f"{s}-{c}-{st}-global.csv"), mode='w', newline='', encoding='utf-8') as f:
                    escritor = csv.writer(f)
                    escritor.writerow(["Generacion", "Fitness(μ)", "Solapes(μ)", "Cohesion Teoria(μ)", "Equilibrio(μ)",
                                       "Cohesion Practicas(μ)", "Preferencias(μ)", "Tiempo(μ)"])
                    escritor.writerows(promedio_por_generacion)

if __name__ == '__main__':
    carpeta = f"../{poblacion}-{generaciones}-{mutacion_elemento}-{mutacion_teoria}-{mutacion_practica}-{t_torneo}-{str(datetime.datetime.now())[:19].replace(':', '-') }"
    os.makedirs(carpeta, exist_ok=True)

    manager = mp.Manager()
    t_total = manager.Value('d', 0.0)
    resultados_totales = manager.list()

    lock = manager.Lock()
    pool = mp.Pool(mp.cpu_count())
    async_results = []

    start_time = time.time()

    for i in range(10):
        ncarpeta = f"{carpeta}/Ejecucion{i + 1}"
        os.makedirs(ncarpeta, exist_ok=True)
        for s in seleccion:
            for c in cruce:
                for st in sustitucion:
                    async_results.append(pool.apply_async(
                        iteracion, args=(i, s, c, st, t_total, resultados_totales, lock, ncarpeta)
                    ))

    for result in async_results:
        result.get()

    pool.close()
    pool.join()

    end_time = time.time()
    total_time = end_time - start_time

    generar_resumenes(carpeta, resultados_totales, total_time)
    combinar_archivos_por_combinacion(carpeta)
