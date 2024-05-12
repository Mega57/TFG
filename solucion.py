from collections import defaultdict
class solucion:

    def __init__(self,alumnos,preferencias):
        self.alumnos = alumnos
        self.solapes = 0
        self.tasa_cohesion = 0
        self.d_total = 0
        self.tasa_practicas_pronto = 0
        self.tasa_cohesion_practicas = 0
        self.tasa_preferencias = 0
        self.preferencias = preferencias
        self.estudiantes_asignatura = None

    def calcular_tasa_cohesion_desequilibrio(self):
        cohesiones_alumno = []  # Almacena las tasas de cohesión para cada alumno
        cohesiones_alumno_practicas = []
        estudiantes_por_teoria = defaultdict(lambda: defaultdict(int))  # Conteo de estudiantes por grupo de teoría
        estudiantes_por_practica = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # Conteo de estudiantes por subgrupo de prácticas
        tasas_practicas_pronto = []  # Almacena las tasas de asignación a prácticas pronto para cada alumno
        coincidencia_preferencias = []
        desequilibrio_grupos = []
        indice_alumno = 0
        for alumno in self.alumnos:
            indice_matricula = 0
            coincidencia_p = 0
            practicas_pronto = 0  # Contador para prácticas en horario pronto
            grupos_curso = defaultdict(set)  # Grupos por curso para el alumno
            asignaturas_curso_grupo = defaultdict(lambda: defaultdict(int))  # Asignaturas por curso y grupo
            cohesion_curso = defaultdict(float)  # Cohesión por curso
            practicas_curso = defaultdict(set)
            asignaturas_curso_practicas = defaultdict(lambda: defaultdict(int))
            cohesion_practicas = defaultdict(float)

            # Recorrido de las matrículas para calcular cohesión y contar estudiantes en teoría/práctica
            for matricula in alumno.matriculas_variables:
                grupos_curso[matricula.curso].add(matricula.grupo)
                practicas_curso[matricula.curso].add(matricula.grupo_practicas)
                asignaturas_curso_grupo[matricula.curso][matricula.grupo] += 1
                asignaturas_curso_practicas[matricula.curso][matricula.grupo_practicas] += 1
                estudiantes_por_teoria[(matricula.cod_asignatura, matricula.curso)][matricula.grupo] += 1
                estudiantes_por_practica[matricula.cod_asignatura][matricula.grupo][matricula.grupo_practicas] += 1
                if matricula.grupo_practicas == 1:  # Suponemos que 1 indica un horario pronto
                    practicas_pronto += 1
                if matricula.grupo == self.preferencias[indice_alumno].matriculas_variables[indice_matricula].grupo:
                    coincidencia_p+=1
                if matricula.grupo_practicas == self.preferencias[indice_alumno].matriculas_variables[indice_matricula].grupo_practicas:
                    coincidencia_p+=1
                indice_matricula += 1
            indice_alumno += 1
            # Cálculo de la tasa de prácticas pronto
            if len(alumno.matriculas_variables) != 0:
                tasas_practicas_pronto.append(practicas_pronto / len(alumno.matriculas_variables))
                coincidencia_preferencias.append(coincidencia_p / (len(alumno.matriculas_variables) * 2))

            # Cálculo de la cohesión por curso
            for curso in grupos_curso.keys():
                cohesion_curso[curso] = max(asignaturas_curso_grupo[curso].values()) / sum(asignaturas_curso_grupo[curso].values())
                cohesion_practicas[curso] = max(asignaturas_curso_practicas[curso].values()) / sum(asignaturas_curso_grupo[curso].values())


            # Promedio de la cohesión para el alumno
            if len(alumno.matriculas_variables) != 0:
                tasa_cohesion_alumno = (1 / len(asignaturas_curso_grupo.keys())) * sum(cohesion_curso.values())
                cohesiones_alumno.append(tasa_cohesion_alumno)
                cohesiones_alumno_practicas.append((1 / len(asignaturas_curso_grupo.keys())) * sum(cohesion_practicas.values()))

        self.estudiantes_asignatura = (estudiantes_por_teoria,estudiantes_por_practica)
        # Promedio de tasas para todos los alumnos
        tasa_practicas_pronto = (1 / len(tasas_practicas_pronto)) * sum(tasas_practicas_pronto)
        tasa_cohesion = (1 / len(cohesiones_alumno)) * sum(cohesiones_alumno)
        tasa_cohesion_practicas = (1 / len(cohesiones_alumno_practicas)) * sum(cohesiones_alumno_practicas)

        d_total = 0  # Inicialización del desequilibrio total
        # Cálculo del desequilibrio de grupos y subgrupos
        for asignatura in estudiantes_por_teoria.keys():
            desequilibrio_grupos_teoria = []
            desequilibrio_grupos_practicas = []
            if asignatura[1] == 1:  # Primer curso
                n_ideal = int(sum(estudiantes_por_teoria[asignatura].values()) / 3)
                grupos = [10,11,12]
            else:  # Otros cursos
                n_ideal = int(sum(estudiantes_por_teoria[asignatura].values()) / 2)
                grupos = [10, 11]
            n_ideal_practicas = int(n_ideal / 2)
            '''print(n_ideal)
            print(n_ideal_practicas)'''
            for grupo_teoria in grupos:
                '''print(estudiantes_por_teoria[asignatura][grupo_teoria])
                print(estudiantes_por_practica[asignatura[0]][grupo_teoria][1])
                print(estudiantes_por_practica[asignatura[0]][grupo_teoria][2])'''
                # Desequilibrio en grupos de teoría
                d_total += abs(estudiantes_por_teoria[asignatura][grupo_teoria] - n_ideal)
                desequilibrio_grupos_teoria.append(1-abs((estudiantes_por_teoria[asignatura][grupo_teoria] - n_ideal)/n_ideal))
                # Desequilibrio en subgrupos de prácticas
                d_total += abs(estudiantes_por_practica[asignatura][grupo_teoria][1] - n_ideal_practicas)
                d_total += abs(estudiantes_por_practica[asignatura][grupo_teoria][2] - n_ideal_practicas)
                desequilibrio_grupos_practicas.append(1-abs((estudiantes_por_practica[asignatura[0]][grupo_teoria][1] - n_ideal_practicas)/n_ideal_practicas))
                desequilibrio_grupos_practicas.append(1 - abs((estudiantes_por_practica[asignatura[0]][grupo_teoria][2] - n_ideal_practicas) / n_ideal_practicas))

            desequilibrio_grupos.append((sum(desequilibrio_grupos_teoria)+sum(desequilibrio_grupos_practicas))/(len(desequilibrio_grupos_teoria)+len(desequilibrio_grupos_practicas)))

        d_total/=6603
        desequilibrio_grupos_total = sum(desequilibrio_grupos)/len(desequilibrio_grupos)
        tasa_coincidencias_preferencias = (1/len(coincidencia_preferencias)) * sum(coincidencia_preferencias)

        return tasa_cohesion, desequilibrio_grupos_total, tasa_practicas_pronto, tasa_cohesion_practicas, tasa_coincidencias_preferencias

    def calcular_solapes(self):
        return sum(alumno.calcular_solapes() for alumno in self.alumnos)

    def calcular_fitness(self,w1=0.2,w2=0.2,w3=0.15,w4=0.15,w5=0.1,w6=0.2):
        self.solapes = self.calcular_solapes()
        self.tasa_cohesion,self.d_total,self.tasa_practicas_pronto,self.tasa_cohesion_practicas, self.tasa_preferencias= self.calcular_tasa_cohesion_desequilibrio()

        return ((w1 * self.tasa_cohesion) - (w2 * (self.solapes/solucion(self.preferencias,None).calcular_solapes())) + (w3 * self.d_total) + (w4 * self.tasa_practicas_pronto)
                + (w5 * self.tasa_cohesion_practicas) + (w6 * self.tasa_preferencias))

        #return 1/self.solapes

    def __str__(self):
        return (" ( " + str(self.solapes) + ", " +
               str(self.tasa_cohesion) + ", " +
               str(self.d_total) + ", " +
               str(self.tasa_practicas_pronto) + ", " +
               str(self.tasa_cohesion_practicas) + ", " +
               str(self.tasa_preferencias) + " ) ")

