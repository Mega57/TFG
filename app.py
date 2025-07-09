from collections import defaultdict

import numpy as np
import traceback
from model.genetico import Genetico
from model.nsga3 import NSGA3

import os
import uuid
import threading
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename

from utils.utils import Utils

app = Flask(__name__)
app.secret_key = 'clave_super_secreta'

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'resultados'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Variables globales
execution_thread = None
execution_cancelled = False
execution_lock = threading.Lock()
resultados_globales = {}  # Almacena resultados por ID de sesión
errores_globales = {}


@app.route('/', methods=['GET'])
def index():
    sid = session.get('sid')
    error_msg = errores_globales.pop(sid, None) if sid else None
    return render_template('index.html', error=error_msg)


@app.route('/upload', methods=['POST'])
def upload():
    horarios = request.files.get('horarios')
    matriculas = request.files.get('matriculas')
    session['params'] = request.form.to_dict()
    path_h = ''
    path_m = ''

    # Crear ID único por sesión
    session_id = str(uuid.uuid4())
    session['sid'] = session_id

    params = session['params']
    if params['configuracion'] == "manual":
        algoritmo = params.get('algoritmo')
        poblacion = int(params['poblacion'])
        t_torneo = int(params['t_torneo']) if (algoritmo == "clasico" and params['seleccion'] == "torneo") or algoritmo != "clasico" else None
        if t_torneo is not None and t_torneo > poblacion:
            errores_globales[session_id] = "El tamaño del torneo no puede ser mayor que el tamaño de la población."
            return redirect(url_for('index'))

    if horarios:
        filename_h = secure_filename(horarios.filename)
        path_h = os.path.join(UPLOAD_FOLDER, filename_h)
        horarios.save(path_h)
        session['horarios_path'] = path_h

    if matriculas:
        filename_m = secure_filename(matriculas.filename)
        path_m = os.path.join(UPLOAD_FOLDER, filename_m)
        matriculas.save(path_m)
        session['matriculas_path'] = path_m

    if not path_h.endswith('.xlsx') or not path_m.endswith('.xlsx'):
        session['error'] = "Los archivos deben ser .xlsx"
        return redirect(url_for('index'))

    return redirect(url_for('loading'))


