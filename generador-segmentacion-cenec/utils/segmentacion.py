from utils.query import to_dict
from utils.listado_urbano import listado_ruta
from bd import cnx
import itertools
from os import path
from operator import itemgetter
import shutil
import arcpy
import expresiones_consulta_arcpy as expresion
from datetime import *
from  conf import config
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

class SegmentacionCENEC:
    zonas =[]
    def __init__(self,cant_zonas,cant_est_max):
        self.conn, self.cursor = cnx.connect_bd()
        self.cant_zonas= cant_zonas
        self.cant_est_max = cant_est_max
        self.list_aeu_manzanas =[]
        self.list_aeu = []
        self.list_aeu_manzanas_final = []
        self.list_aeu_final = []
        self.path_trabajo = config.PATH_TRABAJO
        self.path_aeu = path.join(self.path_trabajo, 'aeu')
        self.rutas =[]
        self.rutas_manzanas = []
        self.path_croquis = config.PATH_CROQUIS
        self.path_listado = config.PATH_LISTADO
        self.path_croquis_listado = config.PATH_CROQUIS_LISTADO
        self.path_plantilla_croquis_empadronador = path.join( config.PATH_PLANTILLA_CROQUIS ,'croquis_empadronador.mxd')

    def importar_capas(self):
        arcpy.env.overwriteOutput = True
        path_conexion = cnx.connect_arcpy()
        arcpy.env.workspace = path_conexion
        data = []
        for zona in self.zonas:
            data.append([zona['UBIGEO'],zona['ZONA']])

        where_zona = expresion.expresion(data, ['UBIGEO','ZONA'])
        where_ubigeo = expresion.expresion(data, ['UBIGEO'])


        list_capas = [
            ["{}.DBO.TB_MANZANA".format(config.DB_NAME), "tb_manzana", 2],
            ["{}.DBO.TB_SITIO_INTERES".format(config.DB_NAME), "tb_sitios_interes", 2],
            ["{}.DBO.TB_ZONA".format(config.DB_NAME), "tb_zona", 1],
            ["{}.DBO.TB_PUNTO_INICIO".format(config.DB_NAME), "tb_punto_inicio", 1],
            ["{}.DBO.TB_FRENTES".format(config.DB_NAME), "tb_frentes", 1],
            ["{}.DBO.TB_EJE_VIAL".format(config.DB_NAME), "tb_eje_vial", 2],
        ]

        ## 1 exportacion de datos a nivel de zona, 2 exportacion a nivel de distrito

        for i, capa in enumerate(list_capas):
            if (capa[2]==1):
                where= where_zona
            else:
                where = where_ubigeo

            x = arcpy.MakeQueryLayer_management(path_conexion, 'capa{}'.format(i),
                                                "select * from {} where  {}  ".format(capa[0], where))

            temp = arcpy.CopyFeatures_management(x, '{}/{}'.format(self.path_trabajo,capa[1]))


    def obtener_zonas(self):
        query_zonas = """
                begin
                    declare @table TABLE(
                    coddpto varchar(2),
                    codprov varchar(2),
                    coddist varchar(2),
                    ubigeo varchar(6),
                    zona varchar(6)
                    codccpp varchar(5),
                    departamento varchar(100),
                    provincia varchar(100),
                    distrito varchar(100),
                    nomccpp varchar(100)
                    );

                    select top {cant_zonas} a.CODDPTO,a.CODPROV,a.CODDIST,a.UBIGEO,a.ZONA,a.CODCCPP,a.DEPARTAMENTO,a.PROVINCIA,a.DISTRITO,a.NOMCCPP from DBO.TB_ZONA a
                    where a.flag_proc_segm=0 
                    order by 1,2

                    insert @table
                    select top {cant_zonas} a.CODDPTO,a.CODPROV,a.CODDIST,a.UBIGEO,a.ZONA,a.CODCCPP,a.DEPARTAMENTO,a.PROVINCIA,a.DISTRITO,a.NOMCCPP from DBO.TB_ZONA a
                    where a.flag_proc_segm = 0 
                    order by 1,2
                    
                    update  a
                    set a.flag_proc_segm = 1
                    from DBO.TB_ZONA a
                    where ubigeo+zona in (select UBIGEO+ZONA from @table)
                end
        
        """.format(cant_zonas=self.cant_zonas)
        self.zonas = to_dict(self.cursor.execute(query_zonas))
        self.conn.commit()


    def obtener_rutas(self):
        query_rutas = """
                begin
                    select  CODDPTO,	DEPARTAMENTO,	BRIGADA	,RUTA from [dbo].[SEGM_U_RUTA]
                end
        """
        rutas = to_dict(self.cursor.execute(query_rutas))
        return rutas

    def obtener_rutas_manzanas(self,ruta):

        query_rutas_manzanas = """
                            begin
                                select * from [dbo].[SEGM_U_RUTA_MANZANA]
                                where CODDPTO = '{coddpto}' AND RUTA ='{ruta}'
                            end
                    """.format(coddpto=ruta["CODDPTO"],ruta=ruta["RUTA"])
        rutas_manzanas = to_dict(self.cursor.execute(query_rutas_manzanas))
        return rutas_manzanas



    def llave(self,x):
        return '{}{}{}'.format(x['UBIGEO'] , x['ZONA'] , x['AEU'])

    def crear_aeus(self):
        self.manzanas = sorted (self.manzanas,key = lambda k:k['FALSO_COD'])
        self.list_aeu = []
        self.list_aeu_manzanas = []
        numero_aeu=1
        cant_est_agrupados=0
        anterior_manzana = 0 #manzana inicial

        for manzana in self.manzanas:
            m=manzana.copy()
            cant_est=m['CANT_EST']
            if (cant_est > self.cant_est_max):
                if anterior_manzana == 1:  # la anterior manzana es una menor o igual a 16 viviendas
                    if cant_est_agrupados != 0:
                        numero_aeu = numero_aeu + 1

                cant_est_agrupados = 0
                anterior_manzana = 2  #La manzana nueva tiene mas de self.cant_est_max

                #####partiendo la manzana

                division = float(cant_est) / self.cant_est_max
                cant_aeus = int(math.ceil(division))
                residuo = cant_est % cant_aeus
                est_aeu = cant_est / cant_aeus
                i = 0
                est_aeu_aux = 0

                for i in range(cant_aeus):
                    n=m.copy()

                    if i>0:
                        numero_aeu = numero_aeu + 1

                    if residuo > 0:
                        residuo = residuo - 1
                        est_aeu_aux = est_aeu +1

                    else:
                        est_aeu_aux = est_aeu
                    n['CANT_EST'] = est_aeu_aux
                    n['AEU'] = numero_aeu
                    self.list_aeu_manzanas.append(n)
            else:
                cant_est_agrupados = cant_est_agrupados + cant_est


                if (anterior_manzana == 2 or anterior_manzana == 0):  #
                    cant_est_agrupados = cant_est
                    if anterior_manzana == 2:
                        numero_aeu = numero_aeu + 1

                else:

                    if (cant_est_agrupados <= self.cant_est_max):
                        numero_aeu = numero_aeu

                    else:
                        cant_est_agrupados= cant_est
                        numero_aeu = numero_aeu + 1

                anterior_manzana = 1
                m['AEU']=numero_aeu
                self.list_aeu_manzanas.append(m)



        for key, group in itertools.groupby(self.list_aeu_manzanas, key=lambda x:self.llave(x)):
            cant_est=0
            aeu=''
            ubigeo=''
            zona=''
            for el in list(group):
                cant_est = int(el['CANT_EST']) + cant_est
                aeu=el['AEU']
                ubigeo = el['UBIGEO']
                zona = el['ZONA']

            self.list_aeu.append({'UBIGEO':ubigeo,'ZONA':zona,'AEU':aeu,'CANT_EST':cant_est})



    def obtener_manzanas(self,zona):
        query_manzanas = """
        select UBIGEO,ZONA,MANZANA,CANT_EST,FALSO_COD from [DBO].[TB_MANZANA] 
        where UBIGEO = '{ubigeo}' and ZONA = '{zona}'    
        """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'])
        self.manzanas = to_dict(self.cursor.execute(query_manzanas))

    def procesar_aeus(self):

        if arcpy.Exists(self.path_aeu):
            arcpy.Delete_management(self.path_aeu)

        for zona in self.zonas:
            self.obtener_manzanas(zona)
            self.crear_aeus()
            self.crear_limite_aeus()
            self.list_aeu_manzanas_final  =self.list_aeu_manzanas_final + self.list_aeu_manzanas
            self.list_aeu_final  = self.list_aeu_final +self.list_aeu


    def exportando_resultados_aeu(self):
        insert_sql = ""
        for count, aeu in enumerate(self.list_aeu_final, 1):
            if count == 1:
                insert_sql = """ insert into [SEGM_U_AEU](ubigeo,zona,aeu,cant_est)  values """
            insert_sql = """{insert_sql} ('{ubigeo}','{zona}','{aeu}',{cant_est}) """.format(insert_sql=insert_sql,
                                                                                             ubigeo=aeu['UBIGEO'],
                                                                                             zona=aeu['ZONA'],
                                                                                             aeu=aeu['AEU'],
                                                                                             cant_est=aeu['CANT_EST'])

            if count < len(self.list_aeu_final):
                insert_sql = """{insert_sql},""".format(insert_sql=insert_sql)


        self.cursor.execute(insert_sql)
        self.conn.commit()

    def exportando_resultados_aeu_manzana(self):
        insert_sql = ""
        for count, aeu in enumerate(self.list_aeu_manzanas_final, 1):
            if count == 1:
                insert_sql = """ insert into [SEGM_U_AEU_MANZANA](ubigeo,zona,aeu,manzana,cant_est)  values """
            insert_sql = """{insert_sql} ('{ubigeo}','{zona}','{aeu}','{manzana}',{cant_est}) """.format(insert_sql=insert_sql,
                                                                                             ubigeo=aeu['UBIGEO'],
                                                                                             zona=aeu['ZONA'],
                                                                                             aeu=aeu['AEU'],
                                                                                             manzana=aeu['MANZANA'],
                                                                                             cant_est=aeu['CANT_EST'])
            if count < len(self.list_aeu_manzanas_final):
                insert_sql = """{insert_sql},""".format(insert_sql=insert_sql)





        self.cursor.execute(insert_sql)
        self.conn.commit()

    def exportar_resultados(self):
        self.exportando_resultados_aeu()
        self.exportando_resultados_aeu_manzana()

    def exportar_croquis(self):
        path_manzana=path.join(self.path_trabajo, 'tb_manzana')
        arcpy.MakeFeatureLayer_management(path_manzana, "tb_manzana")
        for aeu in self.list_aeu:
            list_aeu_man=[[d['UBIGEO'],d['ZONA'],d['MANZANA']] for d in self.list_aeu_manzanas if(d['AEU']==aeu['AEU'] and d['UBIGEO']==aeu['UBIGEO'] and d['ZONA']== aeu['ZONA'] )]
            where_manzanas = expresion.expresion_2(list_aeu_man,[["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])
            tb_manzana_selec=arcpy.SelectLayerByAttribute_management("tb_manzana", "NEW_SELECTION", where_manzanas)

    def crear_limite_aeus(self):
        path_manzana=path.join(self.path_trabajo, 'tb_manzana')
        arcpy.MakeFeatureLayer_management(path_manzana, "tb_manzana")
        for aeu in self.list_aeu:
            list_aeu_man=[[d['UBIGEO'],d['ZONA'],d['MANZANA']] for d in self.list_aeu_manzanas if(d['AEU']==aeu['AEU'] and d['UBIGEO']==aeu['UBIGEO'] and d['ZONA']== aeu['ZONA'] )]
            where_manzanas = expresion.expresion_2(list_aeu_man,[["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])
            tb_manzana_selec=arcpy.SelectLayerByAttribute_management("tb_manzana", "NEW_SELECTION", where_manzanas)
            if (int(arcpy.GetCount_management(tb_manzana_selec).getOutput(0)) > 0):
                out_feature_1 = "in_memory/Buffer{}{}{}".format(aeu["UBIGEO"],aeu["ZONA"],aeu["AEU"])
                out_feature_2 = "in_memory/FeatureToLine{}{}{}".format(aeu["UBIGEO"],aeu["ZONA"],aeu["AEU"])
                out_feature_3 = "in_memory/FeatureToPolygon{}{}{}".format(aeu["UBIGEO"],aeu["ZONA"],aeu["AEU"])
                out_feature = "in_memory/out_feature{}{}{}".format(aeu["UBIGEO"],aeu["ZONA"],aeu["AEU"])
                arcpy.Buffer_analysis(tb_manzana_selec, out_feature_1, '5 METERS', 'FULL', 'FLAT', 'LIST')
                arcpy.Dissolve_management(out_feature_1, out_feature)

                add_fields = [ ["UBIGEO","TEXT",aeu["UBIGEO"]],["ZONA","TEXT",aeu["ZONA"]],["AEU","TEXT",aeu["AEU"]],["CANT_EST","SHORT",aeu["CANT_EST"]]]

                for add_field in add_fields:
                    arcpy.AddField_management(out_feature, add_field[0], add_field[1])
                    arcpy.CalculateField_management(out_feature,add_field[0], add_field[2], "PYTHON_9.3")

                if arcpy.Exists(self.path_aeu):
                    arcpy.Append_management(out_feature, self.path_aeu, "NO_TEST")
                else:
                    arcpy.CopyFeatures_management(out_feature, self.path_aeu)


    def procesar_listado_croquis(self):
        rutas = self.obtener_rutas()
        for ruta in rutas:
            rutas_manzanas=self.obtener_rutas_manzanas(ruta)
            info = [ruta,rutas_manzanas]
            output = path.join(self.path_listado,'{departamento}-{ruta}.pdf'.format(departamento=ruta['DEPARTAMENTO'],ruta=ruta['RUTA']))
            self.zonas = [  {'UBIGEO':e[0],'ZONA': e[1],'DEPARTAMENTO':e[2],'PROVINCIA':e[3],
                             'DISTRITO':e[4],'CODDPTO':e[5],'CODPROV':e[6],'CODDIST':e[7],'CODCCPP':e[8],'NOMCCPP':e[9],'BRIGADA':e[10],'RUTA':ruta['RUTA'],'PERIODO':e[11]
                             }   for e in   list(set((d['UBIGEO'], d['ZONA'] ,d['DEPARTAMENTO'],d['PROVINCIA'],d['DISTRITO'],d['CODDPTO'],d['CODPROV'],d['CODDIST'],d['CODCCPP'],d['NOMCCPP'],d['BRIGADA'],d['PERIODO']) for d in rutas_manzanas))]

            for zona in self.zonas:
                filter_rutas_manzanas = [ d for d in rutas_manzanas if (d['UBIGEO'] == zona['UBIGEO'] and d['ZONA'] == zona['ZONA'])]
                cant_est=0
                mensaje_manzanas ='El area de empadronamiento comprende las manzanas '
                for count,ruta_manzana in enumerate(filter_rutas_manzanas,1):
                    cant_est = cant_est + int(ruta_manzana['CANT_EST'])
                    if count==len(filter_rutas_manzanas):
                        mensaje_manzanas = "{} {}".format(mensaje_manzanas,ruta_manzana['MZ'])
                    else:
                        mensaje_manzanas = "{} {},".format(mensaje_manzanas, ruta_manzana['MZ'])

                zona['CANT_EST']=cant_est
                zona['FRASE'] = mensaje_manzanas


            self.importar_capas()
            output_listado=listado_ruta(info, output)
            list_out_croquis=self.croquis_ruta(info)
            list_out_croquis.append(output_listado)
            pdfDoc = arcpy.mapping.PDFDocumentCreate(path.join(self.path_croquis_listado, '{departamento}-{brigada}-{ruta}.pdf'.format(departamento=ruta['DEPARTAMENTO'],brigada=ruta['BRIGADA'],ruta=ruta['RUTA'])))

            for el in list_out_croquis:
                pdfDoc.appendPages(el)
            pdfDoc.saveAndClose()

    def croquis_ruta(self,info):
        list_out_croquis=[]
        for zona in self.zonas:
            ruta = info[0]
            rutas_manzanas = info[1]
            manzanas= list(set((d['UBIGEO'], d['ZONA'],d['MZ']) for d in rutas_manzanas if (d['UBIGEO']==zona['UBIGEO'] and d['ZONA']==zona['ZONA']) ))
            frentes_ini = [(d[0], d[1],d[2],1) for d in manzanas]

            where_manzanas = expresion.expresion_2(manzanas,[["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])
            where_frentes_ini = expresion.expresion_2(frentes_ini,
                                                   [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"],["FRENTE_ORD", "SHORT"]])
            where_zonas = expresion.expresion_2([ [zona['UBIGEO'], zona['ZONA']] ], [["UBIGEO", "TEXT"], ["ZONA", "TEXT"]])


            mxd = arcpy.mapping.MapDocument(self.path_plantilla_croquis_empadronador)
            df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
            zona_mfl = arcpy.mapping.ListLayers(mxd, "TB_ZONAS")[0]
            mzs_mfl = arcpy.mapping.ListLayers(mxd, "TB_MZS_ORD")[0]
            frentes_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES")[0]
            frentes_inicio_mfl = arcpy.mapping.ListLayers(mxd, "TB_FRENTES_INICIO")[0]

            frentes_mfl.definitionQuery = where_manzanas
            frentes_inicio_mfl.definitionQuery = where_frentes_ini

            mzs_mfl.definitionQuery = where_manzanas
            zona_mfl.definitionQuery = where_zonas
            df.extent = zona_mfl.getSelectedExtent()

            list_text_el = [["CODDPTO", zona["CODDPTO"]] , ["CODPROV", zona['CODPROV']], ["CODDIST", zona['CODDIST']]]
            list_text_el = list_text_el +   [["CODCCPP", zona['CODCCPP']], ["DEPARTAMENTO", zona['DEPARTAMENTO']]]
            list_text_el = list_text_el +   [["PROVINCIA", zona['PROVINCIA']], ["DISTRITO", zona['DISTRITO']], ["NOMCCPP",zona['NOMCCPP']]]
            list_text_el = list_text_el + [["BRIGADA",zona["BRIGADA"]],["RUTA",zona["RUTA"]],["CANT_EST", '{}'.format(zona["CANT_EST"])], ["FRASE", zona["FRASE"]],["PERIODO",'{}'.format(zona["PERIODO"])]]


            for text_el in list_text_el:

                el=arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", text_el[0])[0]
                el.text=text_el[1]

            out_croquis = path.join(self.path_croquis,
                               '{departamento}-{ruta}-{zona}.pdf'.format(departamento=ruta['DEPARTAMENTO'], ruta=ruta['RUTA'],zona=zona['ZONA']))
            arcpy.mapping.ExportToPDF(mxd, out_croquis, "PAGE_LAYOUT")
            list_out_croquis.append(out_croquis)
        return list_out_croquis


    def procesar(self):
        #print datetime.today()
        #self.procesar_listado_croquis()
        print datetime.today()
        self.obtener_zonas()
        print datetime.today()
        self.importar_capas()
        print datetime.today()
        self.procesar_aeus()
        print datetime.today()
        self.exportar_resultados()
        print datetime.today()



s= SegmentacionCENEC(cant_zonas=1,cant_est_max=150)
s.procesar()



