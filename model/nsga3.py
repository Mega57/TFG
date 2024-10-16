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
from math import comb
from utils.utils import Cruce, Utils, Mutar


class NSGA3:

    def __init__(self, tamaño_poblacion, generaciones, cruce, p_mutacion_alumno, p_mutacion_teoria, p_mutacion_practica, tamaño_torneo, particiones, debug):
        self.tamaño_poblacion = tamaño_poblacion
        self.generaciones = generaciones
        self.metodo_cruce = cruce
        self.p_mutacion_alumno = p_mutacion_alumno
        self.p_mutacion_teoria = p_mutacion_teoria
        self.p_mutacion_practica = p_mutacion_practica
        self.tamaño_torneo = tamaño_torneo
        self.debug = debug
        self.particiones = particiones

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

    def ejecutar(self):
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)

        horariosPath = "docs/horarios.xlsx"
        matriculasPath = "docs/matriculas.xlsx"
        asignaturasPath = "docs/asignaturas.xlsx"

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
                if fila['CODIGO'] in asignaturasObligatorias and fila['CODIGO'] != 42325:
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
        for i in range(self.tamaño_poblacion):
            individuo = copy.deepcopy(listaAlumnos)
            for a in individuo:
                grupos_curso = defaultdict(int)
                for asignatura in a.matriculas_variables:
                    asignatura.grupo_practicas = random.choice([1, 2])
                    if grupos_curso[asignatura.curso] != 0:
                        asignatura.grupo = grupos_curso[asignatura.curso]
                    else:
                        asignatura.grupo = random.choice([10, 11, 12]) if asignatura.curso == 1 else random.choice(
                            [10, 11])
                        grupos_curso[asignatura.curso] = asignatura.grupo

                    asignatura.horario_teoria = horarios_teoria[asignatura.cod_asignatura][asignatura.grupo]
                    asignatura.horario_practicas = horarios_practica[asignatura.cod_asignatura][asignatura.grupo][
                        asignatura.grupo_practicas]
            poblacionInicial.append(solucion(individuo, listaAlumnos))

        '''Creamos otra poblacion inicial a partir de la primera para que a la hora de elegir elementos en la nueva generacion tengamos mas elementos'''
        padresPt = []
        for i in range(int(self.tamaño_poblacion/2)):
            padre1 = random.choice(poblacionInicial)
            padre2 = random.choice(poblacionInicial)
            while padre1 == padre2:
                padre2 = random.choice(poblacionInicial)
            padresPt.extend([(padre1, padre2)])

        pt = self.__cruce(padresPt, listaAlumnos)
        for individuo in pt:
            for i in range(len(individuo.alumnos)):
                if random.random() < 0.5:
                    individuo.alumnos[i] = Mutar.mutar(individuo.alumnos[i], self.p_mutacion_teoria, self.p_mutacion_practica, horarios_teoria, horarios_practica)
        poblacionInicial.extend(pt)

        pr = self.generar_puntos_referencia(5,self.particiones)

        tiempo_total = 0
        '''Algoritmo genético'''
        for generacion in range(self.generaciones):
            start_time = time.time()
            clasificacion_soluciones = defaultdict(lambda: [[], 0])
            frentes_pareto = defaultdict(list)
            rango_solucion = defaultdict(lambda: [0, [0,0.0]])
            soluciones_por_punto_frente = defaultdict(lambda: defaultdict(list))
            soluciones_por_punto = defaultdict(int)
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
            while sum(len(lista) for lista in frentes_pareto.values()) != len(poblacionInicial):
                claves_con_x = [clave for clave, valor in clasificacion_soluciones.items() if valor[1] == 0]
                frentes_pareto[frente] = copy.deepcopy(claves_con_x)
                for clave in claves_con_x:
                    punto_cercano, distancia = self.calculo_distancia(poblacionInicial[clave],pr)
                    rango_solucion[clave] = [frente, [punto_cercano,distancia]]
                    soluciones_por_punto_frente[frente][punto_cercano].append(clave)
                    #soluciones_por_punto[punto_cercano]+=1
                    for dominado in clasificacion_soluciones[clave][0]:
                        clasificacion_soluciones[dominado][1]-=1
                    del clasificacion_soluciones[clave]
                frente+=1
            nueva_generacion = []
            print("Generacion: " +str(generacion+1))
            print("Elementos frente 0: " +str(len(frentes_pareto[0])))
            for sol in frentes_pareto[0]:
                print(poblacionInicial[sol])
            print("------------------------------------------------------------------------------------------------------")
            for frente in frentes_pareto.keys():
                #print(soluciones_por_punto[frente])
                if len(nueva_generacion) != self.tamaño_poblacion:
                    if len(nueva_generacion) + len(frentes_pareto[frente]) <= self.tamaño_poblacion:
                        nueva_generacion.extend([poblacionInicial[x] for x in frentes_pareto[frente]])
                        for sol in frentes_pareto[frente]:
                            soluciones_por_punto[rango_solucion[sol][1][0]]+=1
                    else:
                        ordenado_por_valor = sorted(soluciones_por_punto, key=lambda k: soluciones_por_punto[k])
                        ordenado_por_valor_frente = sorted(soluciones_por_punto_frente[frente], key=lambda k: len(soluciones_por_punto_frente[frente][k]))
                        for _ in range(self.tamaño_poblacion - len(nueva_generacion)):
                            ordenado_por_valor = sorted(soluciones_por_punto, key=lambda k: soluciones_por_punto[k])
                            for sol in ordenado_por_valor:
                                if sol == 0 and len(soluciones_por_punto_frente[frente][sol]) == 0:
                                    ordenado_por_valor.remove(sol)
                                if len(soluciones_por_punto_frente[frente][sol]) != 0:
                                    distancias = [rango_solucion[dis][1][1] for dis in soluciones_por_punto_frente[frente][sol]]
                                    ordenado_por_distancia = [x for _, x in sorted(zip(distancias, soluciones_por_punto_frente[frente][sol]))]
                                    soluciones_por_punto[rango_solucion[ordenado_por_distancia[0]][1][1]]+=1
                                    nueva_generacion.append(poblacionInicial[ordenado_por_distancia[0]])



                        '''for i in ordenado_por_valor:
                            if len(nueva_generacion) + len(soluciones_por_punto_frente[frente][i]) <= self.tamaño_poblacion:
                                nueva_generacion.extend([poblacionInicial[x] for x in soluciones_por_punto_frente[frente][i]])
                            else:
                                menor_distancia = sorted(soluciones_por_punto_frente[frente][i], key=lambda k: rango_solucion[k][1][1])
                                for x in menor_distancia:
                                    if len(nueva_generacion)+1 <= self.tamaño_poblacion:
                                        nueva_generacion.append(poblacionInicial[x])
                                    else:
                                        break
                            if len(nueva_generacion) == self.tamaño_poblacion:
                                break'''
            padres = []
            for i in range(int(self.tamaño_poblacion/2)):
                padre11, padre12 = random.sample(range(self.tamaño_poblacion), 2)
                if (rango_solucion[padre11][0], rango_solucion[padre11][1]) <= (
                rango_solucion[padre12][0], rango_solucion[padre12][1]):
                    padre1 = padre11
                else:
                    padre1 = padre12
                padre21, padre22 = random.sample(range(self.tamaño_poblacion), 2)
                if (rango_solucion[padre21][0], rango_solucion[padre21][1]) <= (
                        rango_solucion[padre22][0], rango_solucion[padre22][1]):
                    padre2 = padre21
                else:
                    padre2 = padre22
                padres.extend([(poblacionInicial[padre1],poblacionInicial[padre2])])
            pt = self.__cruce(padres, listaAlumnos)
            for individuo in pt:
                for i in range(len(individuo.alumnos)):
                    if random.random() < self.p_mutacion_alumno:
                        individuo.alumnos[i] = Mutar.mutar(individuo.alumnos[i], self.p_mutacion_teoria, self.p_mutacion_practica,horarios_teoria,horarios_practica)
            nueva_generacion.extend(pt)
            if generacion != self.generaciones - 1:
                poblacionInicial = copy.deepcopy(nueva_generacion)
            end_time = time.time()
            iteration_time = end_time - start_time
            tiempo_total += iteration_time
            print(f"Tiempo de la Generación {generacion + 1}: " + Utils.str_time(iteration_time))
        print(f"Tiempo Total: " + Utils.str_time(tiempo_total))
        print("Resultado final")
        print(len(frentes_pareto[0]))
        for x in frentes_pareto[0]:
            print(poblacionInicial[x])

        '''for frente in frentes_pareto.keys():
            print(f"Frente {frente+1}\n")
            for s in frentes_pareto[frente]:
                print(poblacionInicial[s])
            print("------------------------------------------------------------------------------")





            end_time = time.time()
            iteration_time = end_time - start_time
            tiempo_total += iteration_time
            if self.debug:
                print(f"Tiempo de la Generación {generacion + 1}: " + Utils.str_time(iteration_time))
                salida.append(f"Tiempo de la Generación {generacion + 1}: " + Utils.str_time(iteration_time))'''

        '''print(f"Tiempo Total: " + Utils.str_time(tiempo_total))
        salida.append(f"Tiempo Total: " + Utils.str_time(tiempo_total))'''

        '''with open("results/salida.txt", "w") as archivo:
            for linea in salida:
                archivo.write(linea)'''

    def calculo_distancia(self,sol,puntos_referencia):
        puntos = []
        for i, punto in enumerate(puntos_referencia):
            globals()[f'punto{i + 1}'] = punto  # Crea punto1, punto2, etc.
            puntos.append(globals()[f'punto{i + 1}'])
        #punto = np.array([sol.solapes/479, sol.tasa_cohesion, sol.d_total, sol.tasa_practicas_pronto, sol.tasa_cohesion_practicas,sol.tasa_preferencias])
        punto = np.array([sol.solapes / 479, sol.tasa_cohesion, sol.d_total, sol.tasa_practicas_pronto, sol.tasa_preferencias])
        puntos = np.array(puntos)
        distancias = np.linalg.norm(puntos - punto, axis=1)
        indice_cercano = np.argmin(distancias)
        distancia = float(distancias[indice_cercano])
        return indice_cercano, distancia

    def generar_puntos_referencia(self, M, p):
        from math import comb
        combinaciones = list(itertools.combinations_with_replacement(range(p + 1), M))
        puntos_referencia = np.array([list(comb) for comb in combinaciones]) / p
        for punto in puntos_referencia:
            punto[0] = 1 - punto[0]
        return puntos_referencia.tolist()