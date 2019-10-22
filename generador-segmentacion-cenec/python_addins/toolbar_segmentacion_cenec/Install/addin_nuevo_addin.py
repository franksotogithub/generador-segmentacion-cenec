import arcpy
import pythonaddins

class AgruparAesBtn(object):
    """Implementation for addin_nuevo_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.cursor = 3
        self.shape = "Line"

    def onClick(self):
        pass

    def onLine(self, line_geometry):
        array = arcpy.Array()
        part = line_geometry.getPart(0)
        for pt in part:
            array.add(pt)
        #array.add(line_geometry.firstPoint)
        polygon = arcpy.PolyLine(array)

        rutaDB=arcpy.env.workspace
        #arcpy.env.scratchWorkspace = rutaFD


        if arcpy.Exists("in_memory/polygons"):
            arcpy.Delete_management("in_memory/polygons")
        arcpy.RefreshActiveView()
        arcpy.CopyFeatures_management(polygon, "in_memory/polygons")
        mxd = arcpy.mapping.MapDocument("CURRENT")
        aes = [x for x in arcpy.mapping.ListLayers(mxd) if x.name[0:3] == 'AES'][0]
        poligono = [x for x in arcpy.mapping.ListLayers(mxd) if x.name == 'polygons'][0]
        arcpy.SelectLayerByLocation_management(aes, "INTERSECT", poligono, "#", "NEW_SELECTION")
        suma = sum([x[0] for x in arcpy.da.SearchCursor(aes, ["CANT_EST"])])
        with arcpy.da.UpdateCursor(aes, ["RUTA"]) as cursor:
            for c in cursor:
                c[3] =1
                cursor.updateRow(c)
        arcpy.RefreshActiveView()
        pythonaddins.MessageBox("Establecimientos Totales: {}".format(suma), "INEI", 0)

class CargaBD_b006(object):
    """Implementation for CargaBD_b006.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class CrearCapaRutas_b002(object):
    """Implementation for CrearCapaRutas_b002.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class DescargarInformacion_b001(object):
    """Implementation for DescargarInformacion_b001.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class OrdenarCCPP_b003(object):
    """Implementation for OrdenarCCPP_b003.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class TbFinales_b005(object):
    """Implementation for TbFinales.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass