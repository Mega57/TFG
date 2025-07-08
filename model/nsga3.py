import copy
import itertools
import time
import random
from collections import defaultdict
import numpy as np
import pandas as pd

from model.alumno import alumno
from model.matricula import matricula
from model.solucion import solucion
from utils.export import Export
from utils.utils import Cruce, Utils, Mutar


class NSGA3:

    def __init__(self, tamaño_poblacion, generaciones, cruce, p_mutacion_alumno, p_mutacion_teoria, p_mutacion_practica, tamaño_torneo, particiones, carpeta, debug):
        self.tamaño_poblacion = tamaño_poblacion
        self.generaciones = generaciones
        self.metodo_cruce = cruce
        self.p_mutacion_alumno = p_mutacion_alumno
        self.p_mutacion_teoria = p_mutacion_teoria
        self.p_mutacion_practica = p_mutacion_practica
        self.tamaño_torneo = tamaño_torneo
        self.debug = debug
        self.particiones = particiones
        self.time = ""
        self.carpeta = carpeta

    def __cruce(self, padres, listaAlumnos):

        if self.metodo_cruce == 'punto':
            return Cruce.cruce_punto(padres, listaAlumnos)
        elif self.metodo_cruce == 'varios_puntos':
            return Cruce.cruce_varios_puntos(padres, listaAlumnos)
        elif self.metodo_cruce == 'uniforme':
            return Cruce.cruce_uniforme(padres, listaAlumnos)
        elif self.metodo_cruce == 'matricula':
            return Cruce.cruce_matriculas(padres, listaAlumnos)
        else:
            raise ValueError(f"Método de cruce {self.metodo_cruce} no soportado.")

    def ejecutar(self, execution_cancelled, script, horariosPath = "../docs/horarios.xlsx", matriculasPath = "../docs/matriculas.xlsx"):
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)

        horariosPath = horariosPath
        matriculasPath = matriculasPath
        asignaturasPath = "../docs/asignaturas.xlsx" if script else "docs/asignaturas.xlsx"

        horarios = pd.read_excel(horariosPath)
        matriculas = pd.read_excel(matriculasPath)
        asignaturas = pd.read_excel(asignaturasPath)

        '''Lo primero es obtener una lista con los codigos de las asignaturas que son obligatorias y por ende tendrán más de un grupo'''
        asignaturasObligatorias = list(asignaturas[(asignaturas['TECNOLOGÍA'] == 'OB')]['COD. ASIG'])

        # Poblacion inicial que sera una lista de objetos del tipo alumno
        listaAlumnos = list()
        poblacionInicial = []
        horarios_teoria, horarios_practica = Utils.import_horarios(horarios)
        salida = []

        for alu in matriculas['ALUMNO'].unique():
            matriculas_variables = list()
            matriculas_fijas = list()
            grupo_primero = random.choice([10, 11, 12])
            for indice, fila in matriculas.loc[matriculas['ALUMNO'] == alu].iterrows():

                g = fila["GRUPO"]
                horario_teoria = horarios_teoria[fila["CODIGO"]][fila["GRUPO"]]
                horario_practica = horarios_practica[fila["CODIGO"]][fila["GRUPO"]][1]

                if asignaturas[(asignaturas['COD. ASIG'] == fila["CODIGO"])].iloc[0]["CURSO"] == 1:
                    g = grupo_primero
                    horario_teoria = horarios_teoria[fila["CODIGO"]][grupo_primero]
                    horario_practica = horarios_practica[fila["CODIGO"]][grupo_primero][1]

                m = matricula(fila['ASIGNATURA'], fila['CODIGO'],
                              asignaturas[(asignaturas['COD. ASIG'] == fila["CODIGO"])].iloc[0]["CURSO"], g,
                              horario_teoria, fila['GP'], horario_practica,
                              asignaturas[(asignaturas['COD. ASIG'] == fila["CODIGO"])].iloc[0]["CUATRIMESTRE"])
                if fila['CODIGO'] in asignaturasObligatorias:
                    matriculas_variables.append(m)
                else:
                    matriculas_fijas.append(m)
            listaAlumnos.append(alumno(alu, matriculas_variables, matriculas_fijas))

        configuracion_inicial = solucion(listaAlumnos, listaAlumnos)
        fitness_inicial = configuracion_inicial.calcular_fitness()
        if self.debug:
            print("Configuracion inicial")
            print(f"{fitness_inicial:.4f}" + " " + str(configuracion_inicial) + "\n")
            salida.append("Configuracion inicial")
            salida.append(f"{fitness_inicial:.4f}" + " " + str(configuracion_inicial) + "\n")

        '''Preparamos poblacion inicial'''
        for i in range(self.tamaño_poblacion*2):
            individuo = copy.deepcopy(listaAlumnos)
            for a in individuo:
                grupos_curso = defaultdict(int)
                for asignatura in a.matriculas_variables:
                    asignatura.grupo_practicas = random.choice([1, 2])
                    if grupos_curso[asignatura.curso] != 0:
                        asignatura.grupo = grupos_curso[asignatura.curso]
                    else:
                        asignatura.grupo = random.choice([10, 11, 12]) if asignatura.curso == 1 else random.choice([10, 11])
                        grupos_curso[asignatura.curso] = asignatura.grupo
                    if asignatura.cod_asignatura == 42325:
                        asignatura.grupo = random.choice([10,11,12])

                    asignatura.horario_teoria = horarios_teoria[asignatura.cod_asignatura][asignatura.grupo]
                    asignatura.horario_practicas = horarios_practica[asignatura.cod_asignatura][asignatura.grupo][
                        asignatura.grupo_practicas]
            poblacionInicial.append(solucion(individuo, listaAlumnos))

        pr = self.generar_puntos_referencia(self.particiones)

        tiempo_total = 0
        response = []
        '''Algoritmo NSGA-III'''
        for generacion in range(self.generaciones):
            if execution_cancelled():
                print("CANCELADO")
                return None
            start_time = time.time()
            clasificacion_soluciones = defaultdict(lambda: [[], 0])
            frentes_pareto = defaultdict(list)
            rango_solucion = defaultdict(lambda: [0, [0,0.0]])
            soluciones_por_punto_frente = defaultdict(lambda: defaultdict(list))
            soluciones_por_punto = defaultdict(int)
            for i in range(len(pr)):
                soluciones_por_punto[i] = 0
            for elemento in poblacionInicial:
                elemento.evaluar_solucion()
            n = len(poblacionInicial)
            for i in range(n):
                _ = clasificacion_soluciones[i]
                for j in range(i + 1, n):
                    _ = clasificacion_soluciones[j]
                    i_domina_j = poblacionInicial[i].domina(poblacionInicial[j])
                    j_domina_i = poblacionInicial[j].domina(poblacionInicial[i])
                    if i_domina_j:
                        clasificacion_soluciones[i][0].append(j)
                        clasificacion_soluciones[j][1]+=1
                    elif j_domina_i:
                        clasificacion_soluciones[j][0].append(i)
                        clasificacion_soluciones[i][1] += 1
            frente = 0
            poblacionInicialNormalizada = self.normalizar_poblacion_para_distancia(poblacionInicial)
            while sum(len(lista) for lista in frentes_pareto.values()) != len(poblacionInicial):
                claves_con_x = [clave for clave, valor in clasificacion_soluciones.items() if valor[1] == 0]
                frentes_pareto[frente] = copy.deepcopy(claves_con_x)
                for clave in claves_con_x:
                    punto_cercano, distancia = self.calculo_distancia(poblacionInicialNormalizada[clave],pr)
                    rango_solucion[clave] = [frente, [punto_cercano,distancia]]
                    soluciones_por_punto_frente[frente][punto_cercano].append(clave)
                    for dominado in clasificacion_soluciones[clave][0]:
                        clasificacion_soluciones[dominado][1]-=1
                    del clasificacion_soluciones[clave]
                frente+=1
            nueva_generacion = []
            for frente in frentes_pareto.keys():
                if len(nueva_generacion) != self.tamaño_poblacion:
                    if len(nueva_generacion) + len(frentes_pareto[frente]) <= self.tamaño_poblacion:
                        nueva_generacion.extend([poblacionInicial[x] for x in frentes_pareto[frente]])
                        for sol in frentes_pareto[frente]:
                            soluciones_por_punto[rango_solucion[sol][1][0]]+=1
                    else:
                        for _ in range(self.tamaño_poblacion - len(nueva_generacion)):
                            ordenado_por_valor = sorted(soluciones_por_punto, key=lambda k: soluciones_por_punto[k])
                            for sol in ordenado_por_valor:
                                if len(soluciones_por_punto_frente[frente][sol]) != 0:
                                    distancias = [rango_solucion[dis][1][1] for dis in soluciones_por_punto_frente[frente][sol]]
                                    ordenado_por_distancia = [x for _, x in sorted(
                                    zip(distancias, soluciones_por_punto_frente[frente][sol]))]
                                    soluciones_por_punto[rango_solucion[ordenado_por_distancia[0]][1][1]] += 1
                                    nueva_generacion.append(poblacionInicial[ordenado_por_distancia[0]])
                                    soluciones_por_punto_frente[frente][sol].remove(ordenado_por_distancia[0])
                                    break
                        break

            padres = []
            for i in range(int(self.tamaño_poblacion/2)):
                n_tamaño_poblacion = self.tamaño_poblacion if self.tamaño_poblacion % 2 == 0 else self.tamaño_poblacion - 1
                padres1 = random.sample(range(n_tamaño_poblacion), self.tamaño_torneo)
                l_padres1 = [(rango_solucion[p][0],rango_solucion[p][1][1]) for p in padres1]
                padres1_sorted = sorted(zip(l_padres1, padres1), key=lambda x: x[0])
                padre1 = padres1_sorted[0][1]

                padres2 = random.sample(range(n_tamaño_poblacion), self.tamaño_torneo)
                l_padres2 = [(rango_solucion[p][0], rango_solucion[p][1][1]) for p in padres2]
                padres2_sorted = sorted(zip(l_padres2, padres2), key=lambda x: x[0])
                padre2 = padres2_sorted[0][1]

                if padre1 == padre2 and self.tamaño_torneo != 1:
                    padre2 = padres2_sorted[1][1]

                padres.extend([(poblacionInicial[padre1],poblacionInicial[padre2])])
            pt = self.__cruce(padres, listaAlumnos)
            for individuo in pt:
                for i in range(len(individuo.alumnos)):
                    if random.random() < self.p_mutacion_alumno:
                        individuo.alumnos[i] = Mutar.mutar(individuo.alumnos[i], self.p_mutacion_teoria, self.p_mutacion_practica,horarios_teoria,horarios_practica)
            nueva_generacion = copy.deepcopy(pt)
            poblacionInicial = copy.deepcopy(nueva_generacion)
            clasificacion_soluciones = defaultdict(lambda: [[], 0])
            frentes_pareto = defaultdict(list)
            rango_solucion = defaultdict(lambda: [0, [0, 0.0]])
            soluciones_por_punto_frente = defaultdict(lambda: defaultdict(list))
            soluciones_por_punto = defaultdict(int)
            for i in range(len(pr)):
                soluciones_por_punto[i] = 0
            for elemento in poblacionInicial:
                elemento.evaluar_solucion()
            n = len(poblacionInicial)
            for i in range(n):
                _ = clasificacion_soluciones[i]
                for j in range(i + 1, n):
                    _ = clasificacion_soluciones[j]
                    i_domina_j = poblacionInicial[i].domina(poblacionInicial[j])
                    j_domina_i = poblacionInicial[j].domina(poblacionInicial[i])
                    if i_domina_j:
                        clasificacion_soluciones[i][0].append(j)
                        clasificacion_soluciones[j][1] += 1
                    elif j_domina_i:
                        clasificacion_soluciones[j][0].append(i)
                        clasificacion_soluciones[i][1] += 1
            frente = 0
            poblacionInicialNormalizada = self.normalizar_poblacion_para_distancia(poblacionInicial)
            while sum(len(lista) for lista in frentes_pareto.values()) != len(poblacionInicial):
                claves_con_x = [clave for clave, valor in clasificacion_soluciones.items() if valor[1] == 0]
                frentes_pareto[frente] = copy.deepcopy(claves_con_x)
                for clave in claves_con_x:
                    punto_cercano, distancia = self.calculo_distancia(poblacionInicialNormalizada[clave], pr)
                    rango_solucion[clave] = [frente, [punto_cercano, distancia]]
                    soluciones_por_punto_frente[frente][punto_cercano].append(clave)
                    for dominado in clasificacion_soluciones[clave][0]:
                        clasificacion_soluciones[dominado][1] -= 1
                    del clasificacion_soluciones[clave]
                frente += 1
            print("Generacion: " + str(generacion + 1))
            print("Elementos frente 0: " + str(len(frentes_pareto[0])))
            sl = set()
            i = 1
            for sol in frentes_pareto[0]:
                sl.add(poblacionInicial[sol])
                print(poblacionInicial[sol])
                if generacion == self.generaciones - 1:
                    Export.matriculas(poblacionInicial[sol].alumnos, str(poblacionInicial[sol]), "", "",
                                      self.carpeta, script,True, poblacionInicial[sol], i)
                    Export.alumnos_clase(configuracion_inicial.estudiantes_asignatura,
                                         poblacionInicial[sol].estudiantes_asignatura, asignaturas,
                                         str(poblacionInicial[sol]), "", "", self.carpeta, script,True, poblacionInicial[sol],i)
                    i += 1
            if len(response) != 0:
                if response[-1][0] == list(sl):
                    i=1
                    for sol in list(sl):
                        Export.matriculas(sol.alumnos, str(sol), "", "",
                                          self.carpeta, script, True, sol,i)
                        Export.alumnos_clase(configuracion_inicial.estudiantes_asignatura,
                                             sol.estudiantes_asignatura, asignaturas,
                                             str(sol), "", "", self.carpeta, script,True, sol,i)
                        i+=1
                    break
            elementResponse = [list(sl)]
            print(
                "------------------------------------------------------------------------------------------------------")
            if generacion != self.generaciones - 1:
                padresPt = []
                for i in range(int(self.tamaño_poblacion / 2)):
                    n_tamaño_poblacion = self.tamaño_poblacion if self.tamaño_poblacion%2 == 0 else self.tamaño_poblacion-1
                    padres1 = random.sample(range(n_tamaño_poblacion), self.tamaño_torneo)
                    l_padres1 = [(rango_solucion[p][0], rango_solucion[p][1][1]) for p in padres1]
                    padres1_sorted = sorted(zip(l_padres1, padres1), key=lambda x: x[0])
                    padre1 = padres1_sorted[0][1]

                    padres2 = random.sample(range(n_tamaño_poblacion), self.tamaño_torneo)
                    l_padres2 = [(rango_solucion[p][0], rango_solucion[p][1][1]) for p in padres2]
                    padres2_sorted = sorted(zip(l_padres2, padres2), key=lambda x: x[0])
                    padre2 = padres2_sorted[0][1]

                    if padre1 == padre2 and self.tamaño_torneo != 1:
                        padre2 = padres2_sorted[1][1]
                    padresPt.extend([(poblacionInicial[padre1], poblacionInicial[padre2])])

                pt = self.__cruce(padresPt, listaAlumnos)
                for individuo in pt:
                    for i in range(len(individuo.alumnos)):
                        if random.random() < self.p_mutacion_alumno:
                            individuo.alumnos[i] = Mutar.mutar(individuo.alumnos[i], self.p_mutacion_teoria,
                                                               self.p_mutacion_practica, horarios_teoria,
                                                               horarios_practica)
                poblacionInicial.extend(pt)
            end_time = time.time()
            iteration_time = end_time - start_time
            elementResponse.append(iteration_time)
            response.append(elementResponse)
            tiempo_total += iteration_time
            print(f"Tiempo de la Generación {generacion + 1}: " + Utils.str_time(iteration_time))
        print(f"Tiempo Total: " + Utils.str_time(tiempo_total))
        self.time = tiempo_total
        return response

    def calculo_distancia(self,sol,puntos_referencia):
        punto = np.array([
            sol[0],
            sol[1],
            sol[2],
            sol[3],
            sol[4]
        ])

        distancias = []
        for ref in puntos_referencia:
            r = np.array(ref)
            numerador = np.dot(punto, r)
            denominador = np.dot(r, r) + 1e-10  # Para evitar división por cero
            proyeccion = (numerador / denominador) * r
            distancia_perp = np.linalg.norm(punto - proyeccion)
            distancias.append(distancia_perp)

        distancias = np.array(distancias)
        indice_cercano = np.argmin(distancias)
        distancia = float(distancias[indice_cercano])
        return indice_cercano, distancia

    def normalizar_poblacion_para_distancia(self, poblacion):
        objetivos_raw = np.array([
            [
                round(sol.solapes / 479, 4),
                1 - sol.tasa_cohesion,
                sol.d_total,
                1 - sol.tasa_cohesion_practicas,
                1 - sol.tasa_preferencias
            ] for sol in poblacion
        ])
        z_min = np.min(objetivos_raw, axis=0)
        z_max = np.max(objetivos_raw, axis=0)
        normalizados = (objetivos_raw - z_min) / (z_max - z_min + 1e-10)
        return normalizados

    def generar_puntos_referencia(self, H, M = 5):
        points = []
        # Combinaciones enteras que suman H en M componentes
        for bars in itertools.combinations(range(H + M - 1), M - 1):
            bars = (-1,) + bars + (H + M - 1,)
            composition = [bars[i + 1] - bars[i] - 1 for i in range(M)]
            point = tuple(h / H for h in composition)
            points.append(point)
        return points
