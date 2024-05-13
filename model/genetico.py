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
class genetico:

    def __init__(self,configuracion):
        self.generaciones = configuracion.generaciones
        self.tamaño_poblacion = configuracion.tamaño_poblacion
        self.p_mutacion_alumno = configuracion.p_mutacion_alumno
        self.p_mutacion_teoria = configuracion.p_mutacion_teoria
        self.p_mutacion_practica = configuracion.p_mutacion_practica
        self.metodo_seleccion = configuracion.seleccion
        self.metodo_cruce = configuracion.cruce
        self.metodo_sustitucion = configuracion.sustitucion
        self.tamaño_torneo = configuracion.tamaño_torneo
        self.debug = configuracion.debug


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
        elif self.metodo_sustitucion == 'elititsmo':
            return Sustitucion.elitismo(poblacionInicial,nueva_generacion,fitness)
        elif self.metodo_sustitucion == 'truncamiento':
            return Sustitucion.truncamiento(poblacionInicial,nueva_generacion,fitness)
        else:
            raise ValueError(f"Método de sustitucion {self.metodo_sustitucion} no soportado.")


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

        for alu in matriculas['ALUMNO'].unique():
            matriculas_variables = list()
            matriculas_fijas = list()
            grupo_primero = random.choice([10, 11, 12])
            for indice, fila in matriculas.loc[matriculas['ALUMNO'] == alu].iterrows():
                filtro = (horarios["CODIGO"] == fila["CODIGO"]) & (horarios["ID GRUPO"] == fila["GRUPO"]) & (
                        horarios["TEORÍA/PRÁCTICA"] == "T")
                filtro2 = (horarios["CODIGO"] == fila["CODIGO"]) & (horarios["ID GRUPO"] == fila["GRUPO"]) & (
                        horarios["TEORÍA/PRÁCTICA"] == "P")
                g = fila["GRUPO"]
                if fila["GRUPO"] == 14 and fila["CODIGO"] in list(
                        asignaturas[(asignaturas['CURSO'] == 1)]['COD. ASIG']):
                    filtro = (horarios["CODIGO"] == fila["CODIGO"]) & (horarios["ID GRUPO"] == grupo_primero) & (
                            horarios["TEORÍA/PRÁCTICA"] == "T")
                    filtro2 = (horarios["CODIGO"] == fila["CODIGO"]) & (horarios["ID GRUPO"] == grupo_primero) & (
                            horarios["TEORÍA/PRÁCTICA"] == "P")
                    g = grupo_primero
                horario_teoria = horarios.loc[filtro].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'],
                                                            axis=1).tolist()
                horario_practica = horarios.loc[filtro2].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'],
                                                               axis=1).tolist()
                if len(horario_practica) != 1:
                    horario_practica.pop()
                m = matricula(fila['ASIGNATURA'], fila['CODIGO'], horarios.loc[filtro].iloc[0]["CURSO"], g,
                              horario_teoria, fila['GP'], horario_practica,
                              horarios.loc[filtro].iloc[0]["CUATRIMESTRE"])
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

                    filtro = (horarios["CODIGO"] == asignatura.cod_asignatura) & (
                                horarios["ID GRUPO"] == asignatura.grupo) & (
                                     horarios["TEORÍA/PRÁCTICA"] == "T")
                    asignatura.horario_teoria = horarios.loc[filtro].apply(
                        lambda row: row['DÍA'] + '/' + row['HORARIO'], axis=1).tolist()
                    filtro2 = (horarios["CODIGO"] == asignatura.cod_asignatura) & (
                                horarios["ID GRUPO"] == asignatura.grupo) & (
                                      horarios["TEORÍA/PRÁCTICA"] == "P")
                    asignatura.horario_practicas = horarios.loc[filtro2].apply(
                        lambda row: row['DÍA'] + '/' + row['HORARIO'], axis=1).tolist()
                    asignatura.horario_practicas.pop(abs(asignatura.grupo_practicas - 2))
            poblacionInicial.append(solucion(individuo, listaAlumnos))


        max_fitness = float('-inf')
        max_solucion = None
        max_generacion = 0
        tiempo_total = 0
        '''Algoritmo genético'''
        for generacion in range(self.generaciones):
            start_time = time.time()
            fitness = {i: poblacionInicial[i].calcular_fitness() for i in range(len(poblacionInicial))}
            max_i = max(fitness, key=fitness.get)
            if fitness[max_i] > max_fitness:
                max_fitness = fitness[max_i]
                max_generacion = generacion + 1
                max_solucion = copy.deepcopy(poblacionInicial[max_i])
                Export.matriculas(max_solucion.alumnos)
                Export.alumnos_clase(configuracion_inicial.estudiantes_asignatura, max_solucion.estudiantes_asignatura,
                                     asignaturas)
            if self.debug:
                Utils.print_solucion(poblacionInicial, fitness, generacion + 1)
                print("Mejor Generacion: " + str(max_generacion))
                print(f"{max_fitness:.4f}" + " " + str(max_solucion) + "\n")
            padres = []
            for i in range(0, len(poblacionInicial) - 1, 2):
                padre1, padre2 = self.__seleccion(poblacionInicial, fitness)
                padres.extend([(padre1, padre2)])
            nueva_generacion = self.__cruce(padres, listaAlumnos)
            for individuo in nueva_generacion:
                for i in range(len(individuo.alumnos)):
                    if random.random() < self.p_mutacion_alumno:
                        individuo.alumnos[i] = Mutar.mutar(individuo.alumnos[i], self.p_mutacion_teoria, self.p_mutacion_practica)

            poblacionInicial = self.__sustitucion(poblacionInicial, nueva_generacion, fitness)
            end_time = time.time()
            iteration_time = end_time - start_time
            tiempo_total += iteration_time
            if self.debug:
                print(f"Tiempo de la Generación {generacion + 1}: "+Utils.str_time(iteration_time))

        print(f"Tiempo Total: " + Utils.str_time(tiempo_total))