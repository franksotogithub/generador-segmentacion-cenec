import arcpy
import pythonaddins

class BtnPrueba(object):
    """Implementation for rutas_addin.btn_prueba (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.MessageBox('Select a data frame', 'INFO', 0)
        pass