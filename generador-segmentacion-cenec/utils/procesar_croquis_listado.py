# -*- coding: latin-1 -*-
import subprocess
from bd import cnx
from query import actualizar_flag_proc_segm ,actualizar_flag_proc_segm_distrito,\
    obtener_zonas ,obtener_distritos, obtener_sedes
import sys
from datetime import *
import os
import socket
from conf import config
#


equipo=socket.gethostname()
cnxn, cursor=cnx.connect_bd()
lista_dist = [1]

COD_OPER = '90'
PROGRAMACION = 1
IMPORTAR_CAPAS = 1
PROCESAR_CROQUIS = 1
PROCESAR_LISTA_SEDE  = 1
PROCESAR_ETIQUETAS  = 1
sedes = obtener_sedes(cursor,cod_oper=COD_OPER)


for s in sedes:
    print s
    proceso = subprocess.Popen("c:\Python27\ArcGIS10.3\python.exe croquis_listado.py {cod_oper} {codsede} {programacion} {importar_capas} {procesar_croquis} {procesar_lista_sede} {procesar_et}".format(cod_oper=COD_OPER,codsede=s['codsede'], programacion=PROGRAMACION ,importar_capas=IMPORTAR_CAPAS ,procesar_croquis=PROCESAR_CROQUIS ,procesar_lista_sede=PROCESAR_LISTA_SEDE  ,procesar_et = PROCESAR_ETIQUETAS ), shell=True,stderr=subprocess.PIPE)
    errores = proceso.stderr.read()
    print errores




