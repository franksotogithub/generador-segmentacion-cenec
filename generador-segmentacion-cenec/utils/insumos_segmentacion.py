# -*- coding: utf-8 -*-
from utils.query import to_dict
from utils.listado_urbano import listado_ruta, listado_brigada
from bd import cnx
import itertools
from os import path
from operator import itemgetter
import shutil
import arcpy
import expresiones_consulta_arcpy as expresion
from datetime import *
from conf import config

arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

UBIGEO = '{}'.format(sys.argv[1])

class InsumosSegmentacionCENEC:
    zonas = []

    def __init__(self, distritos):
        self.conn, self.cursor = cnx.connect_bd()


        self.path_trabajo = config.PATH_TRABAJO_PROCESAR
        self.path_aeu = path.join(self.path_trabajo, 'aeu')
        self.rutas = []
        self.rutas_manzanas = []


        self.distritos = distritos

    #def actualizar_flag_proc_segm(self):
    #    QUERY = """
    #    begin
    #        SELECT * FROM TB_DISTRITO
    #    end
    #    """
    #    cursor.execute(QUERY)
    #    cnn.commit()

    def importar_capas_insumos(self):
        arcpy.env.overwriteOutput = True
        path_conexion = cnx.connect_arcpy()
        arcpy.env.workspace = path_conexion
        data = []

        for distrito in self.distritos:
            data.append([distrito['UBIGEO']])

        where_ubigeo = expresion.expresion(data, ['UBIGEO'])

        list_capas = [
            ["{}.DBO.TB_MANZANA".format(config.DB_NAME), "tb_manzana_procesar", 1],
            ["{}.DBO.TB_EJE_VIAL".format(config.DB_NAME), "tb_eje_vial_procesar", 2],
            ["{}.DBO.TB_ZONA".format(config.DB_NAME), "tb_zona_procesar", 2],

        ]

        where_ubigeo = "({}) and FASE=0 ".format(where_ubigeo)

        for i, capa in enumerate(list_capas):
            print capa[1]
            if capa[2]==2:
                x = arcpy.MakeQueryLayer_management(path_conexion, 'capa{}'.format(i),
                                                    "select * from {} where  {}  ".format(capa[0], where_ubigeo))
            else:
                x = arcpy.MakeQueryLayer_management(path_conexion, 'capa{}'.format(i),
                                                    "select * from {} where  {}  ".format(capa[0], where_ubigeo))

            temp = arcpy.CopyFeatures_management(x, '{}/{}'.format(self.path_trabajo, capa[1]))

    def llave(self, x):
        return '{}{}{}'.format(x['UBIGEO'], x['ZONA'], x['AEU'])


    def exportando_resultados(self):
        insert_sql = ""
        arcpy.env.overwriteOutput = True
        path_conexion = cnx.connect_arcpy()
        arcpy.env.workspace = path_conexion

        list_capas = [
            [self.path_aeu, path.join(path_conexion, '{}.DBO.SEGM_U_AEU'.format(config.DB_NAME))]
        ]

        for zona in self.zonas:
            sql_query = """
                    DELETE DBO.SEGM_U_AEU where ubigeo='{ubigeo}' and zona='{zona}'
                    """.format(ubigeo=zona['UBIGEO'], zona=zona['ZONA'])
            self.cursor.execute(sql_query)
            self.conn.commit()

        for i, el in enumerate(list_capas):  #
            a = arcpy.MakeFeatureLayer_management(el[0], "MakeFeatureLayer{}".format(i))
            arcpy.Append_management(a, el[1], "NO_TEST")


    def exportar_resultados(self):
        self.exportando_resultados_aeu()
        #self.exportando_resultados_aeu_manzana()

    def crear_limite_manzanas(self):
        arcpy.env.overwriteOutput = True
        path_manzana = path.join(self.path_trabajo, 'tb_manzana_procesar')
        path_eje_vial = path.join(self.path_trabajo, 'tb_eje_vial_procesar')
        path_zona = path.join(self.path_trabajo, 'tb_zona_procesar')

        fragmentos=arcpy.FeatureToPolygon_management([path_eje_vial,path_zona,path_manzana], path.join(self.path_trabajo,'fragmentos'),"10 Meters","NO_ATTRIBUTES", "" )
        x=arcpy.SpatialJoin_analysis(fragmentos,path_manzana, path.join(self.path_trabajo,'fragmentos_manzanas_x') ,'JOIN_ONE_TO_ONE','KEEP_ALL','','HAVE_THEIR_CENTER_IN')
        arcpy.SelectLayerByAttribute_management(x,"NEW_SELECTION"," Join_Count=1")

        dissolveFields=['CODDPTO',	'CODPROV'	,'CODDIST'	,'CODZONA',	'SUFZONA',	'CODMZNA',	'UBIGEO	'
                        'CODCCPP'	,'DEPARTAMENTO'	,'PROVINCIA'	,'DISTRITO'	,'NOMCCCPP'
                        'SUF_MZNA'	,'PK_MANZANA','ZONA',	'MANZANA']

        fragmentos_manzanas=arcpy.Dissolve_management(x, path.join(self.path_trabajo,'fragmentos_manzanas'),dissolveFields, "",
                          "SINGLE_PART", "DISSOLVE_LINES")

        #arcpy.MakeFeatureLayer_management(path_manzana, "tb_manzana_procesar")




        #for aeu in self.list_aeu:
