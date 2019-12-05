from rest_framework.routers import DefaultRouter
from .views import GenerarDocViewset, DocControlViewset


router = DefaultRouter()
router.register('generar/doc-control', GenerarDocViewset)
router.register('doc-control', DocControlViewset)
app_name = 'printings'
urlpatterns = router.urls
