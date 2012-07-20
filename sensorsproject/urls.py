from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'sensors.views.home', name='home'),
    url(r'^sensors$', 'sensors.views.home', name='home'),
    url(r'^sensors/(?P<year>\d{4})/$', 'sensors.views.year_detail'),
    url(r'^sensors/(?P<year>\d{4})/(?P<month>\d{2})/$', 'sensors.views.month_detail'),
    url(r'^sensors/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d+)/$', 'sensors.views.day_detail'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
