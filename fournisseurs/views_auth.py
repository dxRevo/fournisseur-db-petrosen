from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from fournisseurs.models import UserProfile


class AppPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        UserProfile.objects.filter(user=self.request.user).update(
            must_change_password=False
        )
        messages.success(self.request, "Votre mot de passe a été mis à jour.")
        return response
