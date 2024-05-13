from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook


class Export:

    @staticmethod
    def matriculas(listaAlumnos):
        wb = Workbook()
        ws = wb.active
        ws.append(["AÑO", "PLAN", "CODIGO", "ASIGNATURA", "ALUMNO", "GRUPO", "GP"])
        for alumno in listaAlumnos:
            matriculas = alumno.matriculas_variables + alumno.matriculas_fijas
            for matricula in matriculas:
                ws.append(["2023-24", "406", matricula.cod_asignatura, matricula.nombre_asignatura, alumno.nombre,
                           matricula.grupo, matricula.grupo_practicas])

        ws.column_dimensions[get_column_letter(4)].width = len(
            "PLANIFICACIÓN E INTEGRACIÓN DE SISTEMAS Y SERVICIOS") + 0.5
        ws.column_dimensions[get_column_letter(5)].width = len("Estudiante000") + 0.4
        wb.save('results/solucion.xlsx')

    @staticmethod
    def alumnos_clase(alumnosClaseInicio, alumnosClaseFinal, asignaturas):

        wb = Workbook()

        hoja1 = wb.active
        hoja1.title = "Configuracion Inicial"
        hoja2 = wb.create_sheet(title="Configuracion Final")

        hoja1.append(
            ["NOMBRE", "ALUMNOS", "ESPERADOS POR GRUPO TEORIA", "ESPERADOS POR GRUPO PRACTICAS", "GRUPO 10", "GP1",
             "GP2", "GRUPO 11", "GP1", "GP2", "GRUPO 12", "GP1", "GP2", ])
        hoja2.append(
            ["NOMBRE", "ALUMNOS", "ESPERADOS POR GRUPO TEORIA", "ESPERADOS POR GRUPO PRACTICAS", "GRUPO 10", "GP1",
             "GP2", "GRUPO 11", "GP1", "GP2", "GRUPO 12", "GP1", "GP2", ])

        alumnosClaseTeoriaInicio, alumnosClasePracticasInicio = alumnosClaseInicio[0], alumnosClaseInicio[1]
        alumnosClaseTeoriaFinal, alumnosClasePracticasFinal = alumnosClaseFinal[0], alumnosClaseFinal[1]

        for clave in alumnosClaseTeoriaInicio.keys():

            cod_asignatura = clave[0]
            filtro = (asignaturas["COD. ASIG"] == cod_asignatura)
            datos_asignatura = asignaturas.loc[filtro, ["NOMBRE ASIGNATURA", "CURSO"]]
            if (datos_asignatura["CURSO"] == 1).any():
                hoja1.append(
                    [datos_asignatura.iloc[0]["NOMBRE ASIGNATURA"], sum(alumnosClaseTeoriaInicio[clave].values()),
                     int(sum(alumnosClaseTeoriaInicio[clave].values()) / 3),
                     int((sum(alumnosClaseTeoriaInicio[clave].values()) / 3) / 2), alumnosClaseTeoriaInicio[clave][10],
                     alumnosClasePracticasInicio[clave[0]][10][1], alumnosClasePracticasInicio[clave[0]][10][2],
                     alumnosClaseTeoriaInicio[clave][11], alumnosClasePracticasInicio[clave[0]][11][1],
                     alumnosClasePracticasInicio[clave[0]][11][2], alumnosClaseTeoriaInicio[clave][12],
                     alumnosClasePracticasInicio[clave[0]][12][1], alumnosClasePracticasInicio[clave[0]][12][2]])
                hoja2.append(
                    [datos_asignatura.iloc[0]["NOMBRE ASIGNATURA"], sum(alumnosClaseTeoriaFinal[clave].values()),
                     int(sum(alumnosClaseTeoriaFinal[clave].values()) / 3),
                     int((sum(alumnosClaseTeoriaFinal[clave].values()) / 3) / 2),
                     alumnosClaseTeoriaFinal[clave][10], alumnosClasePracticasFinal[clave[0]][10][1],
                     alumnosClasePracticasFinal[clave[0]][10][2],
                     alumnosClaseTeoriaFinal[clave][11], alumnosClasePracticasFinal[clave[0]][11][1],
                     alumnosClasePracticasFinal[clave[0]][11][2], alumnosClaseTeoriaFinal[clave][12],
                     alumnosClasePracticasFinal[clave[0]][12][1],
                     alumnosClasePracticasFinal[clave[0]][12][2]])
            else:
                hoja1.append(
                    [datos_asignatura.iloc[0]["NOMBRE ASIGNATURA"], sum(alumnosClaseTeoriaInicio[clave].values()),
                     int(sum(alumnosClaseTeoriaInicio[clave].values()) / 2),
                     int((sum(alumnosClaseTeoriaInicio[clave].values()) / 2) / 2),
                     alumnosClaseTeoriaInicio[clave][10], alumnosClasePracticasInicio[clave[0]][10][1],
                     alumnosClasePracticasInicio[clave[0]][10][2],
                     alumnosClaseTeoriaInicio[clave][11], alumnosClasePracticasInicio[clave[0]][11][1],
                     alumnosClasePracticasInicio[clave[0]][11][2], "",
                     "",
                     ""])
                hoja2.append(
                    [datos_asignatura.iloc[0]["NOMBRE ASIGNATURA"], sum(alumnosClaseTeoriaFinal[clave].values()),
                     int(sum(alumnosClaseTeoriaFinal[clave].values()) / 2),
                     int((sum(alumnosClaseTeoriaFinal[clave].values()) / 2) / 2),
                     alumnosClaseTeoriaFinal[clave][10], alumnosClasePracticasFinal[clave[0]][10][1],
                     alumnosClasePracticasFinal[clave[0]][10][2],
                     alumnosClaseTeoriaFinal[clave][11], alumnosClasePracticasFinal[clave[0]][11][1],
                     alumnosClasePracticasFinal[clave[0]][11][2], "",
                     "",
                     ""])

        hoja1.column_dimensions[get_column_letter(1)].width = len("PROGRAMACIÓN CONCURRENTE Y TIEMPO REAL") + 5.7
        hoja1.column_dimensions[get_column_letter(2)].width = len("ALUMNOS") + 3
        hoja1.column_dimensions[get_column_letter(3)].width = len("ESPERADOS POR GRUPO TEORIA") + 3.3
        hoja1.column_dimensions[get_column_letter(4)].width = len("ESPERADOS POR GRUPO PRACTICAS") + 3.3

        hoja2.column_dimensions[get_column_letter(1)].width = len("PROGRAMACIÓN CONCURRENTE Y TIEMPO REAL") + 5.7
        hoja2.column_dimensions[get_column_letter(2)].width = len("ALUMNOS") + 3
        hoja2.column_dimensions[get_column_letter(3)].width = len("ESPERADOS POR GRUPO TEORIA") + 3.3
        hoja2.column_dimensions[get_column_letter(4)].width = len("ESPERADOS POR GRUPO PRACTICAS") + 3.3

        wb.save("results/estudiantes_asignatura.xlsx")