import random
import re
from collections import defaultdict

import numpy as np
from model.alumno import alumno
from model.solucion import solucion

class Mutar:

    @staticmethod
    def mutar(alumno, p_mutacion_teoria, p_mutacion_practicas,horarios_teoria,horarios_practica):
        for matricula in alumno.matriculas_variables:
            if random.random() < p_mutacion_practicas:
                matricula.grupo_practicas = 1 if matricula.grupo_practicas == 2 else 2
                matricula.horario_practicas = horarios_practica[matricula.cod_asignatura][matricula.grupo][matricula.grupo_practicas]

            if random.random() < p_mutacion_teoria:
                grupos = {10, 11, 12} if matricula.curso == 1 or matricula.cod_asignatura == 42325 else {10, 11}
                matricula.grupo = random.choice(list(grupos.difference({matricula.grupo})))
                matricula.horario_teoria = horarios_teoria[matricula.cod_asignatura][matricula.grupo]
                matricula.horario_practicas = horarios_practica[matricula.cod_asignatura][matricula.grupo][matricula.grupo_practicas]
        return alumno


class Seleccion:

    @staticmethod
    def seleccion_fitness(poblacion,fitness):
        probabilidades_seleccion = np.exp(list(fitness.values()))
        probabilidades_seleccion_n = probabilidades_seleccion / np.sum(probabilidades_seleccion)
        padre1 = poblacion[np.random.choice(len(poblacion),p=probabilidades_seleccion_n)]
        padre2 = poblacion[np.random.choice(len(poblacion),p=probabilidades_seleccion_n)]
        attempts = 0
        while padre1 == padre2 and attempts<5:
            padre2 = poblacion[np.random.choice(len(poblacion),p=probabilidades_seleccion_n)]
            attempts += 1
        return padre1, padre2

    @staticmethod
    def seleccion_rango(poblacion,fitness):
        id_sorted = sorted(fitness, key=lambda x: fitness[x], reverse=True)
        probabilidades_seleccion = [(2*(len(poblacion)-(i+1)+1))/((len(poblacion)**2)+len(poblacion)) for i in range(len(poblacion))]
        padre1 = poblacion[np.random.choice(id_sorted, p=probabilidades_seleccion)]
        padre2 = poblacion[np.random.choice(id_sorted, p=probabilidades_seleccion)]
        attempts = 0
        while padre1 == padre2 and attempts<5:
            padre2 = poblacion[np.random.choice(id_sorted, p=probabilidades_seleccion)]
            attempts += 1
        return padre1, padre2

    @staticmethod
    def seleccion_torneo(poblacion,fitness,k):

        torneo1 = random.sample([i for i in range(len(poblacion))], k)
        torneo2 = random.sample([i for i in range(len(poblacion))], k)
        id1 = sorted(torneo1, key=lambda x: fitness[x], reverse=True)[0]
        id2 = sorted(torneo2, key=lambda x: fitness[x], reverse=True)[0]
        attempts = 0
        while id1 == id2 and attempts<5:
            torneo2 = random.sample([i for i in range(len(poblacion))], k)
            id2 = sorted(torneo2, key=lambda x: fitness[x], reverse=True)[0]
            attempts+=1
        padre1 = poblacion[id1]
        padre2 = poblacion[id2]
        return padre1, padre2

class Cruce:

    @staticmethod
    def cruce_punto(padres,listaAlumnos):
        nueva_generacion = []
        for pareja in padres:
            division = random.randrange(len(listaAlumnos))
            padre1, padre2 = pareja[0], pareja[1]
            hijo1 = solucion(padre1.alumnos[:division]+padre2.alumnos[division:],listaAlumnos)
            hijo2 = solucion(padre2.alumnos[:division]+padre1.alumnos[division:],listaAlumnos)
            nueva_generacion.extend([hijo1,hijo2])
        return nueva_generacion

    @staticmethod
    def cruce_varios_puntos(padres,listaAlumnos):
        nueva_generacion = []
        for pareja in padres:
            punto1 = random.randint(0, len(listaAlumnos) - 2)
            punto2 = random.randint(punto1 + 1, len(listaAlumnos) - 1)
            padre1, padre2 = pareja[0], pareja[1]
            hijo1 = solucion(padre1.alumnos[:punto1] + padre2.alumnos[punto1:punto2] + padre1.alumnos[punto2:], listaAlumnos)
            hijo2 = solucion(padre2.alumnos[:punto1] + padre1.alumnos[punto1:punto2] + padre2.alumnos[punto2:], listaAlumnos)
            nueva_generacion.extend([hijo1, hijo2])
        return nueva_generacion

    @staticmethod
    def cruce_uniforme(padres,listaAlumnos):
        nueva_generacion = []
        for pareja in padres:
            mascara = [random.choice([False, True]) for _ in range(len(padres[0][0].alumnos))]
            padre1, padre2 = pareja[0], pareja[1]
            hijo1 = []
            hijo2 = []
            for i in range(len(padre1.alumnos)):
                hijo1.append(padre1.alumnos[i] if mascara[i] else padre2.alumnos[i])
                hijo2.append(padre2.alumnos[i] if mascara[i] else padre1.alumnos[i])

            nueva_generacion.extend([solucion(hijo1, listaAlumnos), solucion(hijo2, listaAlumnos)])

        return nueva_generacion


    @staticmethod
    def cruce_matriculas(padres,listaAlumnos):
        nueva_generacion = []
        for pareja in padres:
            padre1, padre2 = pareja[0], pareja[1]
            alumnos1 = []
            alumnos2 = []
            for i in range(len(padre1.alumnos)):
                if len(padre1.alumnos[i].matriculas_variables)>0:
                    b = (len(padre1.alumnos[i].matriculas_variables) - 1)
                    punto_corte = random.randint(0, b)
                    punto1 = int(len(padre1.alumnos[i].matriculas_variables) / 2) if punto_corte > int(len(padre1.alumnos[i].matriculas_variables) / 2) else punto_corte
                    punto2 = int(len(padre1.alumnos[i].matriculas_variables) / 2) if punto_corte <= int(len(padre1.alumnos[i].matriculas_variables) / 2) else punto_corte
                    matriculas_variables1 = padre1.alumnos[i].matriculas_variables[:punto1] + padre2.alumnos[i].matriculas_variables[punto1:punto2] + padre1.alumnos[i].matriculas_variables[punto2:]
                    matriculas_variables2 = padre2.alumnos[i].matriculas_variables[:punto1] + padre1.alumnos[i].matriculas_variables[punto1:punto2] + padre2.alumnos[i].matriculas_variables[punto2:]
                else:
                    matriculas_variables1 = []
                    matriculas_variables2 = []
                alumnos1.append(alumno(padre1.alumnos[i].nombre,matriculas_variables1,padre1.alumnos[i].matriculas_fijas))
                alumnos2.append(alumno(padre2.alumnos[i].nombre, matriculas_variables2, padre2.alumnos[i].matriculas_fijas))
            nueva_generacion.extend([solucion(alumnos1, listaAlumnos), solucion(alumnos2, listaAlumnos)])
        return nueva_generacion
