import copy
import random
import time

import pandas as pd
from model.alumno import alumno
from model.matricula import matricula
from model.solucion import solucion
from collections import defaultdict
from utils.utils import Seleccion
from utils.utils import Cruce
from utils.utils import Sustitucion
from utils.utils import Utils
from utils.utils import Mutar
from utils.export import Export
class Genetico:

    def __init__(self, tamaño_poblacion, generaciones, seleccion, cruce, sustitucion, p_mutacion_alumno, p_mutacion_teoria, p_mutacion_practica, tamaño_torneo, carpeta, debug):
        self.tamaño_poblacion = tamaño_poblacion
        self.generaciones = generaciones
        self.metodo_seleccion = seleccion
        self.metodo_cruce = cruce
        self.metodo_sustitucion = sustitucion
        self.p_mutacion_alumno = p_mutacion_alumno
        self.p_mutacion_teoria = p_mutacion_teoria
        self.p_mutacion_practica = p_mutacion_practica
        self.tamaño_torneo = tamaño_torneo
        self.debug = debug
        self.max_generacion = 0
        self.max_fitness = ""
        self.time = ""
        self.carpeta = carpeta


    def __seleccion(self,poblacion,fitness):

        if self.metodo_seleccion == 'fitness':
            return Seleccion.seleccion_fitness(poblacion, fitness)
        elif self.metodo_seleccion == 'rango':
            return Seleccion.seleccion_rango(poblacion, fitness)
        elif self.metodo_seleccion == 'torneo':
            k = self.tamaño_torneo if self.tamaño_torneo > 0 else int(len(poblacion)/2)
            return Seleccion.seleccion_torneo(poblacion, fitness, k)
        else:
            raise ValueError(f"Método de selección {self.metodo_seleccion} no soportado.")

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

    def __sustitucion(self, poblacionInicial, nueva_generacion, fitness):

        if self.metodo_sustitucion == 'reemplazo':
            return Sustitucion.reemplazo(nueva_generacion)
        elif self.metodo_sustitucion == 'elitismo':
            return Sustitucion.elitismo(poblacionInicial,nueva_generacion,fitness)
        elif self.metodo_sustitucion == 'truncamiento':
            return Sustitucion.truncamiento(poblacionInicial,nueva_generacion,fitness)
        else:
            raise ValueError(f"Método de sustitucion {self.metodo_sustitucion} no soportado.")


    def ejecutar(self, execution_cancelled, script, horariosPath = "../docs/horarios.xlsx", matriculasPath = "../docs/matriculas.xlsx"):
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)

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
                    if asignatura.cod_asignatura == 42325:
                        asignatura.grupo = random.choice([10, 11, 12])

                    asignatura.horario_teoria = horarios_teoria[asignatura.cod_asignatura][asignatura.grupo]
                    asignatura.horario_practicas = horarios_practica[asignatura.cod_asignatura][asignatura.grupo][
                        asignatura.grupo_practicas]
            poblacionInicial.append(solucion(individuo, listaAlumnos))

        max_fitness = float('-inf')
        max_solucion = None
        max_generacion = 0
        tiempo_total = 0
        response = []
        '''Algoritmo genético'''
        for generacion in range(self.generaciones):
            if execution_cancelled():
                print("CANCELADO")
                return None
            start_time = time.time()
            fitness = {i: poblacionInicial[i].calcular_fitness() for i in range(len(poblacionInicial))}
            max_i = max(fitness, key=fitness.get)
            if fitness[max_i] > max_fitness:
                self.max_generacion = generacion + 1

                max_fitness = fitness[max_i]
                max_generacion = generacion + 1
                max_solucion = copy.deepcopy(poblacionInicial[max_i])
                self.max_fitness = f"{fitness[max_i]:.4f}" + str(max_solucion)
            if self.debug:
                Utils.print_solucion(poblacionInicial, fitness, generacion + 1)
                print("Mejor Generacion: " + str(max_generacion))
                print(
                    f"{self.generaciones}-{self.tamaño_poblacion}-{self.p_mutacion_alumno}-{self.p_mutacion_teoria}-{self.p_mutacion_practica}-{self.metodo_seleccion}-{self.metodo_cruce}-{self.metodo_sustitucion}-{self.tamaño_torneo}")
                print("fitness" + " ( " + "solapes" + ", " +
                      "Cohesion teoria" + ", " +
                      "Equilibrio grupos" + ", " +
                      "Cohesion practicas" + ", " +
                      "Preferencias" + " ) " + str(generacion + 1) + " Generacion")
                print(f"{max_fitness:.4f}" + " " + str(max_solucion) + "\n")
                salida.append("Mejor Generacion: " + str(max_generacion))
                salida.append(f"{max_fitness:.4f}" + " " + str(max_solucion) + "\n")
            padres = []
            for i in range(0, len(poblacionInicial) - 1, 2):
                padre1, padre2 = self.__seleccion(poblacionInicial, fitness)
                padres.extend([(padre1, padre2)])
            nueva_generacion = self.__cruce(padres, listaAlumnos)
            for individuo in nueva_generacion:
                for i in range(len(individuo.alumnos)):
                    if random.random() < self.p_mutacion_alumno:
                        individuo.alumnos[i] = Mutar.mutar(individuo.alumnos[i], self.p_mutacion_teoria,
                                                           self.p_mutacion_practica, horarios_teoria,
                                                           horarios_practica)

            elementResponse = [poblacionInicial]
            poblacionInicial = self.__sustitucion(poblacionInicial, nueva_generacion, fitness)
            end_time = time.time()
            iteration_time = end_time - start_time
            elementResponse.append(iteration_time)
            response.append(elementResponse)
            tiempo_total += iteration_time
            if self.debug:
                print(f"Tiempo de la Generación {generacion + 1}: " + Utils.str_time(iteration_time))
                salida.append(f"Tiempo de la Generación {generacion + 1}: " + Utils.str_time(iteration_time))

        print(f"Tiempo Total: " + Utils.str_time(tiempo_total))
        self.time = tiempo_total
        salida.append(f"Tiempo Total: " + Utils.str_time(tiempo_total))

        Export.matriculas(max_solucion.alumnos, self.metodo_seleccion, self.metodo_cruce, self.metodo_sustitucion,
                          self.carpeta, script)
        Export.alumnos_clase(configuracion_inicial.estudiantes_asignatura, max_solucion.estudiantes_asignatura,
                             asignaturas, self.metodo_seleccion, self.metodo_cruce, self.metodo_sustitucion,
                             self.carpeta, script)

        return response