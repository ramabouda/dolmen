#vim: set fileencoding=utf-8 :

from ..models import Report, Village, Mission
from ..serializers import ReportSerializer, ReportPermission,\
        VillageSerializer, TileRendererSerializer, MissionSerializer,\
        MissionRequestSerializer
from django.shortcuts import redirect
from rest_framework import viewsets, views
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

class ReportViewSet(viewsets.ModelViewSet):
    "A viewSet handling report display"
    serializer_class = ReportSerializer
    queryset = Report.objects.all()
    permission_classes = (ReportPermission,)

    def filter_queryset(self, queryset):
        tribe_id = self.request.session['tribe'].id
        return queryset.filter(tribe_id=tribe_id)

    def list(self, request, format='html'):
        queryset = Report.objects.filter(tribe=request.session['tribe'])
        serializer = ReportSerializer(queryset, many=True)
        return Response(serializer.data)

class MapView(views.APIView):
    def get(self, request, format=None):
        tribe = request.session['tribe']
        serializer = tribe.get_serialized_tiles()
        return Response({'tiles': serializer})

class VillageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VillageSerializer
    queryset = Village.objects.all()

    def filter_queryset(self, queryset):
        tribe_id = self.request.session['tribe'].id
        return queryset.filter(tribe_id=tribe_id)

    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk == 'current':
            return redirect('game:village-detail',
                    pk=request.session['village'].id,
                    *args, **kwargs)
        else:
            return super(VillageViewSet, self)\
                    .retrieve(request, pk=pk, *args, **kwargs)

class TilesView(views.APIView):
    def get(self, request, format=None):
        tribe = request.session['tribe']
        dicto = tribe.dispatch_tiles()
        result = TileRendererSerializer(
                dicto['seen'], many=True).data

        for item in result:
            item['seen'] = True

        result2 = TileRendererSerializer(
                dicto['unseen'], many=True,).data
        for item in result2:
            item['seen'] = False
        result.extend(result2)
        return Response({'tiles': result})

        data = [tile.update({'seen': True}) for tile in dicto['seen'].values()]
        data.extend([tile.update({'seen': False}) for tile in dicto['unseen'].values()])
        serializer = TileRendererSerializer(dicto, many=True)
        return Response({'tiles': serializer.data})

class MissionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MissionSerializer
    queryset = Mission.objects.all()

    def filter_request(self, queryset):
        tribe_id = self.request.session['tribe'].id
        return queryset.filter(group__village__tribe_id=tribe_id)

    def create(self, request):
        serializer = MissionRequestSerializer(data=request.DATA,
                            context={'request': request})
        if serializer.is_valid():
            Mission.start_mission(**serializer.object)
            return Response({'message': 'success'})
        return Response(serializer.errors)


router = DefaultRouter()
router.register(r'reports', ReportViewSet)
router.register(r'villages', VillageViewSet)
router.register(r'missions', MissionViewSet)
