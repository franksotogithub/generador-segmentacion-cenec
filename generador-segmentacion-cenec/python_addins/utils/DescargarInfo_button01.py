# -*- #################

import arcpy, time, getpass ,os
import pyodbc
sede = arcpy.GetParameterAsText(0)
subsede = arcpy.GetParameterAsText(1)
carpeta = arcpy.GetParameterAsText(2)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_INSUMOS = os.path.join(BASE_DIR,'insumos')

lyrTrack = os.path.join(PATH_INSUMOS,'TRACK.lyr')
#lyrAeu = os.path.join(PATH_INSUMOS,'AEU.lyr')
lyrAe = os.path.join(PATH_INSUMOS,'AE.lyr')
lyrCcppUrbano = os.path.join(PATH_INSUMOS,'CCPP_URBANO.lyr')
lyrHidro = os.path.join(PATH_INSUMOS,'HIDRO.lyr')
lyrProvincia = os.path.join(PATH_INSUMOS,'LIMITE_PROVINCIA.lyr')
lyrDistrito = os.path.join(PATH_INSUMOS,'LIMITE_DISTRITO.lyr')
lyrZona = os.path.join(PATH_INSUMOS,'LIMITE_ZONA.lyr')
lyrDepartamento = os.path.join(PATH_INSUMOS,'LIMITE_DEPARTAMENTO.lyr')
lyrSede = os.path.join(PATH_INSUMOS,'SEDE_OPERATIVA.lyr')


arcpy.env.overwriteOutput = True



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


