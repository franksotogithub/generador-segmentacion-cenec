import arcpy, pymssql


arcpy.env.overwriteOutput = True

gdb = arcpy.GetParameter(0)

lyrScr = r'\\192.168.201.115\cpv2017\SegmentacionRural_Procesamiento\Insumos\SCR_FINAL.lyr'


def crearFeature(ubigeo, dataset):

    nombreFc = 'SCR_{}'.format(ubigeo)
    Campos_SCR = [("UBIGEO", "TEXT", "6"), ("SCR", "SHORT", "5")]
    fc_tmp = arcpy.CreateFeatureclass_management("in_memory", '{}_TMP'.format(nombreFc), "POLYGON", "#", "#", "#", arcpy.SpatialReference(4326))

    for n in Campos_SCR:
        if n[1] == "TEXT":
            arcpy.AddField_management(fc_tmp, n[0], n[1], '#', '#', n[2], '#', 'NULLABLE', 'NON_REQUIRED', '#')
        else:
            arcpy.AddField_management(fc_tmp, n[0], n[1], n[2], '#', '#', '#', 'NULLABLE', 'NON_REQUIRED', '#')

    scr = arcpy.CreateFeatureclass_management(dataset, nombreFc, "POLYGON", fc_tmp, "#", "#", arcpy.SpatialReference(4326))

    arcpy.AssignDefaultToField_management(scr, 'UBIGEO', ubigeo)

    return scr


def fcCcppRutas(gdb, ubigeo):
    ccppsRuta = '{}\Procesamiento\CCPPRUTAS_{}'.format(gdb, ubigeo)
    return ccppsRuta


def fcRutas(gdb, ubigeo):
    rutas = '{}\Procesamiento\RUTAS_{}'.format(gdb, ubigeo)
    return rutas


def consistencia01(ccppsRuta):
    informacion = [[1, x[0]] for x in arcpy.da.SearchCursor(ccppsRuta, ["IDCCPP", "OR_CCPP"]) if x[1] == None]
    return informacion

def consistencia02(rutas, ccppsRuta):
    informacion = []
    for x in [x[0] for x in arcpy.da.SearchCursor(rutas, ["OID@"])]:
        info = 0
        lista = [[m[0], m[1], m[2]] for m in arcpy.da.SearchCursor(ccppsRuta, ["CODCCPP", "OR_CCPP", "RUTA_TMP"], "RUTA_TMP = {}".format(x)) if m[1] <> None]
        lista.sort(key = lambda orden:(orden[2], orden[1]))
        for n in lista:
            if n[1] - info == 1:
                info = n[1]
            else:
                informacion.append([2, x])
                break

    return informacion



def validarGDB(gdb):
    informacion = []
    desc = arcpy.Describe(gdb)
    validacion = desc.basename


def validarGDB(gdb):
    informacion = []
    desc = arcpy.Describe(gdb)
    validacion = desc.basename

    if validacion[0:10] == 'BD_SEGM_R_':
        if arcpy.Exists(r'{}\Procesamiento'.format(gdb)):
            ubigeo = validacion[10:16]
            dataset = r'{}\Procesamiento'.format(gdb)
            if arcpy.Exists(r'{}\CCPPRUTAS_{}'.format(dataset, ubigeo)):
                ccppsRuta = fcCcppRutas(gdb, ubigeo)
                rutas = fcRutas(gdb, ubigeo)
                con01 = consistencia01(ccppsRuta)
                con02 = consistencia02(rutas, ccppsRuta)

                if len(con01) > 0 or len(con02) > 0:
                    informacion.extend(con01)
                    informacion.extend(con02)
                    for x in informacion:
                        if x[0] == 1:
                            arcpy.AddWarning("El ccpp {} no presenta un numero de orden en la ruta".format(x[1]))
                        elif x[0] == 2:
                            arcpy.AddWarning("La ruta: {} contiene centros poblados en orden NO correlativos".format(x[1]))
                        elif x[0] == 3:
                            arcpy.AddWarning("El centro poblado {} no existe en la base de datos (posiblemente agrego un centro poblado nuevo)".format(x[1]))
                        elif x[0] == 4:
                            arcpy.AddWarning("El centro poblado {} no se encuentra o fue eliminado, asegurese de que todos los centros poblados RURALES del distrito se encuentren presentes en la Segmentacion".format(x[1]))

                else:
                    output = crearFeature(ubigeo, dataset)
                    arcpy.SetParameterAsText(1, output)

                    params = arcpy.GetParameterInfo()

                    for param in params:
                        if '{}'.format(param.name) == 'seccion':
                            param.symbology = lyrScr

                    arcpy.RefreshActiveView()

                    mxd = arcpy.mapping.MapDocument("CURRENT")
                    for i in arcpy.mapping.ListLayers(mxd):
                        if i.name == "SCR_{}".format(ubigeo):
                            i.replaceDataSource(gdb, "FILEGDB_WORKSPACE", "SCR_{}".format(ubigeo), True)


                    arcpy.AssignDefaultToField_management(output, 'UBIGEO', ubigeo)

            else:
                arcpy.AddError("Debes asignar el orden de visita a los centros poblados")
        else:
            arcpy.AddError("OBSERVACION:")
            arcpy.AddError("No se encuentra el dataset 'Procesamiento' dentro de la GDB ingresada")
    else:
        arcpy.AddError("El dataset ingresado es incorrecto")



validarGDB(gdb)