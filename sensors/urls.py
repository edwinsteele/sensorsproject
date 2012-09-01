from django.conf.urls import patterns, url
import sensors.views

urlpatterns = patterns('sensors.views',
    url(r'^$', 'home', name='home'),
    url(r'^latest$', sensors.views.LatestViewClass.as_view(), name='latest'),
    url(r'^recent$', sensors.views.RecentViewClass.as_view(), name='recent'),
    url(r'^canned$', sensors.views.CannedViewClass.as_view(), name='canned'),
)

