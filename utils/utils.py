import random
import numpy as np
from model.alumno import alumno
from model.solucion import solucion
import pandas as pd

class Mutar:

    @staticmethod
    def mutar(alumno, p_mutacion_teoria, p_mutacion_practicas):
        horariosPath = "docs/horarios.xlsx"
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
                filtro = (horarios["CODIGO"] == matricula.cod_asignatura) & (
                            horarios["ID GRUPO"] == matricula.grupo) & (
                                 horarios["TEORÍA/PRÁCTICA"] == "T")
                matricula.horario_teoria = horarios.loc[filtro].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'],
                                                                      axis=1).tolist()
                filtro2 = (horarios["CODIGO"] == matricula.cod_asignatura) & (
                        horarios["ID GRUPO"] == matricula.grupo) & (
                                  horarios["TEORÍA/PRÁCTICA"] == "P")
                matricula.horario_practicas = horarios.loc[filtro2].apply(lambda row: row['DÍA'] + '/' + row['HORARIO'],
                                                                          axis=1).tolist()
                matricula.horario_practicas.pop(abs(matricula.grupo_practicas - 2))
        return alumno


class Seleccion:

    @staticmethod
    def seleccion_fitness(poblacion,fitness):
        #probabilidades_seleccion = [fitness[i]/sum(fitness.values()) for i in range(len(poblacion))]
        probabilidades_seleccion = np.exp(list(fitness.values()))
        probabilidades_seleccion_n = probabilidades_seleccion / np.sum(probabilidades_seleccion)
        padre1 = poblacion[np.random.choice(len(poblacion),p=probabilidades_seleccion_n)]
        padre2 = poblacion[np.random.choice(len(poblacion),p=probabilidades_seleccion_n)]
        while padre1 == padre2:
            padre2 = poblacion[np.random.choice(len(poblacion),p=probabilidades_seleccion_n)]
        return padre1, padre2

    @staticmethod
    def seleccion_rango(poblacion,fitness):
        id_sorted = sorted(fitness, key=lambda x: fitness[x], reverse=True)
        probabilidades_seleccion = [(2*(len(poblacion)-(i+1)+1))/((len(poblacion)**2)+len(poblacion)) for i in range(len(poblacion))]
        padre1 = poblacion[np.random.choice(id_sorted, p=probabilidades_seleccion)]
        padre2 = poblacion[np.random.choice(id_sorted, p=probabilidades_seleccion)]
        while padre1 == padre2:
            padre2 = poblacion[np.random.choice(id_sorted, p=probabilidades_seleccion)]
        return padre1, padre2

    @staticmethod
    def seleccion_torneo(poblacion,fitness,k):

        torneo1 = random.sample([i for i in range(1, len(poblacion) + 1)], k)
        torneo2 = random.sample([i for i in range(1, len(poblacion) + 1)], k)
        id1 = sorted(torneo1, key=lambda x: fitness[x], reverse=True)[0]
        id2 = sorted(torneo2, key=lambda x: fitness[x], reverse=True)[0]
        while id1 == id2:
            torneo2 = random.sample([i for i in range(1, len(poblacion) + 1)], k)
            id2 = sorted(torneo2, key=lambda x: fitness[x], reverse=True)[0]
        padre1 = poblacion[id1]
        padre2 = poblacion[id2]
        return padre1, padre2

class Cruce:

    @staticmethod
    def cruce_punto(padres,listaAlumnos):
        nueva_generacion = []
        for pareja in padres:
            padre1, padre2 = pareja[0], pareja[1]
            division = int(len(padre1.alumnos) / 2)
            hijo1 = solucion(padre1.alumnos[:division]+padre2.alumnos[division:],listaAlumnos)
            hijo2 = solucion(padre2.alumnos[:division]+padre1.alumnos[division:],listaAlumnos)
            nueva_generacion.extend([hijo1,hijo2])
        return nueva_generacion

    @staticmethod
    def cruce_varios_puntos(padres,listaAlumnos):
        nueva_generacion = []
        for pareja in padres:
            padre1, padre2 = pareja[0], pareja[1]
            punto1 = int(len(padre1.alumnos) / 2) - 50
            punto2 = int(len(padre1.alumnos) / 2) + 50
            hijo1 = solucion(padre1.alumnos[:punto1] + padre2.alumnos[punto1:punto2] + padre1.alumnos[punto2:], listaAlumnos)
            hijo2 = solucion(padre2.alumnos[:punto1] + padre1.alumnos[punto1:punto2] + padre2.alumnos[punto2:], listaAlumnos)
            nueva_generacion.extend([hijo1, hijo2])
        return nueva_generacion

    @staticmethod
    def cruce_uniforme(padres,listaAlumnos):
        nueva_generacion = []
        mascara = [random.choice([False, True]) for _ in range(len(padres[0][0].alumnos))]
        for pareja in padres:
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
        fitness_n = {str(i) + 'b': nueva_generacion[i].calcular_fitness() for i in range(len(nueva_generacion))}
        fitness_n.update(fitness)
        n_individuos_id = sorted(fitness_n, key=lambda x: fitness_n[x], reverse=True)
        ng = []
        for i in range(len(poblacionInicial)):
            if not str(n_individuos_id[i])[-1].isalpha():
                individuo = poblacionInicial[n_individuos_id[i]]
                n_individuos_id.remove(str(n_individuos_id[i])+'b')
            else:
                individuo = nueva_generacion[int(str(n_individuos_id[i])[:-1])]
                n_individuos_id.remove(int(str(n_individuos_id[i])[:-1]))

            ng.append(individuo)
        return ng



class Utils:

    @staticmethod
    def print_solucion(poblacionInicial,fitness,generacion):
        print("fitness" + " ( " + "solapes" + ", " +
              "Cohesion teoria" + ", " +
              "Equilibrio grupos" + ", " +
              "Practicas pronto" + ", " +
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



