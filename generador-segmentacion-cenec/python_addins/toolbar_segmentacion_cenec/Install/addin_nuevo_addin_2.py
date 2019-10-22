import arcpy ,os
import pythonaddins

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH_TOOLBOX = os.path.join(BASE_DIR,'tbx','ToolboxSegmentacionCenec.tbx')
class CapaSecciones_b004(object):
    """Implementation for CapaSecciones_b004.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

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
        pythonaddins.GPToolDialog(PATH_TOOLBOX, 'DescargarInfo')


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