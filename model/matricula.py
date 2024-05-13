class matricula:

    def __init__(self,nombre_asignatura,cod_asignatura,curso,grupo,horario_teoria,grupo_practicas,horario_practicas,cuatrimestre):
        self.nombre_asignatura = nombre_asignatura
        self.cod_asignatura = cod_asignatura
        self.curso = curso
        self.grupo = grupo
        self.horario_teoria = horario_teoria
        self.grupo_practicas = grupo_practicas
        self.horario_practicas = horario_practicas
        self.cuatrimestre = cuatrimestre

    def __str__(self):
        return f'({self.nombre_asignatura},{self.grupo},{self.horario_teoria},{self.grupo_practicas},{self.horario_practicas})'