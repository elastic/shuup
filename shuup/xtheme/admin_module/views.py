# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from shuup.admin.utils.views import CreateOrUpdateView
from shuup.admin.views.wizard import TemplatedWizardFormDef, WizardPane
from shuup.apps.provides import get_provide_objects
from shuup.xtheme._theme import (
    get_current_theme, get_theme_by_identifier, set_current_theme
)
from shuup.xtheme.models import ThemeSettings


def get_theme_context():
    return {
        "theme_classes": sorted(
            [t for t in get_provide_objects("xtheme") if t.identifier],
            key=lambda t: (t.name or t.identifier)
        ),
        "current_theme": get_current_theme()
    }


class ActivationForm(forms.Form):
    """
    A very simple form for activating a theme.
    """
    activate = forms.CharField(label=_("activate"))


class ThemeWizardPane(WizardPane):
    identifier = "theme"
    icon = "xtheme/theme.png"
    text = _("Choose a theme for your shop")

    def visible(self):
        return not get_current_theme()

    def get_form_defs(self):
        context = get_theme_context()
        if not context["current_theme"] and len(context["theme_classes"]) > 0:
            context["current_theme"] = context["theme_classes"][0]

        return [
            TemplatedWizardFormDef(
                template_name="shuup/xtheme/admin/wizard.jinja",
                name="theme",
                form_class=ActivationForm,
                context=context
            )
        ]

    def form_valid(self, form):
        identifier = form["theme"].cleaned_data["activate"]
        set_current_theme(identifier)


class ThemeConfigView(FormView):
    """
    A view for listing and activating themes.
    """
    template_name = "shuup/xtheme/admin/config.jinja"
    form_class = ActivationForm

    def get_context_data(self, **kwargs):
        context = super(ThemeConfigView, self).get_context_data(**kwargs)
        context.update(get_theme_context())
        return context

    def form_valid(self, form):
        identifier = form.cleaned_data["activate"]
        set_current_theme(identifier)
        messages.success(self.request, _("Theme activated."))
        return HttpResponseRedirect(self.request.path)


class ThemeConfigDetailView(CreateOrUpdateView):
    """
    A view for configuring a single theme.
    """
    model = ThemeSettings
    template_name = "shuup/xtheme/admin/config_detail.jinja"
    form_class = forms.Form
    context_object_name = "theme_settings"
    add_form_errors_as_messages = True

    def get_object(self, queryset=None):
        ts, _ = ThemeSettings.objects.get_or_create(theme_identifier=self.kwargs["theme_identifier"])
        return ts

    def get_theme(self):
        """
        Get the theme object to configure.

        :return: Theme object
        :rtype: shuup.xtheme.Theme
        """
        return get_theme_by_identifier(
            identifier=self.kwargs["theme_identifier"],
            settings_obj=self.object
        )

    def get_context_data(self, **kwargs):
        context = super(ThemeConfigDetailView, self).get_context_data(**kwargs)
        context["theme"] = self.get_theme()
        return context

    def get_form(self, form_class=None):
        return self.get_theme().get_configuration_form(form_kwargs=self.get_form_kwargs())

    def get_success_url(self):
        return reverse("shuup_admin:xtheme.config_detail", kwargs={
            "theme_identifier": self.object.theme_identifier
        })
