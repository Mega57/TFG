import copy
import random
import numpy as np
import pandas as pd
from alumno import alumno
from matricula import matricula
from solucion import solucion
from collections import defaultdict
from utils import Seleccion
from utils import Cruce
from utils import Sustitucion
from utils import Utils

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)

horariosPath = "docs/horarios.xlsx"
matriculasPath = "docs/matriculas.xlsx"
asignaturasPath = "docs/asignaturas.xlsx"

horarios = pd.read_excel(horariosPath)
matriculas = pd.read_excel(matriculasPath)
asignaturas = pd.read_excel(asignaturasPath)

def mutar(alumno):
    p_mutacion_practicas = 0.005
    p_mutacion_teoria = 0.001
    #cursos_vistos = set()
    #cursos_muta = set()
    #curso_nuevo = defaultdict(int)
    horarios = pd.read_excel(horariosPath)
    for matricula in alumno.matriculas_variables:
        if random.random() < p_mutacion_practicas:
            matricula.grupo_practicas = 1 if matricula.grupo_practicas == 2 else 2
            filtro2 = (horarios["CODIGO"] == matricula.cod_asignatura) & (
                    horarios["ID GRUPO"] == matricula.grupo) & (
                              horarios["TEORÍA/PRÁCTICA"] == "P")
            matricula.horario_practicas = horarios.loc[filtro2].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'],
                                                                      axis=1).tolist()
            matricula.horario_practicas.pop(abs(matricula.grupo_practicas - 2))

        if random.random() < p_mutacion_teoria:
            grupos = {10, 11, 12} if matricula.curso == 1 else {10, 11}
            matricula.grupo = random.choice(list(grupos.difference({matricula.grupo})))
            filtro = (horarios["CODIGO"] == matricula.cod_asignatura) & (horarios["ID GRUPO"] == matricula.grupo) & (
                    horarios["TEORÍA/PRÁCTICA"] == "T")
            matricula.horario_teoria = horarios.loc[filtro].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'],
                                                                  axis=1).tolist()
            filtro2 = (horarios["CODIGO"] == matricula.cod_asignatura) & (
                    horarios["ID GRUPO"] == matricula.grupo) & (
                              horarios["TEORÍA/PRÁCTICA"] == "P")
            matricula.horario_practicas = horarios.loc[filtro2].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'],
                                                                      axis=1).tolist()
            matricula.horario_practicas.pop(abs(matricula.grupo_practicas - 2))

        '''if matricula.curso not in cursos_vistos:
            cursos_vistos.add(matricula.curso)
            if random.random() < p_mutacion_teoria:
                cursos_muta.add(matricula.curso)
        if matricula.curso in cursos_muta:
            if curso_nuevo[matricula.curso] == 0:
                grupos = {10,11,12} if matricula.curso == 1 else {10,11}
                curso_nuevo[matricula.curso] = random.choice(list(grupos.difference({matricula.grupo})))
            matricula.grupo = curso_nuevo[matricula.curso]
            filtro = (horarios["CODIGO"] == matricula.cod_asignatura) & (horarios["ID GRUPO"] == matricula.grupo) & (
                    horarios["TEORÍA/PRÁCTICA"] == "T")
            matricula.horario_teoria = horarios.loc[filtro].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'],
                                                                   axis=1).tolist()
            filtro2 = (horarios["CODIGO"] == matricula.cod_asignatura) & (
                    horarios["ID GRUPO"] == matricula.grupo) & (
                              horarios["TEORÍA/PRÁCTICA"] == "P")
            matricula.horario_practicas = horarios.loc[filtro2].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'],
                                                                      axis=1).tolist()
            matricula.horario_practicas.pop(abs(matricula.grupo_practicas - 2))'''

    return alumno


'''Lo primero es obtener una lista con los codigos de las asignaturas que son obligatorias y por ende tendrán más de un grupo'''
asignaturasObligatorias = list(asignaturas[(asignaturas['TECNOLOGÍA'] == 'OB')]['COD. ASIG'])


#Poblacion inicial que sera una lista de objetos del tipo alumno
listaAlumnos = list()
poblacionInicial = []

for alu in matriculas['ALUMNO'].unique():
    matriculas_variables = list()
    matriculas_fijas = list()
    grupo_primero = random.choice([10,11,12])
    for indice,fila in matriculas.loc[matriculas['ALUMNO'] == alu].iterrows():
        filtro = (horarios["CODIGO"] == fila["CODIGO"]) & (horarios["ID GRUPO"] == fila["GRUPO"]) & (
                    horarios["TEORÍA/PRÁCTICA"] == "T")
        filtro2 = (horarios["CODIGO"] == fila["CODIGO"]) & (horarios["ID GRUPO"] == fila["GRUPO"]) & (
                    horarios["TEORÍA/PRÁCTICA"] == "P")
        g = fila["GRUPO"]
        if fila["GRUPO"] == 14 and fila["CODIGO"] in list(asignaturas[(asignaturas['CURSO'] == 1)]['COD. ASIG']):
            filtro = (horarios["CODIGO"] == fila["CODIGO"]) & (horarios["ID GRUPO"] == grupo_primero) & (
                        horarios["TEORÍA/PRÁCTICA"] == "T")
            filtro2 = (horarios["CODIGO"] == fila["CODIGO"]) & (horarios["ID GRUPO"] == grupo_primero) & (
                        horarios["TEORÍA/PRÁCTICA"] == "P")
            g=grupo_primero
        horario_teoria = horarios.loc[filtro].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'], axis=1).tolist()
        horario_practica = horarios.loc[filtro2].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'], axis=1).tolist()
        if len(horario_practica) != 1:
            horario_practica.pop()
        m = matricula(fila['ASIGNATURA'], fila['CODIGO'], horarios.loc[filtro].iloc[0]["CURSO"], g,
                      horario_teoria, fila['GP'], horario_practica, horarios.loc[filtro].iloc[0]["CUATRIMESTRE"])
        if fila['CODIGO'] in asignaturasObligatorias and fila['CODIGO'] != 42325:
            matriculas_variables.append(m)
        else:
            matriculas_fijas.append(m)
    listaAlumnos.append(alumno(alu, matriculas_variables, matriculas_fijas))

