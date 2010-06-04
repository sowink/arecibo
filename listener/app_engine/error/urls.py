from django.conf.urls.defaults import *
from error.views import LatestEntriesFeed

urlpatterns = patterns('',
    url(r'^feed/$', LatestEntriesFeed(), name="rss"),
    url(r'^list/$', 'error.views.errors_list', name="error-list"),
    url(r'^groups/$', 'error.views.groups_list', name="group-list"),
    url(r'^view/(?P<pk>[\w-]+)/$', 'error.views.error_view', name="error-view"),    
    url(r'^send/created/(?P<pk>[\w-]+)/$', 'error.views.send_signal', name="error-created"),    
)
