from django.conf.urls import patterns, url, include
from views.api import router, MapView

urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^map/(.(?P<format>\w*))?', MapView.as_view()),
    #url(r'^map/tiles/(.(?P<format>\w*))?', TilesView.as_view()),
)