def crearFileGDB(sede,subsede, carpeta):

    user = getpass.getuser()
    fecha = time.strftime('%d%b%y')
    hora = time.strftime('%H%M%S')
    nameFile = "SEGMENTACION_{}_{}_{}_{}".format(sede, subsede, fecha, hora)
    folder = arcpy.CreateFolder_management(carpeta, nameFile)
    nameGDB = "BD_SEGM_{}_{}".format(sede,subsede)
    fileGDB = arcpy.CreateFileGDB_management(folder, nameGDB, "10.0")

    fdGenerales = arcpy.CreateFeatureDataset_management(fileGDB, "Generales", arcpy.SpatialReference(4326))

    fdProcesamiento=arcpy.CreateFeatureDataset_management(fileGDB, "Procesamiento", arcpy.SpatialReference(4326))
    arcpy.CreateFeatureDataset_management(fileGDB, "Resultados", arcpy.SpatialReference(4326))





    campos_HIDRO = [
                    ("CLASIFICAC","SHORT","3"),("NOMBRE","TEXT","50"),("UBIGEO", "TEXT", "6"),
                    ("SUP_VIA", "TEXT", "50")
                    ]

    campos_CCPP_URBANO = [
                ("UBIGEO", "TEXT", "6"), ("CODCCPP", "TEXT", "5"), ("NOMCCPP", "TEXT", "100"),
                ("ESTADO","SHORT","3"),("CATEGORIA","TEXT","20"),("CODSEDE","TEXT","2"),
                ("SEDE_OPERATIVA","TEXT","100"),("DEPARTAMENTO","TEXT","100"),("PROVINCIA","TEXT","100"),
                ("DISTRITO", "TEXT", "100"), ("PRIORIDAD","TEXT","2")
                ]



    campos_AES = [

                ("PK_AEU","TEXT","15"),("CODSEDE","TEXT","2"),("CODSUBSEDE","SHORT","3"),
                ("UBIGEO", "TEXT", "6"),("ZONA", "TEXT", "5"), ("AEU", "TEXT", "3"),
                ("TOTAL_EST", "SHORT", "3"),("CANT_EST", "SHORT", "3"),("MERCADO", "SHORT", "3"),("PUESTO", "SHORT", "3"),
                ("N_MANZANAS", "SHORT", "3"),("RUTA", "SHORT", "3"),("PERSONAL_AD", "SHORT", "3"),
                ("BRIGADA","SHORT","3"),("PERIODO", "SHORT", "3"),("ORDEN","SHORT","3"), ("FECHA_INI","DATE","40"),("FECHA_FIN","DATE","40"), ("DIAS_VIAJE", "SHORT", "3"),
                ("DIAS_TRABAJO", "SHORT", "3"),("GABINETE", "SHORT", "3"),("DIAS_RECUPERACION", "SHORT", "3"),("DIAS_DESCANSO", "SHORT", "3"),
                ("DIAS_OPERATIVOS", "SHORT", "3"),("PASAJES", "DOUBLE", "3"), ("VIATICOS", "SHORT", "3"),
                ("MOV_LOCAL", "SHORT", "3"),("MOV_ESPECIAL", "SHORT", "3")

                ]


    campos_SEDE = [
                ("CODSEDE","TEXT","2"),("SEDE_OPERATIVA","TEXT","50")
                ]

    campos_DEPARTAMENTO = [
                ("PK_DEPARTAMENTO","TEXT","2"),("CODDPTO","TEXT","2"),
                ("NOMBDEP","TEXT","100"),
                ]

    campos_PROVINCIA = [
        ("PK_PROVINCIA", "TEXT", "4"),
        ("CODDPTO", "TEXT", "2"),
        ("CODPROV", "TEXT", "2"),
        ("NOMBDEP", "TEXT", "100"),
        ("NOMBPROV", "TEXT", "100"),

    ]
    campos_DISTRITO = [
        ("PK_DISTRITO", "TEXT", "6"),
        ("COD_OPER","TEXT","2"),
        ("CODSEDE", "TEXT", "2"),
        ("CODDPTO", "TEXT", "2"),
        ("CODPROV", "TEXT", "2"),
        ("CODDIST", "TEXT", "2"),
        ("NOMBDEP", "TEXT", "100"),
        ("NOMBPROV", "TEXT", "100"),
        ("NOMBDIST", "TEXT", "100"),


    ]



    campos_ZONA = [
        ("UBIGEO", "TEXT", "6"), ("ZONA", "TEXT", "5"),
                    ]

    campos_DISTRITO = [
        ("UBIGEO", "TEXT", "6"),("DEPARTAMENTO", "TEXT", "50"), ("PROVINCIA", "TEXT", "50"), ("DISTRITO", "TEXT", "50")
    ]

    campos_TRACK = [("CODSEDE","TEXT","2"),("CODSUBSEDE","SHORT","3"),("UBIGEO", "TEXT", "6"),
                    ("SUP_VIA", "TEXT", "50")
                    ]


    featureClass = [
                    ["CCPP_URBANO_{}_{}".format(sede,subsede),"POINT",campos_CCPP_URBANO],
                    ["DEPARTAMENTO".format(), "POLYGON", campos_DEPARTAMENTO],
                    ["SEDE_OPERATIVA".format(), "POLYGON", campos_SEDE],
                    ["PROVINCIA".format(), "POLYGON", campos_PROVINCIA],
                    ["AES_{}_{}".format(sede, subsede), "POLYGON", campos_AES ],
                    ["TRACK_{}_{}".format(sede, subsede), "POLYLINE", campos_TRACK ],
                    ["HIDRO_{}_{}".format(sede, subsede), "POLYLINE", campos_HIDRO],
                    ["DISTRITO_{}_{}".format(sede, subsede), "POLYGON", campos_DISTRITO],
                    ["ZONAS_{}_{}".format(sede, subsede), "POLYGON", campos_ZONA],

                    ]

    for i in featureClass:
        fc_tmp = arcpy.CreateFeatureclass_management("in_memory", i[0], i[1], "#", "#", "#", arcpy.SpatialReference(4326))
        for n in i[2]:
            if n[1] == "TEXT":
                arcpy.AddField_management(fc_tmp, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE', 'NON_REQUIRED', '#')
            else:
                arcpy.AddField_management(fc_tmp, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')

        fc = arcpy.CreateFeatureclass_management(fdGenerales, i[0], i[1], fc_tmp, "#", "#", arcpy.SpatialReference(4326))

    rutaFD = '{}\{}\{}.gdb\Generales'.format(carpeta, nameFile, nameGDB)

    rutaGeodatabase = '{}\{}\{}.gdb'.format(carpeta, nameFile, nameGDB)

    return rutaGeodatabase

def importarFeatureClass(sede,subsede, rutaFD):
    conexionDB = conectionDB_arcpy()

    ccpp_urbano = arcpy.MakeQueryLayer_management(conexionDB, "CCPP_URBANO_{}_{}".format(sede, subsede),
                                            "SELECT * FROM {}.SDE.TB_CCPP_URBANO where CODSEDE = '{}' AND CODSUBSEDE = {} AND PRIORIDAD='01' ".format(
                                                DB_NAME, sede, subsede), 'OBJECTID', 'POINT', '4326',
                                            arcpy.SpatialReference(4326))

    departamento = arcpy.MakeQueryLayer_management(conexionDB, "DEPARTAMENTO",
                                                  "SELECT * FROM {db}.SDE.TB_DEPARTAMENTO WHERE CODDPTO IN (SELECT DISTINCT CODDPTO FROM {db}.SDE.TB_DISTRITO B WHERE b.CODSEDE ='{sede}' AND B.CODSUBSEDE ={subsede} )  ".format(
                                                      db=DB_NAME, sede=sede, subsede=subsede), 'OBJECTID', 'POLYGON', '4326',
                                                  arcpy.SpatialReference(4326))

    provincia = arcpy.MakeQueryLayer_management(conexionDB, "PROVINCIA",
                                                   "SELECT * FROM {db}.SDE.TB_PROVINCIA WHERE CODDPTO + CODPROV  IN (SELECT DISTINCT CODDPTO+CODPROV FROM {db}.SDE.TB_DISTRITO B WHERE B.CODSEDE ='{sede}' AND B.CODSUBSEDE ={subsede} )  ".format(
                                                       db=DB_NAME, sede=sede, subsede=subsede), 'OBJECTID',
                                                   'POLYGON', '4326',
                                                   arcpy.SpatialReference(4326))

    sede_operativa = arcpy.MakeQueryLayer_management(conexionDB, "SEDE_OPERATIVA",
                                                   " SELECT * FROM {db}.SDE.TB_SEDE_OPERATIVA WHERE CODSEDE ='{sede}' ".format(
                                                       db=DB_NAME, sede=sede), 'OBJECTID',
                                                   'POLYGON', '4326',
                                                   arcpy.SpatialReference(4326))

    #hidro = arcpy.MakeQueryLayer_management(conexionDB, "HIDRO_{}_{}".format(sede, subsede),"SELECT * FROM {}.SDE.TB_HIDRO where CODSEDE = '{}' ".format(DB_NAME, sede), 'OBJECTID_1')


    track = arcpy.MakeQueryLayer_management(conexionDB, "TRACK_{}_{}".format(sede, subsede),
                                            "SELECT * FROM {}.SDE.TB_TRACK where CODSEDE = '{}' ".format(
                                                DB_NAME, sede), 'OBJECTID', 'POLYLINE', '4326',
                                            arcpy.SpatialReference(4326))

    distritos = arcpy.MakeQueryLayer_management(conexionDB, "DISTRITO_{}_{}".format(sede, subsede),
                                            "SELECT * FROM {}.SDE.TB_DISTRITO where CODSEDE = '{}' AND CODSUBSEDE = {} AND COD_OPER='01' ".format(DB_NAME, sede, subsede), 'OBJECTID', 'POLYLINE', '4326',
                                            arcpy.SpatialReference(4326))


    zonas = arcpy.MakeQueryLayer_management(conexionDB, "ZONA_{}_{}".format(sede, subsede),
                                            "SELECT * FROM {}.SDE.TB_ZONA where CODSEDE = '{}' AND CODSUBSEDE = {} AND COD_OPER='01' ".format(
                                                DB_NAME, sede, subsede), 'OBJECTID', 'POLYLINE', '4326',
                                            arcpy.SpatialReference(4326))

    aes = arcpy.MakeQueryLayer_management(conexionDB, "AES_{}_{}".format(sede, subsede),
                                          "SELECT * FROM  {}.SDE.SEGM_U_AEU where CODSEDE = '{}' AND CODSUBSEDE = {} ".format(
                                              DB_NAME, sede, subsede), 'OBJECTID', 'POLYGON', '4326',
                                          arcpy.SpatialReference(4326))


    #arcpy.Append_management(hidro, r'{}\HIDRO_{}_{}'.format(rutaFD, sede, subsede),"NO_TEST")
    arcpy.Append_management(track, r'{}\TRACK_{}_{}'.format(rutaFD, sede, subsede), "NO_TEST")
    arcpy.Append_management(distritos, r'{}\DISTRITO_{}_{}'.format(rutaFD, sede, subsede), "NO_TEST")
    arcpy.Append_management(zonas, r'{}\ZONAS_{}_{}'.format(rutaFD, sede, subsede), "NO_TEST")
    arcpy.Append_management(aes, r'{}\AES_{}_{}'.format(rutaFD, sede,subsede), "NO_TEST")
    arcpy.Append_management(ccpp_urbano, r'{}\CCPP_URBANO_{}_{}'.format(rutaFD, sede, subsede), "NO_TEST")
    arcpy.Append_management(departamento, r'{}\DEPARTAMENTO'.format(rutaFD), "NO_TEST")
    arcpy.Append_management(provincia, r'{}\PROVINCIA'.format(rutaFD), "NO_TEST")
    arcpy.Append_management(sede_operativa, r'{}\SEDE_OPERATIVA'.format(rutaFD), "NO_TEST")

def iniciar(sede, subsede, carpeta):

    rutaGeodatabase = crearFileGDB(sede, subsede,carpeta)
    rutaFD = os.path.join( rutaGeodatabase,'Generales')
    importarFeatureClass(sede,subsede, rutaFD)
    arcpy.env.workspace = rutaGeodatabase
    arcpy.env.scratchWorkspace = rutaGeodatabase


    arcpy.SetParameterAsText(3, r'{}\HIDRO_{}_{}'.format(rutaFD, sede, subsede))
    arcpy.SetParameterAsText(4, r'{}\CCPP_URBANO_{}_{}'.format(rutaFD, sede, subsede))
    arcpy.SetParameterAsText(5, r'{}\AES_{}_{}'.format(rutaFD, sede, subsede))
    arcpy.SetParameterAsText(6, r'{}\SEDE_OPERATIVA'.format(rutaFD))
    arcpy.SetParameterAsText(7, r'{}\DEPARTAMENTO'.format(rutaFD))
    arcpy.SetParameterAsText(8, r'{}\PROVINCIA'.format(rutaFD))
    arcpy.SetParameterAsText(9, r'{}\DISTRITO_{}_{}'.format(rutaFD,sede,subsede))
    arcpy.SetParameterAsText(10, r'{}\ZONAS'.format(rutaFD))
    arcpy.SetParameterAsText(11, r'{}\TRACK_{}_{}'.format(rutaFD, sede, subsede))


    params = arcpy.GetParameterInfo()
    print params
    arcpy.AddWarning("params {}".format(params))
    for param in params:
        print param
        arcpy.AddWarning("param {}".format(param))

        if '{}'.format(param.name) == 'aes':
            param.symbology = lyrAe

        elif '{}'.format(param.name) == 'hidro':
            param.symbology = lyrHidro

        elif '{}'.format(param.name) == 'distrito':
            param.symbology = lyrDistrito

        elif '{}'.format(param.name) == 'zona':
            param.symbology = lyrZona

        elif '{}'.format(param.name) == 'track':
            param.symbology = lyrTrack

        elif '{}'.format(param.name) == 'ccpp_urbano':
            param.symbology = lyrCcppUrbano

        elif '{}'.format(param.name) == 'departamento':
            param.symbology = lyrDepartamento

        elif '{}'.format(param.name) == 'provincia':
            param.symbology = lyrProvincia

        elif '{}'.format(param.name) == 'sede_operativa':
            param.symbology = lyrSede
iniciar(sede, subsede, carpeta)