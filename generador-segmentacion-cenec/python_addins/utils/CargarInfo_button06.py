import arcpy
import pymssql

arcpy.env.overwriteOutput = True

agregarTablaRutas = arcpy.GetParameter(0)
agregarTablaCcppRutas = arcpy.GetParameter(1)

#arcpy.CreateDatabaseConnection_management()


def conectionGDB_arcpy(ip="172.18.1.93"):
    if arcpy.Exists("CPV_SEGMENTACION_GDB.sde") == False:
        arcpy.CreateDatabaseConnection_management("Database Connections",
                                                  'CPV_SEGMENTACION_GDB.sde',
                                                  'SQL_SERVER',
                                                  ip,
                                                  'DATABASE_AUTH',
                                                  'sde',
                                                  "$deDEs4Rr0lLo",
                                                  "#",
                                                  'CPV_SEGMENTACION_GDB',
                                                  "#",
                                                  '#',
                                                  '#',
                                                  "#")

    conexionGDB = r'Database Connections\CPV_SEGMENTACION_GDB.sde'
    return conexionGDB

def conectionDB_pymmsql(user_sde="us_arcgis_seg_2", password_sde="MBs0p0rt301", ip="172.18.1.93", nombre='CPV_SEGMENTACION'):
    conexion = pymssql.connect(ip, user_sde, password_sde, nombre)
    return conexion

def cargarTablaRutas(agregarTablaRutas, conexionGDB, ubigeo):
    conexion = conectionDB_pymmsql()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM CPV_SEGMENTACION_GDB.SDE.SEGM_R_RUTA WHERE UBIGEO = '{}'".format(ubigeo))
    conexion.commit()
    cursor.close()
    arcpy.Append_management(agregarTablaRutas, r'{}\CPV_SEGMENTACION_GDB.SDE.MODULO_SEGM_RURAL\CPV_SEGMENTACION_GDB.SDE.SEGM_R_RUTA'.format(conexionGDB), "NO_TEST")

def cargarTablaCcppRutas(agregarTablaCcppRutas, conexionGDB, ubigeo):
    conexion = conectionDB_pymmsql()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM CPV_SEGMENTACION_GDB.SDE.SEGM_R_CCPPRUTA WHERE UBIGEO = '{}'".format(ubigeo))
    conexion.commit()
    cursor.close()
    arcpy.Append_management(agregarTablaCcppRutas, r'{}\CPV_SEGMENTACION_GDB.SDE.MODULO_SEGM_RURAL\CPV_SEGMENTACION_GDB.SDE.SEGM_R_CCPPRUTA'.format(conexionGDB), "NO_TEST")

def asignarEstado(ubigeo):
    conexion = conectionDB_pymmsql()
    cursor = conexion.cursor()
    cursor.execute("UPDATE TB_MODULO_ASIGN_R SET ESTADO = 3 WHERE UBIGEO = '{}'".format(ubigeo))
    conexion.commit()
    cursor.close()

def capturaUbigeo(agregarTablaRutas):
    desc = arcpy.Describe(agregarTablaRutas)
    nombre = desc.basename
    ubigeo = nombre[16:22]
    return ubigeo


def cargarTablas(agregarTablaRutas, agregarTablaCcppRutas):
    ubigeo = capturaUbigeo(agregarTablaCcppRutas)
    arcpy.AddMessage(ubigeo)
    #try:
    conexionGDB = conectionGDB_arcpy()
    cargarTablaRutas(agregarTablaRutas, conexionGDB, ubigeo)
    cargarTablaCcppRutas(agregarTablaCcppRutas, conexionGDB, ubigeo)
    asignarEstado(ubigeo)
    arcpy.AddMessage("La carga se realizo con exito. \nPor favor espera la validacion del Jefe de equipo")
    #except:
    #e = sys.exc_info()[1]
    #arcpy.AddError(e.args[0])

# cargarTablas(agregarTablaRutas, agregarTablaCcppRutas)
arcpy.AddMessage("---------------------------------------------")
arcpy.AddMessage("---------------------------------------------")
arcpy.AddMessage("---------------------------------------------")
arcpy.AddMessage("Base de datos en mantenimiento")
arcpy.AddMessage("Espere las indicaciones de su jefe de equipo.")
arcpy.AddMessage("---------------------------------------------")
arcpy.AddMessage("---------------------------------------------")
arcpy.AddMessage("---------------------------------------------")