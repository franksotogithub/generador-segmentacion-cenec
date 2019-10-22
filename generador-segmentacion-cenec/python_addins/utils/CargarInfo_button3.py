import arcpy
import pyodbc

arcpy.env.overwriteOutput = True

agregarTablaRutas = arcpy.GetParameter(0)

gdb = arcpy.GetParameter(0)


HOST = '192.168.200.46'
DB_NAME = 'CENEC_SEGMENTACION'
USER = 'sde'
PASSWORD = 'wruvA7a*tat*'


def conectionDB_arcpy():
    if arcpy.Exists("{}.sde".format(DB_NAME)) == False:
        arcpy.CreateDatabaseConnection_management("Database Connections",
                                                  "{}.sde".format(DB_NAME),
                                                  "SQL_SERVER",
                                                  HOST,
                                                  "DATABASE_AUTH",
                                                  USER,
                                                  PASSWORD,
                                                  "#",
                                                  DB_NAME,
                                                  "#",
                                                  "#",
                                                  "#",
                                                  "#")

    conexionDB = r'Database Connections\{}.sde'.format(DB_NAME)
    return conexionDB


def conection_bd():
    cnxn = pyodbc.connect(
        'DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s'
        % (HOST, DB_NAME, USER, PASSWORD), autocommit=True)
    cursor = cnxn.cursor()
    return cnxn, cursor


def cargar(gdb):
    conexionGDB = conectionDB_arcpy()
    dataset =  r'{}\Procesamiento'.format(gdb)
    rutaFD = r'{}\Generales'.format(gdb)
    mxd = arcpy.mapping.MapDocument("CURRENT")
    arcpy.env.overwriteOutput= True
    arcpy.env.workspace = rutaFD

    features = arcpy.ListFeatureClasses()

    programacion_rutas = [feature for feature in features if feature[0:3] == 'AES'][0]
    arcpy.env.workspace = dataset
    features = arcpy.ListFeatureClasses()

    for feature in features:
        print 'feature>>>', feature

    temp_programacion_brigadas = [feature for feature in features if feature[0:21] == 'programacion_brigadas']

    #programacion_brigadas = [feature for feature in features if feature[0:21] == 'programacion_brigadas'][0]


    temp_programacion_adicional = [feature for feature in features if feature[0:22] == 'programacion_adicional']

    programacion_adicional = None
    programacion_brigadas = None

    if len(temp_programacion_adicional)>0:
        programacion_adicional = temp_programacion_adicional[0]
        opc =1

    else:
        opc = 2

    if len(temp_programacion_brigadas)>0:
        programacion_brigadas = temp_programacion_brigadas[0]


    if programacion_rutas is None:
        arcpy.AddError("No se encuentra la tabla de programacion de rutas dentro de la GDB ingresada")
    elif programacion_brigadas is  None:
        arcpy.AddError("No se encuentra la tabla de programacion de brigadas dentro de la GDB ingresada")


    else:

        path_programacion_rutas = r'{}\{}'.format(rutaFD, programacion_rutas)


        mf_programacion_rutas = arcpy.MakeFeatureLayer_management(path_programacion_rutas, 'programacion_rutas')





        path_programacion_brigadas = r'{}\{}'.format(gdb, programacion_brigadas)

        mf_programacion_brigadas = arcpy.MakeFeatureLayer_management(path_programacion_brigadas, 'programacion_brigadas')



        cant_brigadas = int(arcpy.GetCount_management(mf_programacion_brigadas)[0])

        if (cant_brigadas == 0):


            arcpy.AddError("La programacion de brigadas no se encuentra llena")
        else:

            temp_rutas = arcpy.TableToTable_conversion(mf_programacion_rutas, conexionGDB, 'TEMP_PROGRAMACION_RUTAS',
                                                       'RUTA IS NOT NULL')

            temp_brigadas = arcpy.TableToTable_conversion(mf_programacion_brigadas, conexionGDB,
                                                          'TEMP_PROGRAMACION_BRIGADAS', ' DIAS_TRABAJO > 0')


            campos_temp_rutas = [
                        ("RUTA_TEMP", "SHORT", "3"),
                        ("BRIGADA_TEMP", "SHORT", "3"),
                        ("TOTAL_DIAS", "SHORT", "3"),
                        ]

            campos_temp_brigadas = [
                ("BRIGADA_TEMP", "SHORT", "3"),
                ("TOTAL_DIAS", "SHORT", "3"),
            ]

            for n in campos_temp_rutas:
                if n[1] == "TEXT":
                    arcpy.AddField_management(temp_rutas, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE', 'NON_REQUIRED', '#')
                else:
                    arcpy.AddField_management(temp_rutas, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')

            for n in campos_temp_brigadas:
                if n[1] == "TEXT":
                    arcpy.AddField_management(temp_brigadas, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE', 'NON_REQUIRED', '#')
                else:
                    arcpy.AddField_management(temp_brigadas, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')


            if programacion_adicional is not None:
                path_programacion_adicional = r'{}\{}'.format(gdb, programacion_adicional)


                mf_programacion_adicional = arcpy.MakeFeatureLayer_management(path_programacion_adicional, 'programacion_adicional')
                temp_programacion_adicional = arcpy.TableToTable_conversion(mf_programacion_adicional, conexionGDB, 'TEMP_PROGRAMACION_ADICIONAL')
                campos_temp_programacion_adicional = [
                    ("RUTA_TEMP", "SHORT", "3"),
                    ("BRIGADA_TEMP", "SHORT", "3"),
                ]


                for n in campos_temp_programacion_adicional:
                    if n[1] == "TEXT":
                        arcpy.AddField_management(temp_programacion_adicional, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE',
                                                  'NON_REQUIRED', '#')
                    else:
                        arcpy.AddField_management(temp_programacion_adicional, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE',
                                                  'NON_REQUIRED', '#')
            conexion , cursor = conection_bd()
            cursor.execute("EXEC sde.SP_ACTUALIZAR_PROGRAMACION {opc}".format(opc=opc) )
            conexion.commit()
            cursor.close()

cargar(gdb)


