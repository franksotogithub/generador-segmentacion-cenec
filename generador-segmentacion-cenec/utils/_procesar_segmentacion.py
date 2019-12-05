# -*- coding: latin-1 -*-
import subprocess
from bd import cnx
from query import actualizar_flag_proc_segm ,actualizar_flag_proc_segm_distrito,obtener_zonas ,obtener_distritos
import sys
from datetime import *
import os
import socket
from conf import config
#
#
equipo=socket.gethostname()
cnxn, cursor=cnx.connect_bd()
lista_dist = [1]

while len(lista_dist) > 0:
    #lista_zonas = obtener_zonas(cursor,cnxn,cant_zonas=1)
    lista_dist = obtener_distritos(cursor, cnxn)
    if len(lista_dist) > 0:
        for el in lista_dist:
            ubigeo = el['UBIGEO']
            proceso = subprocess.Popen("python segmentacion.py {}".format(ubigeo), shell=True,stderr=subprocess.PIPE)
            errores = proceso.stderr.read()
            print errores
            e=errores.split('\n')[-1]
            if len(errores) > 0:
                print 'algo salido mal'
                actualizar_flag_proc_segm_distrito(cursor,cnxn,ubigeo, flag=3, equipo=equipo, error=e)
            else:
                print 'nada salio mal'
                actualizar_flag_proc_segm_distrito(cursor,cnxn,ubigeo, flag=1, equipo=equipo)


#for el in range(1000):
#    lista_zonas = obtener_zonas(cursor,cnxn,cant_zonas=1)
#    if len(lista_zonas)>0:
#        for el in lista_zonas:
#            ubigeo = el['UBIGEO']
#            zona = el['ZONA']
#            proceso = subprocess.Popen("python segmentacion.py {} {}".format(ubigeo, zona), shell=True,stderr=subprocess.PIPE)
#            errores = proceso.stderr.read()
#            e=errores.split('\n')[-1]
#            if len(e) > 0:
#                print 'algo salido mal'
#                actualizar_flag_proc_segm(cursor,cnxn,ubigeo, zona, flag=3, equipo=equipo, error=e)
#            else:
#                print 'nada salio mal'
#                actualizar_flag_proc_segm(cursor,cnxn,ubigeo, zona, flag=1, equipo=equipo)
#    else:
#        break