configuracion_inicial = solucion(listaAlumnos,listaAlumnos)
fitness_inicial = configuracion_inicial.calcular_fitness()
print("Configuracion inicial")
print(str(fitness_inicial)+" "+str(configuracion_inicial))
#s = solucion(listaAlumnos)
#poblacionInicial.append(s)
#print(s.calcular_tasa_cohesion_desequilibrio())
#print(s.calcular_solapes())

'''Preparamos poblacion inicial'''
for i in range(400):
    individuo = copy.deepcopy(listaAlumnos)
    for a in individuo:
        grupos_curso = defaultdict(int)
        for asignatura in a.matriculas_variables:
            asignatura.grupo_practicas = random.choice([1,2])
            if grupos_curso[asignatura.curso] != 0:
                asignatura.grupo = grupos_curso[asignatura.curso]
            else:
                asignatura.grupo = random.choice([10, 11, 12]) if asignatura.curso == 1 else random.choice([10, 11])
                grupos_curso[asignatura.curso] = asignatura.grupo

            filtro = (horarios["CODIGO"] == asignatura.cod_asignatura) & (horarios["ID GRUPO"] == asignatura.grupo) & (
                    horarios["TEORÍA/PRÁCTICA"] == "T")
            asignatura.horario_teoria = horarios.loc[filtro].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'], axis=1).tolist()
            filtro2 = (horarios["CODIGO"] == asignatura.cod_asignatura) & (horarios["ID GRUPO"] == asignatura.grupo) & (
                    horarios["TEORÍA/PRÁCTICA"] == "P")
            asignatura.horario_practicas = horarios.loc[filtro2].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'], axis=1).tolist()
            asignatura.horario_practicas.pop(abs(asignatura.grupo_practicas-2))
    poblacionInicial.append(solucion(individuo,listaAlumnos))


generaciones = 20
N = len(poblacionInicial)
max_fitness = float('-inf')
max_solucion = None
max_generacion = 0
'''Algoritmo genético'''
for generacion in range(generaciones):
    fitness = {i:poblacionInicial[i].calcular_fitness() for i in range(len(poblacionInicial))}
    max_i = max(fitness, key=fitness.get)
    if fitness[max_i] >= max_fitness:
        max_fitness=fitness[max_i]
        max_generacion = generacion+1
        max_solucion = copy.deepcopy(poblacionInicial[max_i])
        Utils.export(max_solucion.alumnos)
        Utils.export_alumnos_clae(configuracion_inicial.estudiantes_asignatura,max_solucion.estudiantes_asignatura,asignaturas)

    Utils.print_solucion(poblacionInicial,fitness)
    print(str(generacion+1))
    print(str(max_fitness) + " " + str(max_solucion))
    print(solucion(max_solucion.preferencias, None).calcular_solapes())
    print(max_generacion)
    nueva_generacion = []
    padres = []
    for i in range(0,len(poblacionInicial)-1,2):
        padre1, padre2 = Seleccion.seleccion_fitness(poblacionInicial,fitness)
        padres.extend([(padre1,padre2)])
    nueva_generacion = Cruce.cruce_uniforme(padres,listaAlumnos)
    for individuo in nueva_generacion:
        for i in range(len(individuo.alumnos)):
            if random.random() < 0.05:
                individuo.alumnos[i] = mutar(individuo.alumnos[i])

    poblacionInicial = Sustitucion.truncamiento(poblacionInicial,nueva_generacion,fitness)


'''matri1 = matricula("a1",1,1,"a",None,1,None,1)
matri2 = matricula("a2",2,1,"a",None,1,None,1)
matri3 = matricula("a3",3,2,"a",None,1,None,1)
matri4 = matricula("a4",4,2,"a",None,1,None,1)

alumno1 = alumno("a",[matri1,matri2,matri3,matri4],None)

matri5 = matricula("a1",1,1,"a",None,1,None,1)
matri6 = matricula("a2",2,1,"b",None,1,None,1)
matri7 = matricula("a3",3,2,"a",None,1,None,1)


alumno2 = alumno("a2",[matri5,matri6,matri7],None)

so = solucion([alumno1,alumno2])

print(so.calcular_tasa_cohesion_desequilibrio())'''