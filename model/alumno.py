from itertools import combinations
class alumno:

    def __init__(self,nombre,matriculas_variables,matriculas_fijas):
        self.nombre = nombre
        self.matriculas_variables = matriculas_variables
        self.matriculas_fijas = matriculas_fijas

    def __str__(self):
        return f'({self.nombre},{self.matriculas_variables},{self.matriculas_fijas})'

    def calcular_solapes(self):
        solapes = 0
        try:
            matriculas = self.matriculas_variables + self.matriculas_fijas
            combinaciones = list(combinations(matriculas, 2))
            for c in combinaciones:
                matricula1, matricula2 = c[0], c[1]
                if matricula1.cuatrimestre == matricula2.cuatrimestre:
                    horarios1 = set(matricula1.horario_teoria + matricula1.horario_practicas)
                    horarios2 = set(matricula2.horario_teoria + matricula2.horario_practicas)
                    if len(horarios1.intersection(horarios2)) > 0:
                        solapes += 1
        except TypeError:
            print("ERROR")
        return solapes
