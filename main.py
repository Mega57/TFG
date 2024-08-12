from model.genetico import Genetico
from model.nsga3 import NSGA3

'''algoritmo_genetico = Genetico(800, 20, "fitness", "uniforme", "truncamiento", 0.05, 0.001, 0.005, 10, True)

algoritmo_genetico.ejecutar()'''

nsa3 = NSGA3(100,20,"uniforme",0.05, 0.001, 0.005,10,True)

nsa3.ejecutar()