@app.route('/loading', methods=['GET'])
def loading():
    global execution_thread, execution_cancelled

    sid = session.get('sid')
    params = session['params']
    horarios_path = session['horarios_path']
    matriculas_path = session['matriculas_path']
    algoritmo = params.get('algoritmo')

    with execution_lock:
        if execution_thread and execution_thread.is_alive():
            execution_cancelled = True
            execution_thread.join()
        execution_cancelled = False

    def run_algorithm():
        global execution_cancelled
        try:
            with execution_lock:
                if execution_cancelled:
                    print("Cancelado antes de empezar")
                    return

            # Configuracion manual u optima
            if params['configuracion'] == "manual":
                poblacion = int(params['poblacion'])
                generaciones = int(params['generaciones'])
                seleccion = params['seleccion'] if algoritmo == "clasico" else 'torneo'
                cruce = params['cruce']
                sustitucion = params['sustitucion'] if algoritmo == "clasico" else 'sustitucion'
                mutacion_elemento = float(params['mutacion_elemento'])
                mutacion_teoria = float(params['mutacion_teoria'])
                mutacion_practica = float(params['mutacion_practica'])
                t_torneo = int(params['t_torneo']) if seleccion == "torneo" else None
                particiones = int(params['particiones']) if algoritmo == "nsga-iii" else None
            else:
                poblacion = 500 if algoritmo == "clasico" else 300
                generaciones = 80 if algoritmo == "clasico" else 50
                seleccion = "torneo"
                cruce = "uniforme"
                sustitucion = "reemplazo"
                mutacion_elemento = 0.00009
                mutacion_teoria = 0.0005
                mutacion_practica = 0.0005
                t_torneo = 10
                particiones = 6 if algoritmo == "nsga-iii" else None

            cancel_check = lambda: execution_cancelled

            if algoritmo == "clasico":
                algoritmo_obj = Genetico(
                    poblacion, generaciones, seleccion, cruce, sustitucion,
                    mutacion_elemento, mutacion_teoria, mutacion_practica,
                    t_torneo, "result", True
                )
            elif algoritmo == "nsga-iii":
                algoritmo_obj = NSGA3(
                    poblacion, generaciones, cruce, mutacion_elemento, mutacion_teoria,
                    mutacion_practica, t_torneo, particiones,
                    "result", True)
            else:
                raise ValueError("Algoritmo no reconocido")

            result = algoritmo_obj.ejecutar(
                cancel_check, False,
                horariosPath=horarios_path,
                matriculasPath=matriculas_path
            )

            if not execution_cancelled:
                if algoritmo == "clasico":
                    max_solution_split = algoritmo_obj.max_fitness.split(" ")
                    resumen = []
                    for i, g in enumerate(result, start=1):
                        fitness = [f.fitness for f in g[0]]
                        f_mix = min(g[0], key=lambda f: f.fitness)
                        min_fitness = f_mix.fitness
                        mean_fitness = np.mean(fitness)
                        std_dev = np.sqrt(np.var(fitness, ddof=1))
                        time = g[1]
                        f_max = max(g[0], key=lambda f: f.fitness)
                        max_fitness = f_max.fitness
                        resumen.append({
                            "generacion": i,
                            "max": f"{max_fitness:.4f}" + str(f_max),
                            "media": f"{mean_fitness:.4f}",
                            "min": f"{min_fitness:.4f}" + str(f_mix),
                            "desviacion": f"{std_dev:.4f}",
                            "tiempo": Utils.str_time(time)
                        })

                    resultados_globales[sid] = {
                        "algortimo": "clasico",
                        "params": {
                            "poblacion": poblacion,
                            "generaciones": generaciones,
                            "seleccion": seleccion,
                            "cruce": cruce,
                            "sustitucion": sustitucion,
                            "mutacion_elemento": mutacion_elemento,
                            "mutacion_teoria": mutacion_teoria,
                            "mutacion_practica": mutacion_practica,
                            "t_torneo": t_torneo,
                        },
                        "mejor": {
                            "generacion": algoritmo_obj.max_generacion,
                            "objetivos": [
                                max_solution_split[0], max_solution_split[2],
                                max_solution_split[3], max_solution_split[4],
                                max_solution_split[5], max_solution_split[6]
                            ]
                        },
                        "resumen": resumen,
                        "archivos": ["matriculas.xlsx", "distribucion-grupos.xlsx"]
                    }

                elif algoritmo == "nsga-iii":
                    resumen = []
                    i=1
                    for sol in result:
                        resumen.append({
                            "generacion":i,
                            "num_elementos":len(sol[0]),
                            "tiempo":Utils.str_time(sol[1])
                        })
                        i+=1
                    frente = []  # lista de listas de objetivos [solapes, teoria, grupos, preferencias]
                    for sol in result[-1][0]:
                        frente.append([sol.solapes, f"{float(sol.tasa_cohesion):.4f}", f"{float(sol.d_total):.4f}", f"{float(sol.tasa_cohesion_practicas):.4f}", f"{float(sol.tasa_preferencias):.4f}"])

                    resultados_globales[sid] = {
                        "algortimo": "nsga",
                        "params": {
                            "poblacion": poblacion,
                            "generaciones": generaciones,
                            "cruce": cruce,
                            "particiones": particiones,
                            "mutacion_elemento": mutacion_elemento,
                            "mutacion_teoria": mutacion_teoria,
                            "mutacion_practica": mutacion_practica,
                            "t_torneo": t_torneo
                        },
                        "frente_pareto": frente,
                        "resumen": resumen,
                        "num_soluciones": len(frente)
                    }


        except Exception as e:
            print("EXCEPCION DETECTADA:", e)
            errores_globales[sid] = (
                "Se ha producido un error inesperado durante la ejecución del algoritmo. "
                "Por favor, revisa que los archivos subidos tengan el formato correcto y vuelve a intentarlo."
            )
            traceback.print_exc()
            resultados_globales.pop(sid, None)

    execution_thread = threading.Thread(target=run_algorithm)
    execution_thread.start()

    return render_template('loading.html')




@app.route('/cancel', methods=['POST'])
def cancel():
    global execution_cancelled
    with execution_lock:
        execution_cancelled = True
    sid = session.get('sid')
    resultados_globales.pop(sid, None)
    return redirect(url_for('index'))


@app.route('/resultado', methods=['GET'])
def resultado():
    sid = session.get('sid')
    if sid not in resultados_globales:
        return redirect(url_for('loading'))

    data = resultados_globales[sid]
    algoritmo = data['algortimo']

    if algoritmo == 'nsga':
        return render_template('result_nsga.html', data=data)
    else:
        return render_template('result_genetico.html', data=data)


@app.route('/descargar/<path:filename>')
def descargar(filename):
    return send_from_directory(RESULT_FOLDER, filename, as_attachment=True)


@app.route('/check-status')
def check_status():
    sid = session.get('sid')
    if sid in errores_globales:
        return {'ready': False, 'error': True}
    return {'ready': sid in resultados_globales, 'error': False}


if __name__ == '__main__':
    app.run(debug=True)
