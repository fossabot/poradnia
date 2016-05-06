# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.http import HttpResponseServerError
from django.template import Context, loader
from django.views.generic import TemplateView

admin.autodiscover()

urlpatterns = [
    url(r'^$',
        TemplateView.as_view(template_name='pages/home.html'),
        name="home"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^navsearch/', include('navsearch.urls', namespace="navsearch")),

    # User management
    url(r'^uzytkownik/klucze', include('keys.urls', namespace="keys")),
    url(r'^uzytkownik/', include("users.urls", namespace="users")),
    url(r'^konta/', include('allauth.urls')),

    # Flatpages
    url(r'^strony/', include('django.contrib.flatpages.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    # Poradnia
    url(r'^sprawy/', include('cases.urls', namespace='cases')),
    url(r'^listy/', include('letters.urls', namespace='letters')),
    url(r'^wydarzenia/', include('events.urls', namespace='events')),
    url(r'^porady/', include('advicer.urls', namespace='advicer')),
    # Utils
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^uwagi/', include('tasty_feedback.urls', namespace='tasty_feedback')),
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#if settings.DEBUG:
#    import debug_toolbar
#    urlpatterns += patterns('',
#        url(r'^__debug__/', include(debug_toolbar.urls)),
#    )


def handler500(request):
    """500 error handler which includes ``request`` in the context.

    Templates: `500.html`
    Context: None
    """

    t = loader.get_template('500.html')  # You need to create a 500.html template.
    return HttpResponseServerError(t.render(Context({
        'request': request,
    })))
