import arcpy ,os
import pythonaddins

BASE_DIR = os.path.abspath(__file__)


class ImportarInformacion_b001(object):
    """Implementation for ImportarInformacion_b001.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(r'\\192.168.201.115\cpv2017\SegmentacionRural_Procesamiento\TBX\ToolbarSegmRuralV3.tbx', 'ImportInfo')

class CrearCapaRutas_b002(object):
    """Implementation for CrearCapaRutas_b002.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(r'\\192.168.201.115\cpv2017\SegmentacionRural_Procesamiento\TBX\ToolbarSegmRuralV3.tbx', 'CrearFcRutas')

class OrdenarCCPP_b003(object):
    """Implementation for OrdenarCCPP_b003.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(r'\\192.168.201.115\cpv2017\SegmentacionRural_Procesamiento\TBX\ToolbarSegmRuralV3.tbx', 'CrearFcCcpps')

class CapaSecciones_b004(object):
    """Implementation for CapaSecciones_b004.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(r'\\192.168.201.115\cpv2017\SegmentacionRural_Procesamiento\TBX\ToolbarSegmRuralV3.tbx', 'CrearcapadeSecciones')

class TbFinales_b005(object):
    """Implementation for TbFinales.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(r'\\192.168.201.115\cpv2017\SegmentacionRural_Procesamiento\TBX\ToolbarSegmRuralV3.tbx', 'GenerarTablasFinales')

class CargaBD_b006(object):
    """Implementation for CargaBD_b006.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(r'\\192.168.201.115\cpv2017\SegmentacionRural_Procesamiento\TBX\ToolbarSegmRuralV3.tbx', 'CargarInfo')