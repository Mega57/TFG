class configuracion:

    def __init__(self,tamaño_poblacion,generaciones,seleccion,cruce,sustitucion, p_mutacion_alumno, p_mutacion_teoria,p_mutacion_practica,tamaño_torneo,debug):
        self.tamaño_poblacion = tamaño_poblacion
        self.generaciones = generaciones
        self.seleccion = seleccion
        self.cruce = cruce
        self.sustitucion = sustitucion
        self.p_mutacion_alumno = p_mutacion_alumno
        self.p_mutacion_teoria = p_mutacion_teoria
        self.p_mutacion_practica = p_mutacion_practica
        self.tamaño_torneo = tamaño_torneo
        self.debug = debug