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


arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

COD_OPER='{}'.format(sys.argv[1])
CODSEDE='{}'.format(sys.argv[2])
PROGRAMACION = int(sys.argv[3])
IMPORTAR_CAPAS = int(sys.argv[4])
PROCESAR_CROQUIS =int (sys.argv[5])
PROCESAR_LISTA_SEDE =int (sys.argv[6])
PROCESAR_ETIQUETAS = 0
PERIODOS = [1,2,3]

class CroquisListadoCENEC:
    zonas = []
    def __init__(self):
        self.conn, self.cursor = cnx.connect_bd()
        self.list_aeu_manzanas = []
        self.list_aeu = []
        self.list_aeu_manzanas_final = []
        self.list_aeu_final = []
        self.path_trabajo = config.PATH_TRABAJO
        self.path_aeu = path.join(self.path_trabajo, 'aeu')
        self.rutas = []
        self.rutas_manzanas = []
        self.path_croquis = config.PATH_CROQUIS
        self.path_listado = config.PATH_LISTADO
        self.path_programaciones = config.PATH_PROGRAMACIONES
        self.path_croquis_listado = config.PATH_CROQUIS_LISTADO
        self.path_kmz=config.PATH_KMZ

        self.path_plantilla_croquis_empadronador = path.join(config.PATH_PLANTILLA_CROQUIS, 'croquis_empadronador.mxd')
        self.path_plantilla_croquis_empadronador_a2 = path.join(config.PATH_PLANTILLA_CROQUIS, 'croquis_empadronador_a2.mxd')
        self.path_plantilla_croquis_empadronador_v = path.join(config.PATH_PLANTILLA_CROQUIS,
                                                                'croquis_empadronador_vertical.mxd')
        self.path_plantilla_croquis_brigada = path.join(config.PATH_PLANTILLA_CROQUIS, 'croquis_brigada.mxd')
        self.path_plantilla_croquis_brigada_a2 = path.join(config.PATH_PLANTILLA_CROQUIS, 'croquis_brigada_a2.mxd')
        self.path_plantilla_croquis_brigada_v = path.join(config.PATH_PLANTILLA_CROQUIS, 'croquis_brigada_vertical.mxd')
        self.path_plantilla_kmz_mxd = path.join(config.PATH_PLANTILLA_CROQUIS, 'plantilla_kmz.mxd')
        self.centroides = []
        self.periodos = PERIODOS

    def importar_capas(self, zonas,cod_oper='01'):
        #print 'zonas>>>',zonas
        arcpy.env.overwriteOutput = True
        path_conexion = cnx.connect_arcpy()
        arcpy.env.workspace = path_conexion
        data = []
        for zona in zonas:
            data.append([zona['UBIGEO'], zona['ZONA']])

        where_zona = expresion.expresion(data, ['UBIGEO', 'ZONA'])
        where_ubigeo = expresion.expresion(data, ['UBIGEO'])

        for el in data:
            if (el[0][:4] == '1501'):
                where_ubigeo = """ (UBIGEO LIKE '1501%') OR ({})""".format(where_ubigeo)
                break

        if cod_oper=='99':
            where_ubigeo = "({})  ".format(where_ubigeo)
            where_zona = "({}) ".format(where_zona)
        else:
            where_ubigeo = "({}) ".format(where_ubigeo)
            where_zona = "({})  ".format(where_zona)

        list_capas = [
            ["{}.SDE.TB_MANZANA".format(config.DB_NAME), "tb_manzana", 2],
            ["{}.SDE.TB_SITIO_INTERES".format(config.DB_NAME), "tb_sitios_interes", 2],
            ["{}.SDE.TB_ZONA".format(config.DB_NAME), "tb_zona", 1],
            #["{}.DBO.TB_PUNTO_INICIO".format(config.DB_NAME), "tb_punto_inicio", 1],
            ["{}.SDE.TB_FRENTES".format(config.DB_NAME), "tb_frentes", 1],
            ["{}.SDE.TRABAJO_EJE_VIAL".format(config.DB_NAME), "tb_eje_vial", 2],
            ["{}.SDE.TB_HIDRO".format(config.DB_NAME), "tb_hidro", 2],
            ["{}.SDE.TB_CN".format(config.DB_NAME), "tb_cn", 2],
            ["{}.SDE.TB_TRACK".format(config.DB_NAME), "tb_track", 2],

        ]

        ## 1 exportacion de datos a nivel de zona, 2 exportacion a nivel de distrito

        for i, capa in enumerate(list_capas):
            if (capa[2] == 1):
                where = where_zona
            else:
                where = where_ubigeo

            print 'where>>>',where
            x = arcpy.MakeQueryLayer_management(path_conexion, 'capa{}'.format(i),
                                                "select * from {} where  {}  ".format(capa[0], where))

            temp = arcpy.CopyFeatures_management(x, '{}/{}'.format(self.path_trabajo, capa[1]))

    def obtener_operacion(self,cod_oper='01'):
        query_operacion  = """
                        begin
                            select * from [SDE].[TB_OPERACION] 
                            where isnull(COD_OPER,'01')='{cod_oper}'                 
                        end
                """.format(cod_oper=cod_oper)

        operacion = to_dict(self.cursor.execute(query_operacion))
        return operacion[0]

    def obtener_brigadas(self,cod_oper='01',codsede='07'):
        query_brigadas = """
                begin
                    
                    select * from [dbo].[SEGM_U_BRIGADA] 
                    where isnull(COD_OPER,'01')='{cod_oper}'  AND CODSEDE ='{codsede}'
                    --AND ISNULL(PROC_CROQUIS,0)=0
                    
                    --update a
					--set  a.proc_croquis = 1 
					--from dbo.SEGM_U_brigada a
					--where isnull(COD_OPER,'01')='{cod_oper}'  AND CODSEDE ='{codsede}'
                    --AND ISNULL(PROC_CROQUIS,0)=0
                                    
                end
        """.format(cod_oper=cod_oper,codsede=codsede)

        brigadas = to_dict(self.cursor.execute(query_brigadas))
        return brigadas

    def obtener_rutas(self, brigada):
        query_rutas = """
                begin
                    select * from [dbo].[SEGM_U_RUTA]
                    where CODSEDE = '{codsede}' AND BRIGADA ='{brigada}' AND COD_OPER ='{cod_oper}' 
                    ORDER BY CODSEDE,RUTA 
                end
        """.format(codsede=brigada["CODSEDE"], brigada=brigada["BRIGADA"],cod_oper=brigada["COD_OPER"])
        #print 'query_rutas>>>',query_rutas
        rutas = to_dict(self.cursor.execute(query_rutas))
        return rutas

    def obtener_programacion_ruta(self,ruta):

        query = """  begin
                        SELECT b.DEPARTAMENTO,b.PROVINCIA,b.DISTRITO,SUBSTRING(CODCCPP,7,5)CODCCPP,b.NOMCCPP,a.* FROM SDE.SEGM_PROGRAMACION_RUTAS A
                        INNER JOIN TB_ZONA B ON A.UBIGEO+ A.ZONA = B.UBIGEO+B.ZONA
                         where A.codsede='{codsede}' and A.ruta ={ruta} and A.cod_oper='{cod_oper}'
                         order by a.periodo,a.orden              
                     end
                            """.format(codsede=ruta["CODSEDE"], ruta=int(ruta["RUTA"]), cod_oper=ruta["COD_OPER"])

        #print 'obtener_emp_por_ruta>>>', query
        empadronadores = to_dict(self.cursor.execute(query))
        return empadronadores

    def obtener_programacion_brigada(self,brigada):

        query_p = ''

        for count,p in enumerate(self.periodos):
            if count>0:
                query_p = '{},{}'.format(query_p, p)
            else:
                query_p = '{}'.format(p)


        query = """  begin
                         SELECT b.DEPARTAMENTO,b.PROVINCIA,b.DISTRITO,SUBSTRING(CODCCPP,7,5)CODCCPP,b.NOMCCPP,a.* FROM SDE.SEGM_PROGRAMACION_BRIGADAS A
                         INNER JOIN TB_ZONA B ON A.UBIGEO+ A.ZONA = B.UBIGEO+B.ZONA
                         where a.codsede='{codsede}' and a.brigada ={brigada} and a.cod_oper='{cod_oper}' and a.periodo in ({periodos})
                         order by a.periodo,a.orden              
                     end
                            """.format(codsede=brigada["CODSEDE"],brigada=int(brigada["BRIGADA"]), cod_oper=brigada["COD_OPER"], periodos = query_p)

        empadronadores = to_dict(self.cursor.execute(query))

        return empadronadores

    def obtener_programacion_ruta_sede(self,sede):
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
                                    """.format(codsede=sede["CODSEDE"],cod_oper=sede["COD_OPER"], periodos = query_p)
        programacion = to_dict(self.cursor.execute(query))
        print 'query>>>',query
        return programacion

    def obtener_programacion_brigada_sede(self,sede):
        query = """  begin
                                 
                                 SELECT b.SEDE_OPERATIVA,b.DEPARTAMENTO,b.PROVINCIA,b.DISTRITO,SUBSTRING(CODCCPP,7,5)CODCCPP,b.NOMCCPP,a.*, 0 ADICIONAL FROM SDE.SEGM_PROGRAMACION_BRIGADAS A
                                 INNER JOIN TB_ZONA B ON A.UBIGEO+ A.ZONA = B.UBIGEO+B.ZONA
                                 where a.codsede='{codsede}'  and a.cod_oper='{cod_oper}'
                                 order by a.brigada,a.ruta,a.periodo,a.orden 
                                 
                                 
                                 
                                              
                             end
                                    """.format(codsede=sede["CODSEDE"],cod_oper=sede["COD_OPER"])
        programacion = to_dict(self.cursor.execute(query))
        return programacion



    #def obtener_emp_ruta_periodo(self,ruta):
    #    query = """  begin
    #                                    SELECT * FROM sde.SEGM_RUTA_EMP_PERIODO
    #                                    where CODSEDE = '{codsede}' AND RUTA ='{ruta}' AND COD_OPER='{cod_oper}'
    #                                    order by CODSEDE,RUTA,EMP
    #                 end
    #                        """.format(codsede=ruta["CODSEDE"], ruta=ruta["RUTA"], cod_oper=ruta["COD_OPER"])
    #    print 'obtener_emp_por_ruta>>>', query
    #    empadronadores = to_dict(self.cursor.execute(query))
    #    return empadronadores

    def obtener_emp_ruta_periodo(self,cod_oper,codsede='07'):
        query = """  begin
                                        SELECT A.*,B.SEDE_OPERATIVA FROM sde.SEGM_RUTA_EMP_PERIODO A 
                                        
                                        INNER JOIN  sde.TB_SEDE_OPERATIVA B ON A.CODSEDE=B.CODSEDE  
                                        where A.COD_OPER='{cod_oper}' and A.CODSEDE = '{codsede}'
                                        AND ISNULL(A.PROC_CROQUIS,0)=0 
                                        order by COD_OPER,CODSEDE,BRIGADA,RUTA,EMPADRONADOR DESC 
                                            
                                        
                                        update a
                                        set  a.proc_croquis = 1 
                                        from sde.SEGM_RUTA_EMP_PERIODO a
                                        where a.COD_OPER='{cod_oper}' and a.CODSEDE = '{codsede}'
                                        AND ISNULL(a.PROC_CROQUIS,0)=0
                                        
                     end
                            """.format(cod_oper=cod_oper,codsede=codsede)
        #print 'obtener_emp_por_ruta>>>', query
        empadronadores = to_dict(self.cursor.execute(query))
        return empadronadores

    def obtener_emp_por_ruta(self, ruta):
        query= """
                            begin
                                SELECT *  FROM dbo.SEGM_U_EMPADRONADOR   
                                where CODSEDE = '{codsede}' AND RUTA ='{ruta}' AND COD_OPER='{cod_oper}'
                                order by CODSEDE,RUTA,EMP
                            end
                    """.format(codsede=ruta["CODSEDE"], ruta=ruta["RUTA"] , cod_oper=ruta["COD_OPER"])
        #print 'obtener_emp_por_ruta>>>',query
        empadronadores = to_dict(self.cursor.execute(query))
        return empadronadores


    def obtener_rutas_manzanas_por_brigada(self, brigada):

        query_rutas_manzanas_por_brigada = """
                            begin
                                
                                SELECT B.*, (B.MARCO_FIN + B.PUESTO) CANT_EST ,isnull(A.ORDEN,0)ORDEN FROM dbo.SEGM_U_RUTA_MANZANA B
                                left join [sde].[SEGM_PROGRAMACION_RUTAS] A ON A.PK_AEU = B.Z_AE
                                where B.CODSEDE = '{codsede}' AND B.BRIGADA ='{brigada}' AND B.COD_OPER = '{cod_oper}' 
                                ORDER BY B.BRIGADA,B.RUTA,B.PERIODO,A.ORDEN,B.UBIGEO,B.ZONA,B.FALSO_COD
                                
                            end
                    """.format(codsede=brigada["CODSEDE"], brigada=brigada["BRIGADA"],cod_oper = brigada["COD_OPER"] )
        print  'query_rutas_manzanas_por_brigada>>>', query_rutas_manzanas_por_brigada
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas_por_brigada))
        return rutas_manzanas

    def obtener_rutas_manzanas_por_sede(self, sede):

        query_rutas_manzanas_por_brigada = """
                            begin

                                SELECT B.*, (B.MARCO_FIN + B.PUESTO) CANT_EST ,isnull(A.ORDEN,0)ORDEN FROM dbo.SEGM_U_RUTA_MANZANA B
                                left join [sde].[SEGM_PROGRAMACION_RUTAS] A ON A.PK_AEU = B.Z_AE

                                where B.CODSEDE = '{codsede}' AND B.COD_OPER = '{cod_oper}' 
                                ORDER BY B.BRIGADA,B.RUTA,B.PERIODO,A.ORDEN,B.UBIGEO,B.ZONA,B.FALSO_COD

                            end
                    """.format(codsede=sede["CODSEDE"],  cod_oper=sede["COD_OPER"])
        print  'query_rutas_manzanas_por_brigada>>>', query_rutas_manzanas_por_brigada
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas_por_brigada))
        return rutas_manzanas

    def obtener_programacion_rutas_por_sede(self, sede):

        query_rutas_manzanas_por_brigada = """
                            begin

                                SELECT B.*, (B.MARCO_FIN + B.PUESTO) CANT_EST ,isnull(A.ORDEN,0)ORDEN FROM dbo.SEGM_U_RUTA_MANZANA B
                                left join [sde].[SEGM_PROGRAMACION_RUTAS] A ON A.PK_AEU = B.Z_AE

                                where B.CODSEDE = '{codsede}' AND B.COD_OPER = '{cod_oper}' 
                                ORDER BY B.PERIODO,A.ORDEN,B.UBIGEO,B.ZONA,B.FALSO_COD

                            end
                    """.format(codsede=sede["CODSEDE"],  cod_oper=brigada["COD_OPER"])
        prog_rutas = to_dict(self.cursor.execute(query_rutas_manzanas_por_brigada))
        return prog_rutas

    def obtener_programacion_brigadas_por_sede(self, sede):

        query_rutas_manzanas_por_brigada = """
                            begin

                                SELECT B.*, (B.MARCO_FIN + B.PUESTO) CANT_EST ,isnull(A.ORDEN,0)ORDEN FROM dbo.SEGM_U_RUTA_MANZANA B
                                left join [sde].[SEGM_PROGRAMACION_RUTAS] A ON A.PK_AEU = B.Z_AE

                                where B.CODSEDE = '{codsede}' AND B.COD_OPER = '{cod_oper}' 
                                ORDER BY B.PERIODO,A.ORDEN,B.UBIGEO,B.ZONA,B.FALSO_COD

                            end
                    """.format(codsede=sede["CODSEDE"],  cod_oper=brigada["COD_OPER"])
        prog_rutas = to_dict(self.cursor.execute(query_rutas_manzanas_por_brigada))
        return prog_rutas

    def obtener_rutas_manzanas(self, ruta):

        query_rutas_manzanas = """
                            begin

                                SELECT B.*, (B.MARCO_FIN + B.PUESTO) CANT_EST ,isnull(A.ORDEN,0) ORDEN FROM SDE.SEGM_U_RUTA_MANZANA B
                                left join [sde].[SEGM_PROGRAMACION_RUTAS] A ON A.PK_AEU = B.Z_AE
                                
                                where B.CODSEDE = '{codsede}' AND B.RUTA ='{ruta}' AND B.COD_OPER = '{cod_oper}' AND B.PERIODO = {periodo}
                                ORDER BY B.PERIODO,A.ORDEN,B.UBIGEO,B.ZONA,B.FALSO_COD
                            end
                    """.format(codsede=ruta["CODSEDE"], ruta=ruta["RUTA"], cod_oper=ruta["COD_OPER"],
                               periodo=ruta["PERIODO"])
        #print 'query_rutas_manzanas>>>', query_rutas_manzanas
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas))
        return rutas_manzanas

    def rellenando_datos_programacion(self,fila_prog,manzanas_prog):
        COSTO_VIATICOS = 120.0
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

        fila_prog['TOTAL_MOV_LOCAL'] = (dias_trabajo * COSTO_MOV_LOCAL_BRIGADA) * int(fila_prog['MOV_LOCAL'])
        fila_prog['TOTAL_MOV_ESPECIAL'] = (dias_trabajo * COSTO_MOV_ESPECIAL) * int(fila_prog['MOV_ESPECIAL'])

        if periodo in [1, 3, 5, 6]:
            fila_prog['TOTAL_VIATICOS'] = ((dias_viaje + dias_trabajo) * COSTO_VIATICOS) * int(fila_prog['VIATICOS'])
        else:
            fila_prog['TOTAL_VIATICOS'] = ((dias_viaje + dias_trabajo + dias_descanso) * COSTO_VIATICOS) * int(fila_prog['VIATICOS'])

        if int(fila_prog['VIATICOS']) > 0:
            fila_prog['TOTAL_GENERAL'] = fila_prog['TOTAL_VIATICOS'] + float(fila_prog['PASAJES'])

        elif int(fila_prog['MOV_LOCAL']) > 0:
            fila_prog['TOTAL_GENERAL'] = fila_prog['TOTAL_MOV_LOCAL']

        elif int(fila_prog['MOV_ESPECIAL']) > 0:
            fila_prog['TOTAL_GENERAL'] = fila_prog['TOTAL_MOV_ESPECIAL']

        return fila_prog




    def procesar_generacion_programacion(self,brigada,manzanas_brigada,rutas_emp):
        COSTO_VIATICOS = 120.0
        COSTO_MOV_LOCAL = 25.0
        COSTO_MOV_LOCAL_BRIGADA = 30.0
        COSTO_MOV_ESPECIAL = 50.0


        prog_brigada = self.obtener_programacion_brigada(brigada)

        ######
        ####creando programacion de brigadas
        ######
        for p in prog_brigada:
            manzanas_prog = [e for e in manzanas_brigada if (p['PK_AEU'] == e['Z_AE'])]

            output_brigada = path.join(self.path_programaciones, '{cod_oper}-{codsede}-{brigada}.xlsx'.format( cod_oper = brigada['COD_OPER'],
                                                              codsede=brigada['CODSEDE'],
                                                              brigada=brigada['BRIGADA']))

            self.rellenando_datos_programacion(p,manzanas_prog)




        crear_programacion_brigadas([brigada, prog_brigada], output_brigada)


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

                self.rellenando_datos_programacion(p, manzanas_prog)



            crear_programacion_rutas([ruta_emp, prog], output)


    def procesar_etiquetas(self,data):
        brigada =data[0]
        output_brigada = path.join(self.path_etiquetas,
                                   '{cod_oper}{periodo}{codsede}{brigada}.xlsx'.format(cod_oper = brigada['COD_OPER'],
                                                                                codsede = brigada['CODSEDE'],
                                                                                periodo = brigada['PERIODO'],
                                                                                brigada=brigada['BRIGADA']))
        name,format =split(output_brigada,'.')
        pdf = '{}.pdf'.format(name)
        crear_etiquetas(data, output_brigada)
        return pdf

    def procesar_programacion_sedes (self,sede):
        output_sede = path.join(self.path_programaciones, '{cod_oper}-{codsede}-rutas.xlsx'.format(
            cod_oper=sede['COD_OPER'],
            codsede=sede['CODSEDE'],
        ))

        output_sede_b = path.join(self.path_programaciones, '{cod_oper}-{codsede}-brigadas.xlsx'.format(
            cod_oper=sede['COD_OPER'],
            codsede=sede['CODSEDE'],
        ))

        manzanas_sede = self.obtener_rutas_manzanas_por_sede(sede)
        programacion = self.obtener_programacion_ruta_sede(sede)

        for p in programacion:
            manzanas_prog = [e for e in manzanas_sede if (p['PK_AEU'] == e['Z_AE'])]
            self.rellenando_datos_programacion(p, manzanas_prog)


        programacion_b = self.obtener_programacion_brigada_sede(sede)

        for p in programacion_b:
            manzanas_prog = [e for e in manzanas_sede if (p['PK_AEU'] == e['Z_AE'])]
            self.rellenando_datos_programacion(p, manzanas_prog)


        sede['SEDE_OPERATIVA'] = programacion[0]['SEDE_OPERATIVA']




        crear_programacion_sedes([sede, programacion], output_sede)
        crear_programacion_sedes([sede, programacion_b], output_sede_b)




    def procesar_croquis_listado(self,cod_oper='01',codsede='07',programacion=1,importar_capas=1,procesar_croquis=1,procesar_lista_sede=1,procesar_etiquetas=1):
        operacion=self.obtener_operacion(cod_oper)

        self.path_base = path.join(config.BASE_DIR_CROQUIS_LISTADO,operacion['DESCRIPCION'])
        self.path_croquis_listado_ini = path.join(config.BASE_DIR_CROQUIS_LISTADO,operacion['DESCRIPCION'], r'croquis_listado')
        self.path_listado = path.join(config.BASE_DIR_CROQUIS_LISTADO,operacion['DESCRIPCION'], r'listado')
        self.path_croquis = path.join(config.BASE_DIR_CROQUIS_LISTADO, operacion['DESCRIPCION'],r'croquis')
        self.path_kmz = path.join(config.BASE_DIR_CROQUIS_LISTADO, operacion['DESCRIPCION'], 'kmz')
        self.path_programaciones = path.join(config.BASE_DIR_CROQUIS_LISTADO, operacion['DESCRIPCION'], 'programacion')
        self.path_etiquetas = path.join(config.BASE_DIR_CROQUIS_LISTADO, operacion['DESCRIPCION'], 'etiquetas')
        self.path_croquis_listado = path.join(self.path_croquis_listado_ini, codsede)
        self.path_mxd = path.join(config.BASE_DIR_CROQUIS_LISTADO, operacion['DESCRIPCION'], 'mxd')

        carpetas  = [self.path_base,self.path_croquis_listado_ini,self.path_listado,self.path_croquis ,self.path_kmz,
                     self.path_programaciones,self.path_etiquetas,self.path_croquis_listado ,self.path_mxd]

        for carpeta in carpetas:
            if not (path.exists(carpeta)):
                mkdir(carpeta)

        zonas = []
        brigada_out_etiquetas =[]


        emp_ruta_periodo = self.obtener_emp_ruta_periodo(cod_oper=cod_oper,codsede=codsede)

        brigadas_periodo = [{'COD_OPER':e[0],'CODSEDE':e[1],'BRIGADA':e[2],'PERIODO':e[3] ,'SEDE_OPERATIVA':e[4] }  for e in  list(set(( d['COD_OPER'],d['CODSEDE'],d['BRIGADA'] ,d['PERIODO'],d['SEDE_OPERATIVA']) for d in emp_ruta_periodo))]

        rutas_periodo =[ {'COD_OPER': e[0], 'CODSEDE': e[1], 'BRIGADA': e[2],'RUTA':e[3],'PERIODO':e[4],'SEDE_OPERATIVA':e[5]}
            for e in list(set((d['COD_OPER'], d['CODSEDE'], d['BRIGADA'],d['RUTA'] , d['PERIODO']  ,d['SEDE_OPERATIVA']) for d in emp_ruta_periodo))]

        brigadas  =  [{'COD_OPER':e[0],'CODSEDE':e[1],'BRIGADA':e[2] ,'SEDE_OPERATIVA':e[3] }  for e in  list(set(( d['COD_OPER'],d['CODSEDE'],d['BRIGADA'] ,d['SEDE_OPERATIVA']) for d in brigadas_periodo))]

        for brigada in brigadas:
            manzanas_brigada = self.obtener_rutas_manzanas_por_brigada(brigada)
            zonas = zonas + [{'UBIGEO': e[0], 'ZONA': e[1]} for e in
                                list(set((d['UBIGEO'], d['ZONA']) for d in manzanas_brigada))]

        ##############procesando lista de sedes operativas###########


        if (procesar_lista_sede == 1 ):
            sede = {'COD_OPER':cod_oper,'CODSEDE': codsede}
            self.procesar_programacion_sedes(sede)


        #############procesando programacion de rutas y brigadas###
        if (programacion == 1 and len(brigadas)>0 ):
            for brigada in brigadas:
                brigadas_periodo_temp = [e for e in brigadas_periodo if (e['CODSEDE'] == brigada['CODSEDE'] and e['BRIGADA'] == brigada['BRIGADA'])]
                manzanas_brigada = self.obtener_rutas_manzanas_por_brigada(brigada)

                rutas_emp =[{'COD_OPER': e[0], 'CODSEDE': e[1], 'BRIGADA': e[2], 'RUTA': e[3], 'SEDE_OPERATIVA': e[4],'EMPADRONADOR':e[5]}
                    for e in list(set(
                    (d['COD_OPER'], d['CODSEDE'], d['BRIGADA'], d['RUTA'], d['SEDE_OPERATIVA'],d['EMPADRONADOR']) for d in
                    emp_ruta_periodo if d['COD_OPER']==brigada['COD_OPER'] and d['CODSEDE']==brigada['CODSEDE'] and  d['BRIGADA']==brigada['BRIGADA'] ))]

                self.procesar_generacion_programacion(brigada,manzanas_brigada,rutas_emp)

        if(importar_capas == 1 and len(brigadas)>0):
            self.importar_capas(zonas, cod_oper)

        if (procesar_etiquetas == 1):
            for periodo in self.periodos:
                brigada_out_etiquetas =[]

                output_periodo_etiquetas = path.join(self.path_etiquetas,'{cod_oper}{periodo}{codsede}.pdf'.format(cod_oper=cod_oper,periodo=periodo, codsede = codsede))

                brigadas_periodo_t = [e for e in brigadas_periodo if int(e['PERIODO']) == int(periodo)  ]

                pdfDoc = arcpy.mapping.PDFDocumentCreate(output_periodo_etiquetas)

                brigadas_periodo_sort = sorted (brigadas_periodo_t, key=lambda k: [k['BRIGADA']] )

                #print 'periodo', periodo
                for brigada_periodo in brigadas_periodo_sort:
                    rutas_emp_periodo = [e for e in emp_ruta_periodo if (
                                e['CODSEDE'] == brigada_periodo['CODSEDE'] and e['BRIGADA'] == brigada_periodo['BRIGADA']
                                and e['PERIODO'] == brigada_periodo['PERIODO'])]

                    rutas_temp = sorted(rutas_emp_periodo, key=lambda k: [k['RUTA'], k['EMPADRONADOR']])
                    data.extend(rutas_temp)
                    brigada_out_etiqueta = self.procesar_etiquetas(data)
                    pdfDoc.appendPages(brigada_out_etiqueta)


                pdfDoc.saveAndClose()

        for brigada in brigadas:
            brigadas_periodo_temp = [e for e in brigadas_periodo if (e['CODSEDE'] == brigada['CODSEDE'] and e['BRIGADA'] == brigada['BRIGADA'] )]
            manzanas_brigada = self.obtener_rutas_manzanas_por_brigada(brigada)
            #rutas_emp =[{'COD_OPER': e[0], 'CODSEDE': e[1], 'BRIGADA': e[2], 'RUTA': e[3], 'SEDE_OPERATIVA': e[4],'EMPADRONADOR':e[5]}
            #    for e in list(set(
            #    (d['COD_OPER'], d['CODSEDE'], d['BRIGADA'], d['RUTA'], d['SEDE_OPERATIVA'],d['EMPADRONADOR']) for d in
            #    emp_ruta_periodo if d['COD_OPER']==brigada['COD_OPER'] and d['CODSEDE']==brigada['CODSEDE'] and  d['BRIGADA']==brigada['BRIGADA'] ))]

            for brigada_periodo in brigadas_periodo_temp:
                rutas = [e for e in rutas_periodo if (e['CODSEDE'] == brigada_periodo['CODSEDE'] and e['BRIGADA'] == brigada_periodo['BRIGADA'] and e['PERIODO'] == brigada_periodo['PERIODO']) ]
                rutas_emp_periodo = [e for e in emp_ruta_periodo if (e['CODSEDE'] == brigada_periodo['CODSEDE'] and e['BRIGADA'] == brigada_periodo['BRIGADA'] and e['PERIODO'] == brigada_periodo['PERIODO']) ]
                list_out_croquis_brigada = []
                lista_emp_brigada_est = []

                #rutas_manzanas_brigada = self.obtener_rutas_manzanas_por_brigada(brigada_periodo)
                rutas_manzanas_brigada = [e for e in manzanas_brigada if (e['CODSEDE'] == brigada_periodo['CODSEDE'] and e['BRIGADA'] == brigada_periodo['BRIGADA'] and e['PERIODO'] == brigada_periodo['PERIODO']) ]
                zonas_brigada = [{'UBIGEO': e[0], 'ZONA': e[1], 'DEPARTAMENTO': e[2], 'PROVINCIA': e[3],
                                  'DISTRITO': e[4], 'CODDPTO': e[5], 'CODPROV': e[6], 'CODDIST': e[7], 'CODCCPP': e[8],
                                  'NOMCCPP': e[9], 'BRIGADA': e[10], 'PERIODO': e[11],
                                  'CODSEDE': e[12], 'SEDE_OPERATIVA': e[13]
                                  } for e in list(set((
                                                          d['UBIGEO'], d['ZONA'], d['DEPARTAMENTO'], d['PROVINCIA'],
                                                          d['DISTRITO'],
                                                          d['CODDPTO'], d['CODPROV'], d['CODDIST'], d['CODCCPP'],
                                                          d['NOMCCCPP'],
                                                          d['BRIGADA'], d['PERIODO'], d['CODSEDE'], d['SEDE_OPERATIVA'] ) for d in rutas_manzanas_brigada))]
                output_brigada = path.join(self.path_listado,
                                           '{cod_oper}-{periodo}-{sede}-{brigada}.pdf'.format(cod_oper=brigada_periodo['COD_OPER'],periodo=brigada_periodo['PERIODO'],sede=brigada_periodo['CODSEDE'],
                                                                                 brigada=brigada_periodo['BRIGADA']))

                data = [brigada_periodo]
                rutas_temp = sorted(rutas_emp_periodo, key=lambda k: [k['RUTA'],k['EMPADRONADOR']])
                data.extend(rutas_temp)

                zonas_brigada_sorted = zonas_brigada

                if (procesar_croquis == 1 and len(brigadas) > 0):

                    for zona in zonas_brigada_sorted:
                        filter_rutas_manzanas = [d for d in rutas_manzanas_brigada if
                                                 (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'] and d['PERIODO'] == zona['PERIODO'] )]

                        cant_est = 0
                        mensaje_manzanas = u'<BOL>OBSERVACIONES: </BOL>El area de empadronamiento comprende las manzanas '
                        for count, ruta_manzana in enumerate(filter_rutas_manzanas, 1):
                            cant_est = cant_est + int(ruta_manzana['CANT_EST'])
                        if len(filter_rutas_manzanas) > 10:
                            mensaje_manzanas = u"{} {} al {} ".format(mensaje_manzanas, filter_rutas_manzanas[0]['MZ'],
                                                                          filter_rutas_manzanas[-1]['MZ'])
                        else:
                            for count, ruta_manzana in enumerate(filter_rutas_manzanas, 1):
                                if count == len(filter_rutas_manzanas):
                                    mensaje_manzanas = u"{} {}".format(mensaje_manzanas, ruta_manzana['MZ'])
                                else:
                                    mensaje_manzanas = u"{} {},".format(mensaje_manzanas, ruta_manzana['MZ'])
                        zona['CANT_EST'] = cant_est
                        zona['FRASE'] = mensaje_manzanas
                    print "rutas>>>", rutas
                    for ruta in rutas_temp:
                        rutas_manzanas = [e for e in rutas_manzanas_brigada if (e['CODSEDE'] == ruta['CODSEDE'] and e['RUTA'] == ruta['RUTA'] and e['PERIODO'] == ruta['PERIODO'])]
                        info = [ruta, rutas_manzanas]
                        output = path.join(self.path_listado,
                                           '{cod_oper}-{periodo}-{sede}-{brigada}-{ruta}.pdf'.format(cod_oper=ruta['COD_OPER'],periodo=ruta['PERIODO'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'], ruta=ruta['RUTA']))
                        zonas_rutas = [{'UBIGEO': e[0], 'ZONA': e[1], 'DEPARTAMENTO': e[2], 'PROVINCIA': e[3],
                                        'DISTRITO': e[4], 'CODDPTO': e[5], 'CODPROV': e[6], 'CODDIST': e[7], 'CODCCPP': e[8],
                                        'NOMCCCPP': e[9], 'BRIGADA': e[10], 'RUTA': ruta['RUTA'], 'PERIODO': e[11],
                                        'CODSEDE': e[12], 'SEDE_OPERATIVA': e[13] ,'ORDEN' :e[14]
                                        } for e in list(set((d['UBIGEO'], d['ZONA'], d['DEPARTAMENTO'], d['PROVINCIA'],
                                                             d['DISTRITO'], d['CODDPTO'], d['CODPROV'], d['CODDIST'],
                                                             d['CODCCPP'], d['NOMCCCPP'], d['BRIGADA'], d['PERIODO'],
                                                             d['CODSEDE'], d['SEDE_OPERATIVA'] , d['ORDEN']) for d in rutas_manzanas))]
                        empadronadores = [e for e in  emp_ruta_periodo if  (e['CODSEDE']==ruta['CODSEDE'] and e['RUTA']==ruta['RUTA'] and e['PERIODO']==ruta['PERIODO'])]
                        zonas_rutas_sorted = sorted(zonas_rutas, key=lambda k: [k['PERIODO'],k['ORDEN']])
                        print  "zonas_rutas_sorted >>>",zonas_rutas_sorted
                        for emp in empadronadores:
                            info[0]['EMP'] = emp['EMPADRONADOR']
                            for zona in zonas_rutas_sorted:
                                zonax={}
                                filter_rutas_manzanas = [d for d in rutas_manzanas if
                                                         (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA']  and d['PERIODO'] == zona['PERIODO'] )]
                                cant_est = 0
                                mensaje_manzanas = u'<BOL>OBSERVACIONES: </BOL>El area de empadronamiento comprende las manzanas '
                                manzanas = u""
                                for count, ruta_manzana in enumerate(filter_rutas_manzanas, 1):
                                    cant_est = cant_est + int(ruta_manzana['CANT_EST'])
                                if len(filter_rutas_manzanas) > 10:
                                    mensaje_manzanas = u"{} {} al {}".format(mensaje_manzanas, filter_rutas_manzanas[0]['MZ'],
                                                                             filter_rutas_manzanas[-1]['MZ'])
                                    manzanas = u"{} al {}".format(filter_rutas_manzanas[0]['MZ'], filter_rutas_manzanas[-1]['MZ'])
                                else:
                                    for count, ruta_manzana in enumerate(filter_rutas_manzanas, 1):
                                        if count == 1:
                                            manzanas = u"{}".format(ruta_manzana['MZ'])
                                        else:
                                            manzanas = u"{}-{}".format(manzanas, ruta_manzana['MZ'])
                                        if count == len(filter_rutas_manzanas):
                                            mensaje_manzanas = u"{} {}".format(mensaje_manzanas, ruta_manzana['MZ'])
                                        else:
                                            mensaje_manzanas = u"{} {},".format(mensaje_manzanas, ruta_manzana['MZ'])
                                zona['MANZANAS'] = manzanas
                                zona['CANT_EST'] = cant_est
                                zona['FRASE'] = mensaje_manzanas
                                zona['EMP'] = emp['EMPADRONADOR']
                                zonax = dict.copy(zona)
                                lista_emp_brigada_est.append(zonax)
                            output_listado = listado_ruta(info, output)
                            list_out_croquis = self.croquis_ruta(info, zonas_rutas_sorted,emp)
                            list_out_croquis.append(output_listado)
                            final_out_ruta = path.join(self.path_croquis_listado,'{cod_oper}-{periodo}-{sede}-{brigada}-{ruta}-{emp}.pdf'.format(
                                                                                   cod_oper=ruta['COD_OPER'],periodo=ruta['PERIODO'],sede=ruta['CODSEDE'],
                                                                                   brigada=ruta['BRIGADA'], ruta=ruta['RUTA'],emp=emp['EMPADRONADOR']))
                            if path.exists(final_out_ruta):
                                remove(final_out_ruta)
                            pdfDoc_ruta = arcpy.mapping.PDFDocumentCreate(final_out_ruta)
                            out_programacion_ruta = path.join(self.path_programaciones,
                                                              '{cod_oper}-{codsede}-{brigada}-{ruta}.pdf'.format(
                                                                  cod_oper = ruta['COD_OPER'],
                                                                  codsede=ruta['CODSEDE'],
                                                                  brigada=ruta['BRIGADA'], ruta=ruta['RUTA']))
                            #if path.exists(out_programacion_ruta):
                            #    list_out_croquis.append(out_programacion_ruta)
                            #else:
                            #    print out_programacion_ruta
                            for el in list_out_croquis:
                                pdfDoc_ruta.appendPages(el)
                            pdfDoc_ruta.saveAndClose()
                    lista_emp_brigada_est_o =  [{'UBIGEO': e[0], 'ZONA': e[1], 'DEPARTAMENTO': e[2], 'PROVINCIA': e[3],
                                        'DISTRITO': e[4], 'CODDPTO': e[5], 'CODPROV': e[6], 'CODDIST': e[7], 'CODCCPP': e[8],
                                        'NOMCCCPP': e[9], 'BRIGADA': e[10], 'PERIODO': e[11],
                                        'CODSEDE': e[12], 'SEDE_OPERATIVA': e[13] ,'MANZANAS' :e[14] , 'CANT_EST' : e[15] , 'EMP': e[16] ,'RUTA' :e[17]
                                        } for e in list(set((d['UBIGEO'], d['ZONA'], d['DEPARTAMENTO'], d['PROVINCIA'],
                                                             d['DISTRITO'], d['CODDPTO'], d['CODPROV'], d['CODDIST'],
                                                             d['CODCCPP'], d['NOMCCCPP'], d['BRIGADA'], d['PERIODO'],
                                                             d['CODSEDE'], d['SEDE_OPERATIVA'] , d['MANZANAS'],d['CANT_EST'],d['EMP'] , d['RUTA']) for d in lista_emp_brigada_est ))]

                    lista_emp_brigada_est_s = sorted(lista_emp_brigada_est_o, key=lambda k: [k['RUTA'], k['EMP']])

                    print('lista_emp_brigada_est_s>>>>',lista_emp_brigada_est_s)
                    output_listado_brigada = listado_brigada([brigada_periodo, lista_emp_brigada_est_s], output_brigada)
                    list_out_croquis_brigada = self.croquis_brigada([brigada_periodo, rutas_manzanas_brigada], zonas_brigada_sorted)
                    list_out_croquis_brigada.append(output_listado_brigada)
                    final_out_brigada= path.join(self.path_croquis_listado,'{cod_oper}-{periodo}-{sede}-{brigada}.pdf'.format(
                                                                           cod_oper=brigada_periodo['COD_OPER'],periodo=brigada_periodo['PERIODO'],sede=brigada_periodo['CODSEDE'],
                                                                           brigada=brigada_periodo['BRIGADA']))
                    if path.exists(final_out_brigada):
                        remove(final_out_brigada)
                    pdfDoc_brigada = arcpy.mapping.PDFDocumentCreate(final_out_brigada)
                    out_programacion_brigada = path.join(self.path_programaciones,
                                                         '{cod_oper}-{sede}-{brigada}.pdf'.format(
                                                             cod_oper=brigada['COD_OPER'], sede=brigada['CODSEDE'],
                                                             brigada=brigada['BRIGADA']))
                    #if path.exists(out_programacion_brigada):
                    #    list_out_croquis_brigada.append(out_programacion_brigada)
                    for el in list_out_croquis_brigada:
                        pdfDoc_brigada.appendPages(el)
                    pdfDoc_brigada.saveAndClose()

        self.conn.close()

    def obtener_coordenadas(self,x_max,y_max,x_min,y_min):
        x = x_min + (x_max-x_min)/2.0
        y = y_min + (y_max - y_min)/2.0

        return x,y

    def actualizar_centroide(self,centroide):
        sql_query = """
                DELETE sde.[SEGM_U_CENTROIDES_KMZ] where PK_CENTROIDES_KMZ='{pk}' 
                INSERT INTO sde.[SEGM_U_CENTROIDES_KMZ](PK_CENTROIDES_KMZ,X,Y,COD_OPER) values('{pk}',{x},{y},{cod_oper})
                """.format(pk= centroide['pk'] ,x= centroide['x'] ,y= centroide['y'], cod_oper =centroide['cod_oper'] )
        self.cursor.execute(sql_query)
        self.conn.commit()

    def set_mxd (self,path_plantilla,where_manzanas,where_frentes_ini,where_zonas,where_crecimiento):
        print 'where_crecimiento>>>',where_crecimiento
        mxd = arcpy.mapping.MapDocument(path_plantilla)
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        zona_mfl = arcpy.mapping.ListLayers(mxd, "TB_ZONAS")[0]
        mzs_mfl = arcpy.mapping.ListLayers(mxd, "TB_MZS_ORD")[0]
        frentes_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES")[0]
        frentes_inicio_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES_INICIO")[0]
        manzanas_crecimiento_mfl = arcpy.mapping.ListLayers(mxd, "TB_MZS_CRECIMIENTO")[0]
        #zona_crecimiento_mfl= arcpy.mapping.ListLayers(mxd, "TB_ZONAS_CRECIMIENTO")[0]



        frentes_mfl.definitionQuery = where_manzanas
        frentes_inicio_mfl.definitionQuery = where_frentes_ini

        mzs_mfl.definitionQuery = where_manzanas
        zona_mfl.definitionQuery = where_zonas
        manzanas_crecimiento_mfl.definitionQuery = where_crecimiento

        mxd_extent = mzs_mfl.getSelectedExtent()

        cant_mzs_c=int(arcpy.GetCount_management(manzanas_crecimiento_mfl).getOutput(0))

        if (cant_mzs_c>0):
            mxd_extent_c = manzanas_crecimiento_mfl.getSelectedExtent()
            mxd_extent.XMin = min(float(mxd_extent_c.XMin),float(mxd_extent.XMin))
            mxd_extent.XMax = max(float(mxd_extent_c.XMax), float(mxd_extent.XMax))
            mxd_extent.YMin = min(float(mxd_extent_c.YMin), float(mxd_extent.YMin))
            mxd_extent.YMax = max(float(mxd_extent_c.YMax), float(mxd_extent.YMax))


        #if (where_crecimiento!="1 <> 1"):
        #    print 'manzanas crecimiento'
        #    mxd_extent_c = manzanas_crecimiento_mfl.getSelectedExtent()
        #    mxd_extent.XMin = min(float(mxd_extent_c.XMin),float(mxd_extent.XMin))
        #    mxd_extent.XMax = max(float(mxd_extent_c.XMax), float(mxd_extent.XMax))
        #    mxd_extent.YMin = min(float(mxd_extent_c.YMin), float(mxd_extent.YMin))
        #    mxd_extent.YMax = max(float(mxd_extent_c.YMax), float(mxd_extent.YMax))

        return df ,mxd,mxd_extent

    def croquis_ruta(self, info, zonas,emp):
        list_out_croquis = []

        for zona in zonas:
            ruta = info[0]
            rutas_manzanas = info[1]

            rutas_aes = []

            rutas_aes =  list(set((d['Z_AE']) for d in rutas_manzanas if
                                (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])))

            manzanas = list(set((d['UBIGEO'], d['ZONA'], d['MZ']) for d in rutas_manzanas if
                                (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])))

            frentes_ini = [(d[0], d[1], d[2], 1) for d in manzanas]

            where_manzanas = expresion.expresion_2(manzanas,
                                                   [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])
            where_frentes_ini = expresion.expresion_2(frentes_ini,
                                                      [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"],
                                                       ["FRENTE_ORD", "SHORT"]])
            where_zonas = expresion.expresion_2([[zona['UBIGEO'], zona['ZONA']]],
                                                [["UBIGEO", "TEXT"], ["ZONA", "TEXT"]])

            where_crecimiento = "1 <> 1"

            if (rutas_aes is not None and len(rutas_aes) > 0 and rutas_aes[0] is not None):

                ls = []
                for r in rutas_aes:
                  ls.append([r])

                where_crecimiento = expresion.expresion_2(ls,
                                                          [["PK_AEU", "TEXT"]])




            df ,mxd,mxd_extent = self.set_mxd(self.path_plantilla_croquis_empadronador,where_manzanas,where_frentes_ini,where_zonas,where_crecimiento)



            dflinea = arcpy.Polyline(
                arcpy.Array([arcpy.Point(mxd_extent.XMin, mxd_extent.YMin), arcpy.Point(mxd_extent.XMax, mxd_extent.YMax)]),
                df.spatialReference)

            dflineaX = arcpy.Polyline(
                arcpy.Array([arcpy.Point(mxd_extent.XMin,mxd_extent.YMin), arcpy.Point(mxd_extent.XMax, mxd_extent.YMin)]),
                df.spatialReference)

            dflineaY = arcpy.Polyline(
                arcpy.Array([arcpy.Point(mxd_extent.XMin, mxd_extent.YMin), arcpy.Point(mxd_extent.XMin, mxd_extent.YMax)]),
                df.spatialReference)


            distancia = dflinea.getLength("GEODESIC", "METERS")
            distanciaX = dflineaX.getLength("GEODESIC", "METERS")
            distanciaY = dflineaY.getLength("GEODESIC", "METERS")

            tan = 1

            try:
                tan = math.fabs(float(distanciaY) / float(distanciaX))
            except:
                tan = 1


            print "distancia>>>>", distancia
            if( 0.67<tan ):

                df,mxd, mxd_extent = self.set_mxd(self.path_plantilla_croquis_empadronador_v,where_manzanas,where_frentes_ini,where_zonas,where_crecimiento)
                mxd_extent.YMax = float(mxd_extent.YMax) + 0.002
                df.extent = mxd_extent
                df.scale = df.scale * 1.3

                if (float(distancia) > 1000):
                    #mxd_extent.YMax = float(mxd_extent.YMax) + 0.002
                    #df.extent = mxd_extent
                    e=df.extent
                    e.YMax = float(e.YMax) + 0.002
                    df.extent = e



            else:
                if (float(distancia) > 600):
                    mxd_extent.YMax = float(mxd_extent.YMax) + 0.002
                    mxd_extent.XMax = float(mxd_extent.XMax) - 0.001

                    df.extent = mxd_extent
                    df.scale = df.scale * 1.3


                    if (float(distancia) > 1000):
                        e = df.extent
                        e.YMax = float(e.YMax) + 0.002
                        df.extent = e

                else:
                    mxd_extent.YMax = float(mxd_extent.YMax) + 0.001
                    df.extent = mxd_extent
                    df.scale = df.scale * 2



            codigo ='{cod_oper}{periodo}{sede}{brigada}{ruta}{emp}'.format( cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'],ruta=ruta['RUTA'],emp= emp['EMPADRONADOR'],periodo=ruta['PERIODO'])

            list_text_el = [["COD_BARRA", "*{}*".format(codigo)], ["TEXT_COD_BARRA", "{}".format(codigo)],["CODDPTO", zona["CODDPTO"]], ["CODPROV", zona['CODPROV']], ["CODDIST", zona['CODDIST']],
                            ["ZONA", zona['ZONA']]]
            list_text_el = list_text_el + [["CODCCPP", zona['CODCCPP']], ["DEPARTAMENTO", zona['DEPARTAMENTO']]]
            list_text_el = list_text_el + [["PROVINCIA", zona['PROVINCIA']], ["DISTRITO", zona['DISTRITO']],
                                           ["NOMCCPP", zona['NOMCCCPP']]]
            list_text_el = list_text_el + [["BRIGADA", zona["BRIGADA"]], ["RUTA", zona["RUTA"]],["EMP", emp['EMPADRONADOR']],
                                           ["CANT_EST", '{}'.format(zona["CANT_EST"])], ["FRASE", zona["FRASE"]],
                                           ["PERIODO", '{}'.format(ruta["PERIODO"])]]

            list_text_el = list_text_el + [["DOC", "DOC.CENEC.03.07A"]]

            for text_el in list_text_el:

                el = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text = text_el[1]

            out_croquis = path.join(self.path_croquis,
                                    '{cod_oper}-{periodo}-{sede}-{brigada}-{ruta}-{ubigeo}-{zona}.pdf'.format(cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'],
                                                                              ruta=ruta['RUTA'], ubigeo=zona['UBIGEO'],zona=zona['ZONA'],periodo=ruta['PERIODO'] ))



            out_croquis_copia = path.join(self.path_croquis,
                                          '{cod_oper}-{periodo}-{sede}-{brigada}-{ruta}-{ubigeo}-{zona}-b.pdf'.format(cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'],
                                                                                          ruta=ruta['RUTA'],
                                                                                          ubigeo=zona['UBIGEO'],
                                                                                          zona=zona['ZONA'],
                                                                                                                      periodo=ruta['PERIODO']

                                                                                                                      ))

            arcpy.mapping.ExportToPDF(mxd, out_croquis, "PAGE_LAYOUT")


            newmxd = path.join(self.path_mxd,
                               '{cod_oper}-{periodo}-{sede}-{brigada}-{ruta}-{ubigeo}-{zona}.mxd'.format(
                                   cod_oper=ruta['COD_OPER'], sede=ruta['CODSEDE'], brigada=ruta['BRIGADA'],
                                   ruta=ruta['RUTA'], ubigeo=zona['UBIGEO'], zona=zona['ZONA'],
                                   periodo=ruta['PERIODO']))

            print newmxd
            mxd.saveACopy(newmxd)


            list_out_croquis.append(out_croquis)

            list_text_el = list_text_el + [["DOC", "DOC.CENEC.03.07B"]]
            for text_el in list_text_el:
                el = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text = text_el[1]
            arcpy.mapping.ExportToPDF(mxd, out_croquis_copia, "PAGE_LAYOUT")

            list_out_croquis.append(out_croquis_copia)

            ###############################analisis kmz #######################################

            mxd_kmz = arcpy.mapping.MapDocument(self.path_plantilla_kmz_mxd)
            df_kmz = arcpy.mapping.ListDataFrames(mxd_kmz, "Layers")[0]

            no_seleccion_mfl = arcpy.mapping.ListLayers(mxd_kmz, "NO_SELECCION")[0]
            seleccion_mfl = arcpy.mapping.ListLayers(mxd_kmz, "SELECCION")[0]



            where_not_manzanas = ''
            for count,manzana in enumerate(manzanas):
                if count==0:
                    where_not_manzanas =u"'{manzana}'".format(manzana=manzana[2])
                else:
                    where_not_manzanas = u"{where_not_manzanas},'{manzana}'".format(where_not_manzanas=where_not_manzanas,manzana=manzana[2])

            where_not_manzanas = u"{where_zonas} and MANZANA NOT IN ({where_not_manzanas})".format(where_zonas= where_zonas
                                                                                                  ,where_not_manzanas =where_not_manzanas)


            manzanas = list(set((d['UBIGEO'], d['ZONA'], d['MZ']) for d in rutas_manzanas if
                                (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])))

            where_manzanas = expresion.expresion_2(manzanas,
                                                   [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])


            no_seleccion_mfl.definitionQuery = where_not_manzanas


            seleccion_mfl.definitionQuery = where_manzanas

            out_kmz = path.join(self.path_kmz,
                                          '{cod_oper}{periodo}{sede}{brigada}{ruta}{ubigeo}{zona}.kmz'.format(cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'],
                                                                                          ruta=ruta['RUTA'],
                                                                                          ubigeo=zona['UBIGEO'],
                                                                                          zona=zona['ZONA'],
                                                                                          periodo= ruta['PERIODO']

                                                                                                     ))


            mxd_kmz.save()
            if path.exists(out_kmz):
                remove(out_kmz)

            arcpy.MapToKML_conversion(self.path_plantilla_kmz_mxd,'Layers',out_kmz )

            #####obtener centroides

            x,y = self.obtener_coordenadas(mxd_extent.XMax, mxd_extent.YMax, mxd_extent.XMin, mxd_extent.YMin)
            c={}
            c['pk']='{cod_oper}{periodo}{sede}{brigada}{ruta}{ubigeo}{zona}'.format(cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'],
                                                                                          ruta=ruta['RUTA'],
                                                                                          ubigeo=zona['UBIGEO'],
                                                                                          zona=zona['ZONA'],
                                                                                          periodo= ruta['PERIODO'])

            c['x'] = x
            c['y'] = y
            c['cod_oper'] = ruta['COD_OPER']

            self.actualizar_centroide(c)



        return list_out_croquis

    def croquis_brigada(self, info, zonas):
        list_out_croquis = []
        for zona in zonas:
            brigada = info[0]
            rutas_manzanas = info[1]
            rutas_aes =  list(set((d['Z_AE']) for d in rutas_manzanas if
                                (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])))

            manzanas = list(set((d['UBIGEO'], d['ZONA'], d['MZ']) for d in rutas_manzanas if
                                (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])))
            frentes_ini = [(d[0], d[1], d[2], 1) for d in manzanas]

            where_manzanas = expresion.expresion_2(manzanas,
                                                   [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])

            where_frentes_ini = expresion.expresion_2(frentes_ini,
                                                      [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"],
                                                       ["FRENTE_ORD", "SHORT"]])

            where_zonas = expresion.expresion_2([[zona['UBIGEO'], zona['ZONA']]],
                                                [["UBIGEO", "TEXT"], ["ZONA", "TEXT"]])

            where_crecimiento = "1 <> 1"

            if (rutas_aes is not None and len(rutas_aes) > 0 and rutas_aes[0] is not None):
                ls=[]
                for r in rutas_aes:
                    ls.append([r])

                where_crecimiento = expresion.expresion_2(ls,
                                                          [["PK_AEU", "TEXT"]])

            df, mxd, mxd_extent = self.set_mxd(self.path_plantilla_croquis_brigada, where_manzanas,
                                               where_frentes_ini, where_zonas, where_crecimiento)


            dflinea = arcpy.Polyline(
                arcpy.Array(
                    [arcpy.Point(mxd_extent.XMin, mxd_extent.YMin), arcpy.Point(mxd_extent.XMax, mxd_extent.YMax)]),
                df.spatialReference)

            dflineaX = arcpy.Polyline(
                arcpy.Array(
                    [arcpy.Point(mxd_extent.XMin, mxd_extent.YMin), arcpy.Point(mxd_extent.XMax, mxd_extent.YMin)]),
                df.spatialReference)

            dflineaY = arcpy.Polyline(
                arcpy.Array(
                    [arcpy.Point(mxd_extent.XMin, mxd_extent.YMin), arcpy.Point(mxd_extent.XMin, mxd_extent.YMax)]),
                df.spatialReference)

            distancia = dflinea.getLength("GEODESIC", "METERS")
            distanciaX = dflineaX.getLength("GEODESIC", "METERS")
            distanciaY = dflineaY.getLength("GEODESIC", "METERS")

            tan = 1

            try:
                tan = math.fabs(float(distanciaY) / float(distanciaX))
            except:
                tan = 1

            tan=math.fabs( float(distanciaY)/float(distanciaX) )


            if (0.67<tan):
                df, mxd, mxd_extent = self.set_mxd(self.path_plantilla_croquis_brigada_v, where_manzanas,
                                                   where_frentes_ini, where_zonas, where_crecimiento)

                mxd_extent.YMax = float(mxd_extent.YMax) + 0.002
                df.extent = mxd_extent

                df.scale = df.scale * 1.3

                if (float(distancia) > 1000):
                    e = df.extent
                    e.YMax = float(e.YMax) + 0.002
                    df.extent = e


            else:
                if (float(distancia) > 600):
                    mxd_extent.YMax = float(mxd_extent.YMax) + 0.002
                    mxd_extent.XMax = float(mxd_extent.XMax) - 0.001

                    df.extent = mxd_extent
                    df.scale = df.scale * 1.3


                    if (float(distancia) > 1000):
                        e = df.extent
                        e.YMax = float(e.YMax) + 0.002
                        df.extent = e

                else:
                    mxd_extent.YMax = float(mxd_extent.YMax) + 0.002
                    df.extent = mxd_extent
                    df.scale = df.scale * 2


            codigo = '{cod_oper}{periodo}{sede}{brigada}'.format(cod_oper=brigada['COD_OPER'], sede=brigada['CODSEDE'],
                                                                   brigada=brigada['BRIGADA'],periodo=brigada['PERIODO'])


            list_text_el = [["COD_BARRA", "*{}*".format(codigo)], ["TEXT_COD_BARRA", "{}".format(codigo)],["CODDPTO", zona["CODDPTO"]], ["CODPROV", zona['CODPROV']], ["CODDIST", zona['CODDIST']],
                            ["ZONA", zona['ZONA']]]
            list_text_el = list_text_el + [["CODCCPP", zona['CODCCPP']], ["DEPARTAMENTO", zona['DEPARTAMENTO']]]
            list_text_el = list_text_el + [["PROVINCIA", zona['PROVINCIA']], ["DISTRITO", zona['DISTRITO']],
                                           ["NOMCCPP", zona['NOMCCPP']]]
            list_text_el = list_text_el + [["BRIGADA", zona["BRIGADA"]], ["CANT_EST", '{}'.format(zona["CANT_EST"])],
                                           ["FRASE", zona["FRASE"]], ["PERIODO", '{}'.format(zona["PERIODO"])]]

            list_text_el = list_text_el + [["DOC", "DOC.CENEC.03.09"]]

            for text_el in list_text_el:
                el = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text = text_el[1]


            out_croquis = path.join(self.path_croquis,
                                    '{cod_oper}-{periodo}-{sede}-{brigada}-{ubigeo}-{zona}.pdf'.format(
                                                                                        cod_oper=brigada['COD_OPER'],
                                                                                        sede=brigada['CODSEDE'],
                                                                                        brigada=brigada['BRIGADA'],
                                                                                        ubigeo=zona['UBIGEO'],
                                                                                        zona=zona['ZONA'],
                                                                                        periodo = brigada['PERIODO']
                                    ))

            arcpy.mapping.ExportToPDF(mxd, out_croquis, "PAGE_LAYOUT")
            list_out_croquis.append(out_croquis)

        return list_out_croquis

s = CroquisListadoCENEC()
print 'procesando...'
s.procesar_croquis_listado(cod_oper =COD_OPER,codsede=CODSEDE,programacion=PROGRAMACION,
                           importar_capas=IMPORTAR_CAPAS ,procesar_croquis=PROCESAR_CROQUIS,
                           procesar_lista_sede=PROCESAR_LISTA_SEDE ,procesar_etiquetas=PROCESAR_ETIQUETAS)