#
        #    list_aeu_man = [[d['UBIGEO'], d['ZONA'], d['MANZANA']] for d in self.list_aeu_manzanas if
        #                    (d['AEU'] == aeu['AEU'] and d['UBIGEO'] == aeu['UBIGEO'] and d['ZONA'] == aeu['ZONA'])]
        #    where_manzanas = expresion.expresion_2(list_aeu_man,
        #                                           [["UBIGEO", "TEXT"], ["ZONA", "TEXT"], ["MANZANA", "TEXT"]])
        #    tb_manzana_selec = arcpy.SelectLayerByAttribute_management("tb_manzana_procesar", "NEW_SELECTION",
        #                                                               where_manzanas)
        #    if (int(arcpy.GetCount_management(tb_manzana_selec).getOutput(0)) > 0):
        #        out_feature_1 = "in_memory/Buffer{}{}{}".format(aeu["UBIGEO"], aeu["ZONA"], aeu["AEU"])
        #        out_feature = "in_memory/out_feature{}{}{}".format(aeu["UBIGEO"], aeu["ZONA"], aeu["AEU"])
        #        arcpy.Buffer_analysis(tb_manzana_selec, out_feature_1, '5 METERS', 'FULL', 'FLAT', 'LIST')
        #        arcpy.Dissolve_management(out_feature_1, out_feature)
        #        add_fields = [["UBIGEO", "TEXT", "'{}'".format(aeu["UBIGEO"])],
        #                      ["ZONA", "TEXT", "'{}'".format(aeu["ZONA"])],
        #                      ["AEU", "TEXT", "'{}'".format(str(aeu["AEU"]).zfill(3))],
        #                      ["CANT_EST", "SHORT", int(aeu["CANT_EST"])]]
#
        #        for add_field in add_fields:
        #            arcpy.AddField_management(out_feature, add_field[0], add_field[1])
        #            arcpy.CalculateField_management(out_feature, add_field[0], add_field[2], "PYTHON_9.3")
#
        #        if arcpy.Exists(self.path_aeu):
        #            arcpy.Append_management(out_feature, self.path_aeu, "NO_TEST")
        #        else:
        #            arcpy.CopyFeatures_management(out_feature, self.path_aeu)


    def procesar_distritos(self):
        print datetime.today()
        self.importar_capas_insumos()
        print datetime.today()
        self.crear_limite_manzanas()
        print datetime.today()
        #self.exportar_resultados()
        #print datetime.today()


s = InsumosSegmentacionCENEC(distritos=[{'UBIGEO': UBIGEO}])
s.procesar_distritos()

