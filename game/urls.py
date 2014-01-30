from django.conf.urls import patterns, url, include
from views.management import ChooseTribe, NewTribe, ChooseVillage, ChooseGroup
from views.game_views import EnrollView, TechnologyResearchView, BuildingView, MailBoxView, ReportsView
import api_urls



urlpatterns = patterns('',
    url(r'^$', 'game.views.game_views.main_view', name='main_view', ),
    url(r'^(?P<tribe_id>\d+)$', 'game.views.game_views.main_view', name='choose_tribe_by_id'),
    url(r'^build/$', BuildingView.as_view(), name='build',),
    url(r'^choose/$', ChooseTribe.as_view(), name='choose_tribe',),
    url(r'^choose_group/(\d*)', ChooseGroup.as_view(), name='choose_group',),
    url(r'^choose_village/(\d+)/$', ChooseVillage.as_view(),),
    url(r'^combat/simulateur/$', 'game.views.test.simulateur_combat'),
    url(r'^create/$', NewTribe.as_view(), name='create_tribe'),
    url(r'^enroll/$', EnrollView.as_view(), name='enroll_units'),
    url(r'^research_techno/$', TechnologyResearchView.as_view(), name='research_techno',),
    url(r'^view_map/(\d*)', 'game.views.game_views.view_map', name='view_map'),
    url(r'^messages/$', MailBoxView.as_view(), name='mail_box'),
    url(r'^api/', include(api_urls.urlpatterns)),

    url(r'^reports/$', ReportsView.as_view(), name='reports_list'),
)
