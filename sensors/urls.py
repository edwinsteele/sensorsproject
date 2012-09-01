from django.conf.urls import patterns, url

urlpatterns = patterns('sensors.views',
    url(r'^$', 'home', name='home'),
    url(r'^latest$', 'latest_detail', name='latest'),
    url(r'^recent$', 'recent_detail', name='recent'),
    url(r'^canned$', 'canned_detail', name='canned'),
    url(r'^(?P<year>\d{4})/$', 'year_detail'),
    url(r'^(?P<year>\d{4})/(?P<month>\d{2})/$', 'month_detail'),
    url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d+)/$', 'day_detail'),
)