class Sustitucion:

    @staticmethod
    def reemplazo(nueva_generacion):
        return nueva_generacion

    @staticmethod
    def elitismo(poblacionInicial,nueva_generacion,fitness):
        fitness_n = {i:nueva_generacion[i].calcular_fitness() for i in range(len(nueva_generacion))}
        max_id_old_g = max(fitness, key=lambda k: fitness[k])
        min_id_new_g = min(fitness_n, key=lambda k: fitness_n[k])
        nueva_generacion.pop(min_id_new_g)
        nueva_generacion.extend([poblacionInicial[max_id_old_g]])
        return nueva_generacion

    @staticmethod
    def truncamiento(poblacionInicial,nueva_generacion,fitness):
        fitness_nueva = {f"b{i}": nueva_generacion[i].calcular_fitness() for i in range(len(nueva_generacion))}

        # Unir fitness con población inicial (se asume que las claves del fitness original son enteros)
        fitness_total = {**{str(k): v for k, v in fitness.items()}, **fitness_nueva}

        # Ordenar todos por fitness descendente
        ids_ordenados = sorted(fitness_total.keys(), key=lambda x: fitness_total[x], reverse=True)

        ng = []
        for id_str in ids_ordenados[:len(poblacionInicial)]:
            if id_str.startswith("b"):
                idx = int(id_str[1:])
                ng.append(nueva_generacion[idx])
            else:
                idx = int(id_str)
                ng.append(poblacionInicial[idx])

        return ng



class Utils:

    @staticmethod
    def print_solucion(poblacionInicial,fitness,generacion):
        print("fitness" + " ( " + "solapes" + ", " +
              "Cohesion teoria" + ", " +
              "Equilibrio grupos" + ", " +
              "Cohesion practicas" + ", " +
              "Preferencias" + " ) " + str(generacion) +" Generacion")
        print("---------------------------------------------------------------------------------------------------------------------------------------")
        for e in range(len(poblacionInicial)):
            print(f"{fitness[e]:.4f}" + str(poblacionInicial[e]))
        print("---------------------------------------------------------------------------------------------------------------------------------------")


    @staticmethod
    def str_time(time):
        if time < 60:
            return (f"{time:.2f} seg")
        elif time < 3600:
            minutos = time/60
            return (f"{minutos:.2f} min")
        else:
            horas = time/3600
            return (f"{horas:.2f} hr")

    @staticmethod
    def to_second(time_str):
        match = re.match(r"([\d.]+)\s*(seg|min|hr)", time_str)
        if not match:
            raise ValueError("Formato de tiempo no válido")
        value, unit = match.groups()
        value = float(value)
        if unit == "seg":
            return value
        elif unit == "min":
            return value * 60
        elif unit == "hr":
            return value * 3600
        else:
            raise ValueError("Unidad de tiempo no reconocida")

    @staticmethod
    def import_horarios(horarios):

        horarios_teoria = defaultdict(lambda: defaultdict(list))
        horarios_practicas = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for indice, fila in horarios.iterrows():

            if fila["TEORÍA/PRÁCTICA"] == 'T':
                horarios_teoria[fila["CODIGO"]][fila["ID GRUPO"]].append(fila["DÍA"]+'/'+fila["HORARIO"])
            else:
                if len(horarios_practicas[fila["CODIGO"]][fila["ID GRUPO"]][1]) == 0:
                    horarios_practicas[fila["CODIGO"]][fila["ID GRUPO"]][1].append(fila["DÍA"]+'/'+fila["HORARIO"])
                else:
                    horarios_practicas[fila["CODIGO"]][fila["ID GRUPO"]][2].append(fila["DÍA"] + '/' + fila["HORARIO"])

        return horarios_teoria,horarios_practicas