import arcpy
from conf import config
import pyodbc

def connect_arcpy():
    if arcpy.Exists(r"Database Connections\{}.sde".format(config.DB_NAME)) == False:
        arcpy.CreateDatabaseConnection_management("Database Connections",
                                                  "{}.sde".format(config.DB_NAME),
                                                  "SQL_SERVER",
                                                  config.HOST,
                                                  "DATABASE_AUTH",
                                                  config.USER,
                                                  config.PASSWORD,
                                                  "#",
                                                  "{}".format(config.DB_NAME),
                                                  "#",
                                                  "#",
                                                  "#",
                                                  "#")
    path_conexion = r"Database Connections\{}.sde".format(config.DB_NAME)
    return path_conexion

def connect_bd():
    cnxn = pyodbc.connect(
        'DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s'
        % (config.HOST, config.DB_NAME, config.USER, config.PASSWORD), autocommit=True)
    cursor = cnxn.cursor()
    return cnxn, cursor
