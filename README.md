# Optimización Multiobjetivo de la asignación docente en el Grado de Ingeniería Informática para evitar superposiciones y satisfacer preferencias de horarios de los estudiantes

Este proyecto implementa un algoritmo genético diseñado para optimizar la asignación de alumnos a clases y grupos de prácticas en un entorno educativo, basándose en diversas métricas como la cohesión de grupo, preferencias de horario, y minimización de solapes.

## Estructura del Proyecto

El proyecto está organizado en diferentes carpetas que contienen módulos específicos y datos relacionados:

### Carpeta `model`
Contiene los módulos principales que definen la lógica del algoritmo genético:
- **alumno.py**: Define la clase `Alumno`, que maneja las características y métodos específicos de cada alumno.
- **matricula.py**: Define la clase `Matricula`, que gestiona la información relacionada con las matrículas de cada alumno.
- **solucion.py**: Representa una solución generada por el algoritmo genético, incluyendo métodos para evaluar y comparar soluciones.
- **configuracion.py**: Gestiona la carga y el acceso a la configuración del algoritmo genético, permitiendo ajustes dinámicos en los parámetros de ejecución.
- **genetico.py**: Contiene la implementación principal del algoritmo genético, organizando los procesos de selección, cruce, y mutación.
### Carpeta `utils`
Contiene utilidades y funciones de soporte:
- **export.py**: Proporciona funcionalidades para exportar los resultados del algoritmo a diversos formatos para su análisis o presentación.
- **utils.py**: Incluye funciones auxiliares que apoyan en las diversas tareas del algoritmo.

### Carpeta `docs`
Almacena archivos de datos en formato Excel que son utilizados por el algoritmo:
- **asignaturas.xlsx**: Detalles de las asignaturas disponibles.
- **horarios.xlsx**: Horarios asociados a las asignaturas.
- **matriculas.xlsx**: Información sobre las matrículas de los alumnos.

**main.py**: Archivo principal que inicia y coordina la ejecución del algoritmo genético.

## Salida y Resultados

- **ejemplo_salida.txt**: Este archivo contiene un ejemplo de las impresiones en consola que el algoritmo produce durante su ejecución, mostrando el progreso y las métricas calculadas en cada generación. (Este archivo es solo un ejemplo de lo que se imprime en consola)
- **/results**: Esta carpeta contiene dos archivos generados al final de la ejecución del algoritmo:
  - **configuracion_matriculas.xlsx**: Almacena la configuración final de las matrículas de los alumnos como resultado de la optimización.
  - **proporcion_alumnos.xlsx**: Incluye la proporción ideal de alumnos que debería tener cada grupo de teoría y prácticas en las asignaturas y los conteos de alumnos al inicio y al final de la ejecución.

## Cómo Empezar

Para ejecutar este proyecto, asegúrate de tener Python instalado y las dependencias necesarias:

```bash
pip install numpy
pip install pandas
pip install openpyxl
```
Clona este repositorio y ejecuta el archivo main.py para iniciar el algoritmo:
```bash
git clone https://github.com/Mega57/TFG.git
cd repositorio
python main.py
```

## Configuración

Los parámetros del algoritmo genético se ajustan a través de la clase Configuracion, que se instancia y se pasa al constructor de Genetico. Puedes modificar los parámetros directamente en el código o cargarlos desde un archivo externo antes de crear la instancia de Configuracion.

Ejemplo de configuración en main.py:
```python
from configuracion import Configuracion
from genetico import Genetico

# Configurar los parámetros del algoritmo
config = configuracion(tamaño_poblacion=400,generaciones=20,seleccion="fitness",cruce="uniforme",sustitucion="truncamiento",p_mutacion_alumno=0.05,p_mutacion_teoria=0.001,p_mutacion_practica=0.005,tamaño_torneo=10,debug=True)
genetico = genetico(config)
genetico.ejecutar()
```

