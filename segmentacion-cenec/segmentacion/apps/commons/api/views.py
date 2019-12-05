from django.shortcuts import get_object_or_404
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from django_filters.rest_framework import DjangoFilterBackend
from apps.territories.models import SedeOperativa
from apps.commons.models import Nivel
from apps.logistics.models import AbastecimientoCapacitacion
from ..models import DocumentoControl, DetalleDocumentoControl
from ..utils import GenerarDocControl
from .serializers import (
    GenerarDocSedeSerializer, ImprimirSedesOperativas, imprimirMarcoCensal, DocumentoControlSerializer,
    DetalleDocumentoControlSerializer
)


# generar doc
from apps.logistics.models import MarcoCensal


class GeneraDocMixin:
    def generar_doc(self, sedes):
        """
        Genera documento de control para todos los niveles
        :param sedes: codigo de la sede operativa
        """
        for cod_sede in sedes:
            sedes = SedeOperativa.objects.filter(pk=cod_sede)
            sede = sedes.first()
            marco_censal = MarcoCensal.objects.filter(cod_sede_id=cod_sede).order_by('codigo')
            # Flag que indica que se esta generando el archivo
            marco_censal.update(imprimir=2)
            sedes.update(imprimir=2)
            # Generar los documento decontrol
            doc_control = GenerarDocControl(sede=sede)
            doc_control.genera(niveles=[1, 2], items=marco_censal)
            # Flag que indica que se termino de genera al archivo
            marco_censal.update(imprimir=1)
            sedes.update(imprimir=1)

    def genera_doc_capacitacion(self, niveles):
        for nivel in niveles:
            doc_control = GenerarDocControl(nivel=nivel)
            doc_control.capacitacion()


class GenerarDocViewset(GeneraDocMixin, GenericViewSet):
    queryset = DocumentoControl.objects.all()

    def list(self, request, *args, **kwargs):
        sedesobj = SedeOperativa.objects.all().order_by('id')
        serializer = ImprimirSedesOperativas(sedesobj, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='lista-documentos/(?P<sede_id>[0-9]{2})',
            serializer_class=imprimirMarcoCensal)
    def lista_documentos(self, request, *args, **kwargs):
        sede_id = kwargs.get('sede_id', None)
        marco = MarcoCensal.objects.filter(cod_sede_id=sede_id).order_by('codigo')
        serializer = self.serializer_class(marco, many=True)
        return Response(serializer.data)

    @action(methods=['patch'], detail=False, url_path='sedes', serializer_class=GenerarDocSedeSerializer)
    def generar_sedes(self, request, *args, **kwargs):
        """
        Generar documento de control a partir de un listado de sedes operativas
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        sedes = serializer.data.get("sedes", [])
        self.generar_doc(sedes)
        sedesobj = SedeOperativa.objects.filter(id__in=sedes)
        serializer_response = ImprimirSedesOperativas(sedesobj, many=True)
        return Response(serializer_response.data)

    @action(methods=['patch'], detail=False, url_path='capacitacion', serializer_class=GenerarDocSedeSerializer)
    def generar_capacitacion(self, request, *args, **kwargs):
        cod_niveles = request.data.get("niveles", [])
        niveles = Nivel.objects.filter(id__in=cod_niveles)
        abastecimiento = AbastecimientoCapacitacion.objects.filter(nivel__in=niveles)
        abastecimiento.update(imprimir=2)
        self.genera_doc_capacitacion(niveles=niveles)
        abastecimiento.update(imprimir=1)
        return Response({"success": True})


class DocControlViewset(mixins.ListModelMixin, GenericViewSet):
    queryset = DocumentoControl.objects.all().order_by('nivel_id')
    serializer_class = DocumentoControlSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['nivel_id', 'nivel__tipo_operacion']

    @action(methods=['GET'], detail=True, serializer_class=DetalleDocumentoControlSerializer)
    def detalle(self, request, *args, **kwargs):
        doc_control_id = kwargs.get('pk')
        detalles_documento = DetalleDocumentoControl.objects.filter(doc_control_id=doc_control_id).order_by('orden')
        serializer = self.serializer_class(detalles_documento, many=True)
        return Response(serializer.data)

    @action(methods=['PATCH'], detail=True, url_path='actualizar-detalle')
    def actualizar_detalle(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
