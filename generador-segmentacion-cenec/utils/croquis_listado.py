
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
from programacion import crear_programacion_rutas ,crear_programacion_brigadas ,crear_etiquetas

arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

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
        self.path_plantilla_croquis_brigada = path.join(config.PATH_PLANTILLA_CROQUIS, 'croquis_brigada.mxd')
        self.path_plantilla_croquis_brigada_a2 = path.join(config.PATH_PLANTILLA_CROQUIS, 'croquis_brigada_a2.mxd')

        self.path_plantilla_kmz_mxd = path.join(config.PATH_PLANTILLA_CROQUIS, 'plantilla_kmz.mxd')
        self.centroides = []

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


            print('where>>>', where)
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
        query = """  begin
                         SELECT b.DEPARTAMENTO,b.PROVINCIA,b.DISTRITO,SUBSTRING(CODCCPP,7,5)CODCCPP,b.NOMCCPP,a.* FROM SDE.SEGM_PROGRAMACION_BRIGADAS A
                         INNER JOIN TB_ZONA B ON A.UBIGEO+ A.ZONA = B.UBIGEO+B.ZONA
                         where a.codsede='{codsede}' and a.brigada ={brigada} and a.cod_oper='{cod_oper}'
                         order by a.periodo,a.orden              
                     end
                            """.format(codsede=brigada["CODSEDE"],brigada=int(brigada["BRIGADA"]), cod_oper=brigada["COD_OPER"])
        #print 'obtener_emp_por_ruta>>>', query
        empadronadores = to_dict(self.cursor.execute(query))
        return empadronadores

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
                                        order by COD_OPER,CODSEDE,BRIGADA,RUTA,EMPADRONADOR DESC 
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
                                --SELECT B.*,B.MARCO_FIN CANT_EST  FROM SDE.TRABAJO_PSEUDO_CODIGO A
                                --INNER JOIN dbo.SEGM_U_RUTA_MANZANA  B ON A.UBIGEO= B.UBIGEO AND A.ZONA=B.ZONA AND A.MANZANA=B.MZ --AND A.FASE=B.FASE
                                --where B.CODSEDE = '{codsede}' AND B.BRIGADA ='{brigada}' AND B.COD_OPER = '{cod_oper}' 
                                --ORDER BY B.UBIGEO,B.ZONA,A.FALSO_COD
                                
                                SELECT B.*, (B.MARCO_FIN + B.PUESTO) CANT_EST  FROM dbo.SEGM_U_RUTA_MANZANA B
                                where B.CODSEDE = '{codsede}' AND B.BRIGADA ='{brigada}' AND B.COD_OPER = '{cod_oper}' 
                                
                                ORDER BY B.UBIGEO,B.PERIODO,B.ZONA,B.FALSO_COD
                            end
                    """.format(codsede=brigada["CODSEDE"], brigada=brigada["BRIGADA"],cod_oper = brigada["COD_OPER"])
        print  'query_rutas_manzanas_por_brigada>>>', query_rutas_manzanas_por_brigada
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas_por_brigada))
        return rutas_manzanas

    def obtener_rutas_manzanas(self, ruta):

        query_rutas_manzanas = """
                            begin

                                SELECT B.*, (B.MARCO_FIN + B.PUESTO) CANT_EST  FROM SDE.SEGM_U_RUTA_MANZANA B
                                where B.CODSEDE = '{codsede}' AND B.RUTA ='{ruta}' AND B.COD_OPER = '{cod_oper}' AND B.PERIODO = {periodo}
                                ORDER BY B.UBIGEO,B.ZONA,B.FALSO_COD
                            end
                    """.format(codsede=ruta["CODSEDE"], ruta=ruta["RUTA"], cod_oper=ruta["COD_OPER"],
                               periodo=ruta["PERIODO"])
        print 'query_rutas_manzanas>>>', query_rutas_manzanas
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas))
        return rutas_manzanas

    def procesar_generacion_programacion(self,brigada,manzanas_brigada,rutas_emp):
        prog_brigada = self.obtener_programacion_brigada(brigada)

        ######
        ####creando programacion de brigadas
        ######
        for p in prog_brigada:
            manzanas_prog = [e for e in manzanas_brigada if (p['PK_AEU'] == e['Z_AE'])]
            if len(manzanas_prog) > 1:
                p['MANZANAS'] = 'DEL {} AL {}'.format(manzanas_prog[0]['MZ'], manzanas_prog[-1]['MZ'])
            elif len(manzanas_prog) == 1:
                p['MANZANAS'] = manzanas_prog[0]['MZ']
            else:
                p['MANZANAS'] = ''
            output_brigada = path.join(self.path_programaciones, '{cod_oper}-{codsede}-{brigada}.xlsx'.format(cod_oper=brigada['COD_OPER'],
                                                                                                                codsede=
                                                                                                                brigada[
                                                                                                                    'CODSEDE'],brigada=brigada['BRIGADA']))


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
                if len(manzanas_prog) > 1:

                    p['MANZANAS'] = 'DEL {} AL {}'.format(manzanas_prog[0]['MZ'], manzanas_prog[-1]['MZ'])
                elif len(manzanas_prog) == 1:
                    p['MANZANAS'] = manzanas_prog[0]['MZ']
                else:
                    p['MANZANAS'] = ''
            crear_programacion_rutas([ruta_emp, prog], output)


    def procesar_etiquetas(self,data):
        brigada =data[0]
        output_brigada = path.join(self.path_etiquetas,
                                   '{cod_oper}{periodo}{codsede}{brigada}.xlsx'.format(cod_oper = brigada['COD_OPER'],
                                                                                codsede = brigada['CODSEDE'],
                                                                                periodo = brigada['PERIODO'],
                                                                                brigada=brigada['BRIGADA']))

        crear_etiquetas(data, output_brigada)
        #crear_etiquetas(brigada,output_brigada)



    def procesar_croquis_listado(self,cod_oper='01',codsede='07',programacion=1,importar_capas=1):
        operacion=self.obtener_operacion(cod_oper)

        self.path_croquis_listado = path.join(config.BASE_DIR_CROQUIS_LISTADO,operacion['DESCRIPCION'], r'croquis_listado')
        self.path_listado = path.join(config.BASE_DIR_CROQUIS_LISTADO,operacion['DESCRIPCION'], r'listado')
        self.path_croquis = path.join(config.BASE_DIR_CROQUIS_LISTADO, operacion['DESCRIPCION'],r'croquis')
        self.path_kmz = path.join(config.BASE_DIR_CROQUIS_LISTADO, operacion['DESCRIPCION'], 'kmz')
        self.path_programaciones = path.join(config.BASE_DIR_CROQUIS_LISTADO, operacion['DESCRIPCION'], 'programacion')
        self.path_etiquetas = path.join(config.BASE_DIR_CROQUIS_LISTADO, operacion['DESCRIPCION'], 'etiquetas')


        carpetas  = [self.path_croquis_listado,self.path_listado,self.path_croquis ,self.path_kmz,
                     self.path_programaciones,self.path_etiquetas]

        for carpeta in carpetas:
            if not (path.exists(carpeta)):
                mkdir(carpeta)


        brigadas = self.obtener_brigadas(cod_oper=cod_oper,codsede=codsede)
        zonas = []


        emp_ruta_periodo = self.obtener_emp_ruta_periodo(cod_oper=cod_oper,codsede=codsede)


        brigadas_periodo = [{'COD_OPER':e[0],'CODSEDE':e[1],'BRIGADA':e[2],'PERIODO':e[3] ,'SEDE_OPERATIVA':e[4] }  for e in  list(set(( d['COD_OPER'],d['CODSEDE'],d['BRIGADA'] ,d['PERIODO'],d['SEDE_OPERATIVA']) for d in emp_ruta_periodo))]
        rutas_periodo =[ {'COD_OPER': e[0], 'CODSEDE': e[1], 'BRIGADA': e[2],'RUTA':e[3],'PERIODO':e[4],'SEDE_OPERATIVA':e[5]}
            for e in list(set((d['COD_OPER'], d['CODSEDE'], d['BRIGADA'],d['RUTA'] , d['PERIODO']  ,d['SEDE_OPERATIVA']) for d in emp_ruta_periodo))]

        for brigada in brigadas:
            manzanas_brigada = self.obtener_rutas_manzanas_por_brigada(brigada)
            zonas = zonas + [{'UBIGEO': e[0], 'ZONA': e[1]} for e in
                                list(set((d['UBIGEO'], d['ZONA']) for d in manzanas_brigada))]

        ##############importando capas para los croquis###########

        if(importar_capas==1):
            self.importar_capas(zonas, cod_oper)

        for brigada in brigadas:
            brigadas_periodo_temp = [e for e in brigadas_periodo if (e['CODSEDE'] == brigada['CODSEDE'] and e['BRIGADA'] == brigada['BRIGADA'])]
            manzanas_brigada=self.obtener_rutas_manzanas_por_brigada(brigada)

            rutas_emp =[{'COD_OPER': e[0], 'CODSEDE': e[1], 'BRIGADA': e[2], 'RUTA': e[3], 'SEDE_OPERATIVA': e[4],'EMPADRONADOR':e[5]}
                for e in list(set(
                (d['COD_OPER'], d['CODSEDE'], d['BRIGADA'], d['RUTA'], d['SEDE_OPERATIVA'],d['EMPADRONADOR']) for d in
                emp_ruta_periodo if d['COD_OPER']==brigada['COD_OPER'] and d['CODSEDE']==brigada['CODSEDE'] and  d['BRIGADA']==brigada['BRIGADA'] ))]



            ###procesando etiquetas


            ## creando programacion
            if (programacion == 1):
                self.procesar_generacion_programacion(brigada,manzanas_brigada,rutas_emp)

            for brigada_periodo in brigadas_periodo_temp:
                rutas = [e for e in rutas_periodo if (e['CODSEDE'] == brigada_periodo['CODSEDE'] and e['BRIGADA'] == brigada_periodo['BRIGADA'] and e['PERIODO'] == brigada_periodo['PERIODO']) ]
                #rutas_emp_periodo = [e for e in rutas_emp if (e['CODSEDE'] == brigada_periodo['CODSEDE'] and e['BRIGADA'] == brigada_periodo['BRIGADA'] and e['PERIODO'] == brigada_periodo['PERIODO'])]
                rutas_emp_periodo = [e for e in emp_ruta_periodo if (e['CODSEDE'] == brigada_periodo['CODSEDE'] and e['BRIGADA'] == brigada_periodo['BRIGADA'] and e['PERIODO'] == brigada_periodo['PERIODO']) ]


                list_out_croquis_brigada = []
                lista_emp_brigada_est = []

                rutas_manzanas_brigada = [e for e in manzanas_brigada if (e['CODSEDE'] == brigada_periodo['CODSEDE'] and e['BRIGADA'] == brigada_periodo['BRIGADA'] and e['PERIODO'] == brigada_periodo['PERIODO']) ]

                #rutas_manzanas_brigada = self.obtener_rutas_manzanas_por_brigada(brigada_periodo)

                zonas_brigada = [{'UBIGEO': e[0], 'ZONA': e[1], 'DEPARTAMENTO': e[2], 'PROVINCIA': e[3],
                                  'DISTRITO': e[4], 'CODDPTO': e[5], 'CODPROV': e[6], 'CODDIST': e[7], 'CODCCPP': e[8],
                                  'NOMCCPP': e[9], 'BRIGADA': e[10], 'RUTA': e[14], 'PERIODO': e[11],
                                  'CODSEDE': e[12], 'SEDE_OPERATIVA': e[13]
                                  } for e in list(set((
                                                          d['UBIGEO'], d['ZONA'], d['DEPARTAMENTO'], d['PROVINCIA'],
                                                          d['DISTRITO'],
                                                          d['CODDPTO'], d['CODPROV'], d['CODDIST'], d['CODCCPP'],
                                                          d['NOMCCCPP'],
                                                          d['BRIGADA'], d['PERIODO'], d['CODSEDE'], d['SEDE_OPERATIVA'] ,d['RUTA'] ) for d in rutas_manzanas_brigada))]

                output_brigada = path.join(self.path_listado,
                                           '{cod_oper}-{periodo}-{sede}-{brigada}.pdf'.format(cod_oper=brigada_periodo['COD_OPER'],periodo=brigada_periodo['PERIODO'],sede=brigada_periodo['CODSEDE'],
                                                                                 brigada=brigada_periodo['BRIGADA']))

                print "zonas_brigada>>>", zonas_brigada

                # rutas_emp_temp=sorted(rutas_emp,key = lambda k:k['EMPADRONADOR'])
                #print 'brigada>>>', brigada_periodo
                #print 'rutas_emp_periodo>>>', rutas_emp_periodo


                data = [brigada_periodo]

                rutas_temp = sorted(rutas_emp_periodo, key=lambda k: [k['RUTA'],k['EMPADRONADOR']])
                data.extend(rutas_temp)

                self.procesar_etiquetas(data)




                for zona in zonas_brigada:
                    filter_rutas_manzanas = [d for d in rutas_manzanas_brigada if
                                             (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])]
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

                for ruta in rutas:
                    #rutas_manzanas = rutas_manzanas_brigada
                    #rutas_manzanas = self.obtener_rutas_manzanas(ruta)

                    #rutas_manzanas_brigada
                    #[e for e in rutas_manzanas_brigada if e['CODSEDE'] = ruta['CODSEDE'] and e['RUTA'] =ruta['RUTA'] and e['PERIODO'] = ruta['PERIODO']]
                    rutas_manzanas = [e for e in rutas_manzanas_brigada if (e['CODSEDE'] == ruta['CODSEDE'] and e['RUTA'] == ruta['RUTA'] and e['PERIODO'] == ruta['PERIODO'])]

                    info = [ruta, rutas_manzanas]
                    output = path.join(self.path_listado,
                                       '{cod_oper}-{periodo}-{sede}-{brigada}-{ruta}.pdf'.format(cod_oper=ruta['COD_OPER'],periodo=ruta['PERIODO'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'], ruta=ruta['RUTA']))
                    zonas_rutas = [{'UBIGEO': e[0], 'ZONA': e[1], 'DEPARTAMENTO': e[2], 'PROVINCIA': e[3],
                                    'DISTRITO': e[4], 'CODDPTO': e[5], 'CODPROV': e[6], 'CODDIST': e[7], 'CODCCPP': e[8],
                                    'NOMCCCPP': e[9], 'BRIGADA': e[10], 'RUTA': ruta['RUTA'], 'PERIODO': e[11],
                                    'CODSEDE': e[12], 'SEDE_OPERATIVA': e[13]
                                    } for e in list(set((d['UBIGEO'], d['ZONA'], d['DEPARTAMENTO'], d['PROVINCIA'],
                                                         d['DISTRITO'], d['CODDPTO'], d['CODPROV'], d['CODDIST'],
                                                         d['CODCCPP'], d['NOMCCCPP'], d['BRIGADA'], d['PERIODO'],
                                                         d['CODSEDE'], d['SEDE_OPERATIVA']) for d in rutas_manzanas))]

                    empadronadores = [e for e in  emp_ruta_periodo if  (e['CODSEDE']==ruta['CODSEDE'] and e['RUTA']==ruta['RUTA'] and e['PERIODO']==ruta['PERIODO'])]
                    print "empadronadores>>>", empadronadores

                    for emp in empadronadores:
                        info[0]['EMP'] = emp['EMPADRONADOR']

                        print info[0]['EMP']
                        for zona in zonas_rutas:
                            zonax={}
                            filter_rutas_manzanas = [d for d in rutas_manzanas if
                                                     (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])]
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
                            print 'zona>>>',zona
                            zonax = dict.copy(zona)

                            lista_emp_brigada_est.append(zonax)
                            print 'lista_emp_brigada_est>>>', lista_emp_brigada_est

                        output_listado = listado_ruta(info, output)
                        list_out_croquis = self.croquis_ruta(info, zonas_rutas,emp)
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

                        if path.exists(out_programacion_ruta):
                            list_out_croquis.append(out_programacion_ruta)
                        else:
                            print out_programacion_ruta

                        for el in list_out_croquis:
                            pdfDoc_ruta.appendPages(el)
                        pdfDoc_ruta.saveAndClose()

                print "lista_emp_brigada_est>>>", lista_emp_brigada_est

                output_listado_brigada = listado_brigada([brigada_periodo, lista_emp_brigada_est], output_brigada)
                list_out_croquis_brigada = self.croquis_brigada([brigada_periodo, rutas_manzanas_brigada], zonas_brigada)
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

                if path.exists(out_programacion_brigada):
                    list_out_croquis_brigada.append(out_programacion_brigada)
                else:
                    print out_programacion_brigada
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

    def croquis_ruta(self, info, zonas,emp):
        list_out_croquis = []

        for zona in zonas:
            ruta = info[0]
            rutas_manzanas = info[1]
            rutas_aes =  list(set((d['Z_AE']) for d in rutas_manzanas if
                                (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])))
            print 'rutas_aes>>>',rutas_aes

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



            mxd = arcpy.mapping.MapDocument(self.path_plantilla_croquis_empadronador)
            df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
            zona_mfl = arcpy.mapping.ListLayers(mxd, "TB_ZONAS")[0]
            mzs_mfl = arcpy.mapping.ListLayers(mxd, "TB_MZS_ORD")[0]
            frentes_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES")[0]
            frentes_inicio_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES_INICIO")[0]
            manzanas_crecimiento_mfl = arcpy.mapping.ListLayers(mxd, "TB_MZS_CRECIMIENTO")[0]


            frentes_mfl.definitionQuery = where_manzanas
            frentes_inicio_mfl.definitionQuery = where_frentes_ini


            mzs_mfl.definitionQuery = where_manzanas
            zona_mfl.definitionQuery = where_zonas


            mxd_extent=mzs_mfl.getSelectedExtent()
            df.extent = mxd_extent

            print 'mxd_extent2>>>', mxd_extent



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


            if (float(distancia) <= 100):
                df.scale = df.scale * 4
            elif (float(distancia) > 100 and float(distancia) <= 490):
                df.scale = df.scale * 3
            elif (float(distancia) > 490 and  float(distancia) <=1000 ):
                df.scale = df.scale * 2.5
            elif (float(distancia) > 1000):
                df.scale = df.scale * 2

            print 'df.scale>>>',df.scale

            print 'distancia>>>', distancia

            if (float(distancia)>700):
                print 'distanciaX>>>',distanciaX
                print 'distanciaY>>>', distanciaY
                if (distanciaX  < distanciaY):

                    print 'largo>>>'
                    mxd_extent.YMax = float(mxd_extent.YMax) + 0.0005
                    mxd_extent.XMax = float(mxd_extent.XMax) - 0.004
                else:
                    print 'ancho>>>'
                    mxd_extent.YMax = float(mxd_extent.YMax) + 0.002
                    mxd_extent.XMax = float(mxd_extent.XMax) - 0.001
                df.extent = mxd_extent
                df.scale = df.scale * 1.3
            else:
                mxd_extent.YMax = float(mxd_extent.YMax) + 0.002
                df.extent = mxd_extent
                df.scale = df.scale * 2

            #df.extent = mxd_extent



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



            print 'out_croquis>>>',out_croquis


            out_croquis_copia = path.join(self.path_croquis,
                                          '{cod_oper}-{periodo}-{sede}-{brigada}-{ruta}-{ubigeo}-{zona}-b.pdf'.format(cod_oper=ruta['COD_OPER'],sede=ruta['CODSEDE'],brigada=ruta['BRIGADA'],
                                                                                          ruta=ruta['RUTA'],
                                                                                          ubigeo=zona['UBIGEO'],
                                                                                          zona=zona['ZONA'],
                                                                                                                      periodo=ruta['PERIODO']

                                                                                                                      ))

            arcpy.mapping.ExportToPDF(mxd, out_croquis, "PAGE_LAYOUT")
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

            mxd = arcpy.mapping.MapDocument(self.path_plantilla_croquis_brigada)
            df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
            zona_mfl = arcpy.mapping.ListLayers(mxd, "TB_ZONAS")[0]
            mzs_mfl = arcpy.mapping.ListLayers(mxd, "TB_MZS_ORD")[0]
            frentes_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES")[0]
            frentes_inicio_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES_INICIO")[0]
            frentes_mfl.definitionQuery = where_manzanas
            frentes_inicio_mfl.definitionQuery = where_frentes_ini
            mzs_mfl.definitionQuery = where_manzanas
            zona_mfl.definitionQuery = where_zonas

            mxd_extent = mzs_mfl.getSelectedExtent()
            dflinea = arcpy.Polyline(
                arcpy.Array([arcpy.Point(df.extent.XMin, df.extent.YMin), arcpy.Point(df.extent.XMax, df.extent.YMax)]),
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


            if (float(distancia) <= 100):
                df.scale = df.scale * 4
            elif (float(distancia) > 100 and float(distancia) <= 490):
                df.scale = df.scale * 3
            elif (float(distancia) > 490 and  float(distancia) <=1000 ):
                df.scale = df.scale * 2.5
            elif (float(distancia) > 1000):
                df.scale = df.scale * 2

            print 'df.scale>>>',df.scale

            print 'distancia>>>', distancia

            if (float(distancia)>490):
                print 'distanciaX>>>',distanciaX
                print 'distanciaY>>>', distanciaY
                if (distanciaX  < distanciaY):

                    print 'largo>>>'
                    mxd_extent.YMax = float(mxd_extent.YMax) + 0.0005
                    mxd_extent.XMax = float(mxd_extent.XMax) - 0.004
                else:
                    print 'ancho>>>'
                    mxd_extent.YMax = float(mxd_extent.YMax) + 0.002
                    mxd_extent.XMax = float(mxd_extent.XMax) - 0.001
                df.extent = mxd_extent
                df.scale = df.scale * 1.3
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
s.procesar_croquis_listado(cod_oper ='95',codsede='15',programacion=0,importar_capas=0)

