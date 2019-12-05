from rest_framework import serializers
from apps.territories.models import SedeOperativa
from apps.logistics.models import MarcoCensal
from apps.territories.api.serializers import SedeOperativaSerializer
from apps.logistics.api.serializers import NivelSerializer, ArticuloSerializer
from ..models import DocumentoControl, DetalleDocumentoControl


class DetalleDocumentoControlSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(allow_null=True)
    articulo = ArticuloSerializer()

    class Meta:
        model = DetalleDocumentoControl
        fields = ('id', 'doc_control', 'articulo', 'cantidad', 'observacion', 'orden')


class DocumentoControlSerializer(serializers.ModelSerializer):
    nivel = NivelSerializer(read_only=True)
    detalledocumentocontrol_set = DetalleDocumentoControlSerializer(write_only=True, many=True)

    class Meta:
        model = DocumentoControl
        fields = ('id', 'nombre', 'nivel', 'detalledocumentocontrol_set')

    def update(self, instance, validated_data):
        detalles_documento = validated_data.pop('detalledocumentocontrol_set', [])
        for detalle in detalles_documento:
            DetalleDocumentoControl.objects.filter(pk=detalle.pop('id', None)).update(**detalle)
        super(DocumentoControlSerializer, self).update(instance, validated_data)
        return instance


class GenerarDocSedeSerializer(serializers.Serializer):
    sedes = serializers.PrimaryKeyRelatedField(queryset=SedeOperativa.objects.all(), many=True)


class ImprimirSedesOperativas(SedeOperativaSerializer):
    class Meta(SedeOperativaSerializer.Meta):
        fields = ('id', 'descripcion', 'imprimir')


class imprimirMarcoCensal(serializers.ModelSerializer):
    nivel = NivelSerializer()

    class Meta:
        model = MarcoCensal
        fields = ('codigo', 'nivel', 'imprimir')
