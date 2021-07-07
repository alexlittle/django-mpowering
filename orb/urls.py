from __future__ import unicode_literals

from django.conf.urls import include, url
from django.views.generic import TemplateView

from orb import views
from orb.feeds import LatestEntries, LatestTagEntries

urlpatterns = [
    url(r'^$', views.home_view, name="orb_home"),
    url(r'^robots.txt$', TemplateView.as_view(template_name="orb/robots.txt")),
    url(r'^about/$', TemplateView.as_view(template_name="orb/about.html"), name="orb_about"),
    url(r'^content-review-process/$',
        TemplateView.as_view(template_name="orb/content_review.html"),
        name="orb_content_review_process"),
    url(r'^feed/$', LatestEntries(), name="orb_feed"),
    url(r'^how-to/$', TemplateView.as_view(template_name="orb/how_to.html"), name="orb_how_to"),
    url(r'^cc-faq/$', TemplateView.as_view(template_name="orb/cc-faq.html"), name="orb_cc_faq"),
    url(r'^partners/$', views.partner_view, name="orb_partners"),
    url(r'^upload-instructions/$', views.upload_instructions_view, name="orb_upload_instructions"),
    url(r'^terms/$', TemplateView.as_view(template_name="orb/terms.html"), name="orb_terms"),

    url(r'^profile/', include('orb.profiles.urls')),

    url(r'^tag/view/(?P<tag_slug>\w[\w/-]*)$', views.tag_view, name="orb_tags"),
    url(r'^tag/feed/(?P<tag_slug>\w[\w/-]*)$', LatestTagEntries(), name="orb_tag_feed"),

    url(r'^tag/', include('orb.tags.urls')),

    url(r'^collection/view/(?P<collection_slug>\w[\w/-]*)$', views.collection_view, name="orb_collection"),

    url(r'^analytics/', include('orb.analytics.urls')),

    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^search/$', views.search_view, name="orb_search"),
    url(r'^search/advanced/$', views.search_advanced_view, name="orb_search_advanced"),
    url(r'^search/advanced/(?P<tag_id>\d+)/$', views.search_advanced_view, name="orb_search_advanced_prefill"),
    url(r'^search/advanced/results/$', views.search_advanced_results_view, name="orb_search_advanced_results"),
    url(r'^opensearch/$', TemplateView.as_view(template_name="search/opensearch.html"), name="orb_opensearch"),

    url(r'^api/', include('orb.api.urls')),

    # url(r'^courses/', include('orb.courses.urls')),

    url(r'^resource/rate/', include('orb.rating.urls')),
    url(r'^resource/bookmark/', include('orb.bookmark.urls')),
    url(r'^resource/', include('orb.resources.urls')),
    url(r'^review/', include('orb.review.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
]
