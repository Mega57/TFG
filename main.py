from model.configuracion import configuracion
from model.genetico import genetico


c = configuracion(400,20,"fitness","uniforme","truncamiento",0.05,0.001,0.005,10,True)

algoritmo_genetico = genetico(c)

algoritmo_genetico.ejecutar()
