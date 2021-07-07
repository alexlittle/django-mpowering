"""

"""

from __future__ import unicode_literals

import logging

from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin

from orb import conf
from orb.models import ResourceFile, ResourceURL
from orb.resources.forms import ResourceAccessForm
from orb.signals import resource_file_viewed, resource_url_viewed

logger = logging.getLogger(__name__)


class ResourceComponentView(FormMixin, DetailView):
    model = None
    signal = None
    signal_arg_name = None
    pk_url_kwarg = 'id'
    form_class = ResourceAccessForm
    template_name = 'orb/resource/resource_gateway.html'

    def send_signal(self, **kwargs):
        base_kwargs = {
            'request': self.request,
            self.signal_arg_name: self.object,
        }
        base_kwargs.update(kwargs)
        self.signal.send(sender=self.object, **base_kwargs)

    def get_queryset(self):
        return self.model.objects.approved(self.request.user)

    def form_valid(self, form):
        form_data = form.cleaned_data
        self.request.session['resource_init_data'] = form_data  # set initial data for next resource
        self.send_signal(**form_data)
        return redirect(self.get_success_url())

    def get_initial(self):
        return self.request.session.get('resource_init_data', {})

    def get_form_kwargs(self):
        """Presumes GET requests"""
        kwargs = super(ResourceComponentView, self).get_form_kwargs()
        kwargs.update({
            'data': self.request.GET,
        })
        return kwargs

    def get(self, request, *args, **kwargs):
        """Responds to all requests

        Must check whether form should be bound first by checking for a value that
        is expected to be submitted with the form, i.e. 'submit'.
        """

        self.object = self.get_object()
        form = self.get_form()

        if not conf.DOWNLOAD_EXTRA_INFO:
            form.is_valid()
            return self.form_valid(form)
        elif 'submit' not in self.request.GET:
            return self.render_to_response(self.get_context_data(
                form=self.form_class(initial=self.get_initial()),
                object=self.get_object(),
            ))
        elif form.is_valid():
            return self.form_valid(form)
        return self.render_to_response(self.get_context_data(
            form=form,
            object=self.get_object(),
        ))


class ResourceFileView(ResourceComponentView):
    model = ResourceFile
    signal = resource_file_viewed
    signal_arg_name = 'resource_file'

    def get_object(self, queryset=None):
        self.object = super(ResourceFileView, self).get_object(queryset)
        if not self.object.filesize():
            logger.warning("File for '{}' does not exist or has 0 filesize".format(self.object))
            raise Http404
        return self.object

    def get_success_url(self):
        return self.object.web_path


class ResourceURLView(ResourceComponentView):
    model = ResourceURL
    signal = resource_url_viewed
    signal_arg_name = 'resource_url'

    def get_success_url(self):
        return self.object.url
