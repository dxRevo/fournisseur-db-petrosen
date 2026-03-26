from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from fournisseurs.forms import DomaineActiviteForm, FournisseurForm
from fournisseurs.models import DomaineActivite, Fournisseur
import os


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "fournisseurs/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = {
            "total": Fournisseur.objects.count(),
            "en_attente": Fournisseur.objects.filter(statut=Fournisseur.Statut.EN_ATTENTE).count(),
            "valide": Fournisseur.objects.filter(statut=Fournisseur.Statut.VALIDE).count(),
            "refuse": Fournisseur.objects.filter(statut=Fournisseur.Statut.REFUSE).count(),
        }
        return context


class DomaineListView(LoginRequiredMixin, ListView):
    model = DomaineActivite
    template_name = "fournisseurs/domaines_list.html"
    context_object_name = "domaines"
    paginate_by = 50

    def get_queryset(self):
        # Evite les requêtes N+1 côté template (count sur ManyToMany).
        qs = DomaineActivite.objects.annotate(
            nb_fournisseurs=Count("fournisseurs", distinct=True)
        ).order_by("nom")
        query = (self.request.GET.get("q") or "").strip()
        if query:
            qs = qs.filter(nom__icontains=query)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = (self.request.GET.get("q") or "").strip()
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()
        return context


class DomaineCreateView(LoginRequiredMixin, CreateView):
    model = DomaineActivite
    form_class = DomaineActiviteForm
    template_name = "fournisseurs/domaine_form.html"

    def get_success_url(self):
        return reverse_lazy("fournisseurs:domaines_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Domaine créé avec succès.")
        return response


class DomaineUpdateView(LoginRequiredMixin, UpdateView):
    model = DomaineActivite
    form_class = DomaineActiviteForm
    template_name = "fournisseurs/domaine_form.html"

    def get_success_url(self):
        return reverse_lazy("fournisseurs:domaines_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Domaine mis à jour avec succès.")
        return response


class DomaineDeleteView(LoginRequiredMixin, DeleteView):
    model = DomaineActivite
    template_name = "fournisseurs/domaine_confirm_delete.html"
    context_object_name = "domaine"
    success_url = reverse_lazy("fournisseurs:domaines_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Domaine supprimé.")
        return super().delete(request, *args, **kwargs)


class FournisseurListView(LoginRequiredMixin, ListView):
    model = Fournisseur
    template_name = "fournisseurs/fournisseurs_list.html"
    context_object_name = "fournisseurs"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Fournisseur.objects.all()
            .prefetch_related("domaines")
            .order_by("-date_creation")
        )

        query = (self.request.GET.get("q") or "").strip()
        domaine_id = (self.request.GET.get("domaine") or "").strip()

        if query:
            qs = qs.filter(
                Q(raison_sociale__icontains=query) | Q(domaines__nom__icontains=query)
            )

        if domaine_id:
            qs = qs.filter(domaines__id=domaine_id)

        # Filtrage via ManyToMany => risque de doublons.
        return qs.distinct() if (query or domaine_id) else qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["q"] = (self.request.GET.get("q") or "").strip()
        context["domaine_id"] = (self.request.GET.get("domaine") or "").strip()

        # Données pour le dropdown "Domaine"
        context["domaines"] = DomaineActivite.objects.all().order_by("nom")

        # On prépare un string de query params sans le paramètre page,
        # pour conserver les filtres lors de la pagination.
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()
        return context


class FournisseurDetailView(LoginRequiredMixin, DetailView):
    model = Fournisseur
    template_name = "fournisseurs/fournisseur_detail.html"
    context_object_name = "fournisseur"

    def get_queryset(self):
        return Fournisseur.objects.all().prefetch_related("domaines")


class FournisseurCreateView(LoginRequiredMixin, CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = "fournisseurs/fournisseur_form.html"

    def get_success_url(self):
        return reverse_lazy("fournisseurs:fournisseur_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Fournisseur créé avec succès.")
        return response


class FournisseurUpdateView(LoginRequiredMixin, UpdateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = "fournisseurs/fournisseur_form.html"

    def get_success_url(self):
        return reverse_lazy("fournisseurs:fournisseur_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Fournisseur mis à jour avec succès.")
        return response


class FournisseurDeleteView(LoginRequiredMixin, DeleteView):
    model = Fournisseur
    template_name = "fournisseurs/fournisseur_confirm_delete.html"
    context_object_name = "fournisseur"
    success_url = reverse_lazy("fournisseurs:fournisseurs_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Fournisseur supprimé.")
        return super().delete(request, *args, **kwargs)


class DemandeAgrementFileView(LoginRequiredMixin, View):
    """
    Lecture sécurisée du fichier PDF de demande d’agrément.

    Cette approche reste compatible avec S3 : on utilise le stockage via `FileField.open()`,
    plutôt que de servir directement `demande_agrement.url`.
    """

    def get(self, request, pk, *args, **kwargs):
        fournisseur = get_object_or_404(Fournisseur, pk=pk)
        if not fournisseur.demande_agrement:
            raise Http404("Aucun document disponible pour ce fournisseur.")

        file_handle = fournisseur.demande_agrement.open("rb")
        filename = os.path.basename(fournisseur.demande_agrement.name) or "demande_agrement.pdf"

        response = FileResponse(file_handle, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response
