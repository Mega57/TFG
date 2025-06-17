# Optimización Multiobjetivo de la asignación docente en el Grado de Ingeniería Informática para evitar superposiciones y satisfacer preferencias de horarios de los estudiantes

Este proyecto implementa un algoritmo genético diseñado para optimizar la asignación de alumnos a clases y grupos de prácticas en un entorno educativo, basándose en diversas métricas como la cohesión de grupo, preferencias de horario, y minimización de solapes.

Este proyecto implementa dos algoritmos genéticos —uno clásico y otro basado en **NSGA-III**— para optimizar la asignación de alumnos a grupos de teoría y prácticas en el Grado de Ingeniería Informática. El objetivo es evitar solapes horarios, satisfacer las preferencias de los estudiantes y lograr una distribución equilibrada de alumnos en los grupos.

## Estructura del Proyecto

```
.
├── app.py
├── model/
│   ├── alumno.py
│   ├── matricula.py
│   ├── solucion.py
│   ├── genetico.py
│   └── nsga3.py
├── utils/
│   ├── export.py
│   └── utils.py
├── docs/
│   ├── asignaturas.xlsx
│   ├── horarios.xlsx
│   └── matriculas.xlsx
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   ├── resultados_genetico.html
│   └── resultados_nsga.html
├── scripts/
│   ├── fase1.py
│   ├── fase2.py
│   └── fase3.py
└── result/
```

### Descripción de archivos y carpetas

- **`app.py`**: Archivo principal que lanza la aplicación web. Gestiona las peticiones de usuario, redirige a la lógica correspondiente y devuelve respuestas a la interfaz.

#### Carpeta `model`
Contiene los módulos principales donde se implementa la lógica de los algoritmos:
- `alumno.py`: Define la clase `Alumno`, que contiene la información de cada estudiante.
- `matricula.py`: Clase `Matricula`, que gestiona los registros de cada asignatura a la que se matricula un alumno.
- `solucion.py`: Representa un individuo en el algoritmo genético. Una solución contiene una lista de alumnos, y cada alumno su lista de matrículas.
- `genetico.py`: Implementación del algoritmo genético clásico.
- `nsga3.py`: Implementación del algoritmo NSGA-III.

#### Carpeta `utils`
Módulos auxiliares:
- `export.py`: Funciones para exportar los resultados a formato Excel.
- `utils.py`: Funciones de apoyo para tareas comunes.

#### Carpeta `docs/`
Contiene los archivos de entrada:
- `asignaturas.xlsx`: Información de todas las asignaturas del grado.
- `horarios.xlsx`: Horarios detallados por grupo de teoría y prácticas.
- `matriculas.xlsx`: Matrículas reales anonimizadas del curso 2023–2024.

#### Carpeta `static`
Contiene los estilos CSS utilizados por las plantillas de la aplicación web:
- `style.css`: Estilo base de la interfaz.

#### Carpeta `templates`
Contiene las plantillas HTML que definen la interfaz web:
- `index.html`: Página de inicio. Permite subir los archivos, seleccionar algoritmo y configuración, y ejecutar el proceso.
- `resultados_genetico.html`: Muestra los resultados del algoritmo genético clásico.
- `resultados_nsga.html`: Muestra los resultados del algoritmo NSGA-III.

#### Carpeta `scripts`
Contiene los scripts que se han usado en la fase de experimentación:
- `fase1.py`: Evalúa todas las combinaciones de métodos de selección, cruce y sustitución con hiperparámetros fijos (genético clásico).
- `fase2.py`: Evalúa diferentes combinaciones de hiperparámetros con los mejores métodos de la fase 1 (genético clásico).
- `fase3.py`: Evalúa combinaciones de hiperparámetros en NSGA-III.

## Cómo Empezar

Instala las dependencias necesarias:

```bash
pip install numpy
pip install pandas
pip install openpyxl
pip install flask
pip install werkzeug
```

Clona este repositorio y ejecuta la aplicación web:

```bash
git clone https://github.com/Mega57/TFG.git
cd TFG
python app.py
```

Después de ejecutar, accede a la siguiente dirección en tu navegador:

```
http://localhost:5000
```

Desde ahí podrás subir los ficheros de entrada, seleccionar el algoritmo y configuración, y visualizar los resultados.

## Salida y Resultados

Durante la ejecución desde la aplicación web, los resultados se almacenan automáticamente en la carpeta:

```
/result
```

### Algoritmo Genético Clásico

Se generan dos archivos correspondientes al individuo con mayor **fitness** de todas las generaciones:

- **`matriculas.xlsx`**: Contiene la configuración final de matrícula de ese individuo.
- **`distribucion-grupos.xlsx`**: Muestra cómo ha quedado el reparto de alumnos por grupo de teoría y prácticas. Este objetivo es especialmente relevante, ya que busca mantener el equilibrio entre los grupos.

### Algoritmo NSGA-III

Se generan múltiples soluciones no dominadas (frente de Pareto final). Para cada una se crea una subcarpeta:

```
/result/
├── solucion_1/
│   ├── matriculas.xlsx
│   └── distribucion-grupos.xlsx
├── solucion_2/
│   ├── matriculas.xlsx
│   └── distribucion-grupos.xlsx
```

