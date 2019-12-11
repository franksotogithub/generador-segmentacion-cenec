import sys
from utils.query import to_dict
from utils.listado_urbano import listado_ruta, listado_brigada , programacion_ruta
from bd import cnx
import itertools
from os import path ,remove , mkdir
from operator import itemgetter
import shutil
import arcpy
import expresiones_consulta_arcpy as expresion
from datetime import *
from conf import config
from programacion import crear_programacion_rutas ,crear_programacion_brigadas ,crear_etiquetas , crear_programacion_sedes
import math
from query import obtener_sedes

class ArchivosAnexosCENEC:

    def __init__(self,cod_oper,codsede,periodos):
        self.periodos = periodos
        self.conn, self.cursor = cnx.connect_bd()
        self.path_trabajo = config.PATH_TRABAJO
        self.operacion = self.obtener_operacion(cod_oper)
        self.path_programaciones = path.join(config.BASE_DIR_CROQUIS_LISTADO, self.operacion['DESCRIPCION'], 'programacion')
        self.cod_oper = cod_oper
        self.codsede = codsede
        self.tipo_formato = 1 if int(self.operacion['TIPO_FORMATO']) is None else int(self.operacion['TIPO_FORMATO'])

    def obtener_operacion(self,cod_oper='01'):
        query_operacion  = """
                        begin
                            select * from [SDE].[TB_OPERACION] 
                            where isnull(COD_OPER,'01')='{cod_oper}'                 
                        end
                """.format(cod_oper=cod_oper)

        operacion = to_dict(self.cursor.execute(query_operacion))
        return operacion[0]

    def obtener_emp_ruta_periodo(self, cod_oper, codsede='07'):

        query = """
        SELECT A.*,B.SEDE_OPERATIVA FROM sde.SEGM_RUTA_EMP_PERIODO A 
        INNER JOIN  sde.TB_SEDE_OPERATIVA B ON A.CODSEDE=B.CODSEDE  
        where A.COD_OPER='{cod_oper}' and A.CODSEDE = '{codsede}'
        --AND ISNULL(A.PROC_CROQUIS,0)=0 
        order by COD_OPER,CODSEDE,BRIGADA,RUTA,EMPADRONADOR DESC 
        """.format(cod_oper=cod_oper, codsede=codsede)

        empadronadores = to_dict(self.cursor.execute(query))
        return empadronadores

    def obtener_programacion_ruta(self, ruta):
        query_p = ''

        for count, p in enumerate(self.periodos):
            if count > 0:
                query_p = '{},{}'.format(query_p, p)
            else:
                query_p = '{}'.format(p)

        query = """  begin
                        SELECT b.DEPARTAMENTO,b.PROVINCIA,b.DISTRITO,SUBSTRING(CODCCPP,7,5)CODCCPP,b.NOMCCPP,a.* FROM SDE.SEGM_PROGRAMACION_RUTAS A
                        INNER JOIN TB_ZONA B ON A.UBIGEO + A.ZONA = B.UBIGEO+B.ZONA 
                        where A.codsede='{codsede}' and A.ruta ={ruta} and A.cod_oper='{cod_oper}' and a.periodo in ({periodos})
                        order by a.periodo,a.orden              
                     end
                            """.format(codsede=ruta["CODSEDE"], ruta=int(ruta["RUTA"]), cod_oper=ruta["COD_OPER"],
                                       periodos=query_p)

        empadronadores = to_dict(self.cursor.execute(query))
        return empadronadores

    def obtener_programacion_brigada(self, brigada):

        query_p = ''

        for count, p in enumerate(self.periodos):
            if count > 0:
                query_p = '{},{}'.format(query_p, p)
            else:
                query_p = '{}'.format(p)

        query = """  begin
                         SELECT b.DEPARTAMENTO,b.PROVINCIA,b.DISTRITO,SUBSTRING(CODCCPP,7,5)CODCCPP,b.NOMCCPP,a.* FROM SDE.SEGM_PROGRAMACION_BRIGADAS A
                         INNER JOIN TB_ZONA B ON A.UBIGEO+ A.ZONA = B.UBIGEO+B.ZONA 
                         where a.codsede='{codsede}' and a.brigada ={brigada} and a.cod_oper='{cod_oper}' and a.periodo in ({periodos})
                         order by a.periodo,a.orden              
                     end
                            """.format(codsede=brigada["CODSEDE"], brigada=int(brigada["BRIGADA"]),
                                       cod_oper=brigada["COD_OPER"], periodos=query_p)
        #print 'query emp>>',query
        empadronadores = to_dict(self.cursor.execute(query))

        return empadronadores

    def obtener_programacion_ruta_sede(self, sede):
        query_p = ''

        for count, p in enumerate(self.periodos):
            if count > 0:
                query_p = '{},{}'.format(query_p, p)
            else:
                query_p = '{}'.format(p)

        query = """  begin
                                 SELECT b.SEDE_OPERATIVA,b.DEPARTAMENTO,b.PROVINCIA,b.DISTRITO,SUBSTRING(CODCCPP,7,5)CODCCPP,b.NOMCCPP,a.*, 0 ADICIONAL FROM SDE.SEGM_PROGRAMACION_RUTAS A
                                 INNER JOIN TB_ZONA B ON A.UBIGEO+ A.ZONA = B.UBIGEO+B.ZONA
                                 where A.codsede='{codsede}'  and A.cod_oper='{cod_oper}' and A.periodo in ({periodos})
                                 order by a.brigada,a.ruta,a.periodo,a.orden                
                             end
                                    """.format(codsede=sede["CODSEDE"], cod_oper=sede["COD_OPER"], periodos=query_p)
        programacion = to_dict(self.cursor.execute(query))
        print 'query>>>', query
        return programacion

    def obtener_programacion_brigada_sede(self, sede):
        query = """  begin

                                 SELECT b.SEDE_OPERATIVA,b.DEPARTAMENTO,b.PROVINCIA,b.DISTRITO,SUBSTRING(CODCCPP,7,5)CODCCPP,b.NOMCCPP,a.*, 0 ADICIONAL FROM SDE.SEGM_PROGRAMACION_BRIGADAS A
                                 INNER JOIN TB_ZONA B ON A.UBIGEO+ A.ZONA = B.UBIGEO+B.ZONA 
                                 where a.codsede='{codsede}'  and a.cod_oper='{cod_oper}'
                                 order by a.brigada,a.ruta,a.periodo,a.orden 


                             end
                                    """.format(codsede=sede["CODSEDE"], cod_oper=sede["COD_OPER"])
        programacion = to_dict(self.cursor.execute(query))
        return programacion

    def procesar_generacion_programacion(self,brigada,manzanas_brigada,rutas_emp):

        prog_brigada = self.obtener_programacion_brigada(brigada)

        ######
        ####creando programacion de brigadas
        ######

        output_brigada = path.join(self.path_programaciones,
                                   '{cod_oper}-{codsede}-{brigada}.xlsx'.format(cod_oper=brigada['COD_OPER'],
                                                                                codsede=brigada['CODSEDE'],
                                                                                brigada=brigada['BRIGADA']))

        for p in prog_brigada:
            manzanas_prog = [e for e in manzanas_brigada if (p['PK_AEU'] == e['Z_AE'])]

            self.rellenando_datos_programacion(p,manzanas_prog,2)

        try:
            crear_programacion_brigadas([brigada, prog_brigada], output_brigada,self.tipo_formato)
        except:
            pass

        #########
        ##creando   programacion RUTAS
        ########
        for ruta_emp in rutas_emp:
            output = path.join(self.path_programaciones, '{cod_oper}-{codsede}-{brigada}-{ruta}-{emp}.xlsx'.format(
                                                              cod_oper = ruta_emp['COD_OPER'],
                                                              codsede=ruta_emp['CODSEDE'],
                                                              brigada=ruta_emp['BRIGADA'], ruta=ruta_emp['RUTA'] ,emp=ruta_emp['EMPADRONADOR']))


            prog = self.obtener_programacion_ruta(ruta_emp)
            manzanas_ruta_emp = [e for e in manzanas_brigada if (e['RUTA'] == ruta_emp['RUTA'])]

            for p in prog:
                manzanas_prog = [e for e in manzanas_ruta_emp if (p['PK_AEU'] == e['Z_AE'])]

                self.rellenando_datos_programacion(p, manzanas_prog,1)


            try:
                crear_programacion_rutas([ruta_emp, prog], output,tipo_formato=1)
            except:
                pass

    def obtener_rutas_manzanas_por_brigada(self, brigada):

        query_rutas_manzanas_por_brigada = """
                            begin

                                SELECT B.*, (B.MARCO_FIN + B.PUESTO) CANT_EST ,isnull(A.ORDEN,0)ORDEN FROM dbo.SEGM_U_RUTA_MANZANA B
                                left join [sde].[SEGM_PROGRAMACION_RUTAS] A ON A.PK_AEU = B.Z_AE and A.COD_OPER = B.COD_OPER
                                where B.CODSEDE = '{codsede}' AND B.BRIGADA ='{brigada}' AND B.COD_OPER = '{cod_oper}' 
                                ORDER BY B.BRIGADA,B.RUTA,B.PERIODO,A.ORDEN,B.UBIGEO,B.ZONA,B.FALSO_COD

                            end
                    """.format(codsede=brigada["CODSEDE"], brigada=brigada["BRIGADA"], cod_oper=brigada["COD_OPER"])
        #print  'query_rutas_manzanas_por_brigada>>>', query_rutas_manzanas_por_brigada
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas_por_brigada))
        return rutas_manzanas

    def is_none_zero(self,valor):
        r=0 if valor is None else valor
        return r

    def rellenando_datos_programacion(self,fila_prog,manzanas_prog,nivel = 1):
        if self.tipo_formato == 1:
            COSTO_VIATICOS = 120.0
            COSTO_MOV_LOCAL = 25.0
            COSTO_MOV_LOCAL_BRIGADA = 30.0
            COSTO_MOV_ESPECIAL = 50.0
        else:
            COSTO_VIATICOS = 180.0
            COSTO_MOV_LOCAL = 25.0
            COSTO_MOV_LOCAL_BRIGADA = 30.0
            COSTO_MOV_ESPECIAL = 50.0

        if len(manzanas_prog) > 1:
            fila_prog['MANZANAS'] = 'DEL {} AL {}'.format(manzanas_prog[0]['MZ'], manzanas_prog[-1]['MZ'])
        elif len(manzanas_prog) == 1:
            fila_prog['MANZANAS'] = manzanas_prog[0]['MZ']
        else:
            fila_prog['MANZANAS'] = ''


        periodo = int(fila_prog['PERIODO'])
        dias_trabajo = int(fila_prog['DIAS_TRABAJO'])
        dias_viaje = int(fila_prog['DIAS_VIAJE'])
        dias_descanso = int(fila_prog['DIAS_DESCANSO'])

        if nivel ==1:
            fila_prog['TOTAL_MOV_LOCAL'] =  self.is_none_zero((dias_trabajo * COSTO_MOV_LOCAL) * int(fila_prog['MOV_LOCAL']))
        else:
            fila_prog['TOTAL_MOV_LOCAL'] = self.is_none_zero(
                (dias_trabajo * COSTO_MOV_LOCAL_BRIGADA) * int(fila_prog['MOV_LOCAL']))


        fila_prog['TOTAL_MOV_ESPECIAL'] = self.is_none_zero((dias_trabajo * COSTO_MOV_ESPECIAL) * int(fila_prog['MOV_ESPECIAL']))
        fila_prog['TOTAL_GENERAL'] = 0
        fila_prog['TOTAL_VIATICOS'] = 0

        if periodo in [1, 3, 5, 4,6]:
            fila_prog['TOTAL_VIATICOS'] = self.is_none_zero(((dias_viaje + dias_trabajo) * COSTO_VIATICOS)  * int(fila_prog['VIATICOS']))

        else:
            fila_prog['TOTAL_VIATICOS'] = self.is_none_zero(((dias_viaje + dias_trabajo + dias_descanso) * COSTO_VIATICOS) * int(fila_prog['VIATICOS']))

        if int(fila_prog['VIATICOS']) > 0:
            fila_prog['TOTAL_GENERAL'] = self.is_none_zero(fila_prog['TOTAL_VIATICOS'] + float(fila_prog['PASAJES']))

        elif int(fila_prog['MOV_LOCAL']) > 0:
            fila_prog['TOTAL_GENERAL'] = self.is_none_zero(fila_prog['TOTAL_MOV_LOCAL'])

        elif int(fila_prog['MOV_ESPECIAL']) > 0:
            fila_prog['TOTAL_GENERAL'] = self.is_none_zero(fila_prog['TOTAL_MOV_ESPECIAL'])

        return fila_prog


    def procesar_anexos(self):

        emp_ruta_periodo = self.obtener_emp_ruta_periodo(self.cod_oper,self.codsede)
        brigadas_periodo = [
            {'COD_OPER': e[0], 'CODSEDE': e[1], 'BRIGADA': e[2], 'PERIODO': e[3], 'SEDE_OPERATIVA': e[4]} for e in list(
                set((d['COD_OPER'], d['CODSEDE'], d['BRIGADA'], d['PERIODO'], d['SEDE_OPERATIVA']) for d in
                    emp_ruta_periodo))]

        brigadas  =  [{'COD_OPER':e[0],'CODSEDE':e[1],'BRIGADA':e[2] ,'SEDE_OPERATIVA':e[3] }
                      for e in  list(set(( d['COD_OPER'],d['CODSEDE'],d['BRIGADA'] ,d['SEDE_OPERATIVA']) for d in brigadas_periodo))]

        #if (programacion == 1 and len(brigadas) > 0):
        for brigada in brigadas:
            brigadas_periodo_temp = [e for e in brigadas_periodo if
                                         (e['CODSEDE'] == brigada['CODSEDE'] and e['BRIGADA'] == brigada['BRIGADA'] and
                                          int(e['PERIODO']) in self.periodos
                                          )]
            manzanas_brigada = self.obtener_rutas_manzanas_por_brigada(brigada)

            rutas_emp = [{'COD_OPER': e[0], 'CODSEDE': e[1], 'BRIGADA': e[2], 'RUTA': e[3], 'SEDE_OPERATIVA': e[4],
                              'EMPADRONADOR': e[5]}
                             for e in list(set((d['COD_OPER'], d['CODSEDE'], d['BRIGADA'], d['RUTA'], d['SEDE_OPERATIVA'], d['EMPADRONADOR']) for d in
                                emp_ruta_periodo if (d['COD_OPER'] == brigada['COD_OPER'] and d['CODSEDE'] == brigada['CODSEDE']
                                    and d['BRIGADA'] == brigada['BRIGADA'] and int(d['PERIODO']) in self.periodos)))]

            self.procesar_generacion_programacion(brigada, manzanas_brigada, rutas_emp)

cod_oper='01'
conn, cursor = cnx.connect_bd()
sedes=obtener_sedes(cursor,cod_oper)
periodos = [1,2,3]


for sede in sedes:
    a=ArchivosAnexosCENEC(cod_oper,sede['codsede'],periodos)
    a.procesar_anexos()

