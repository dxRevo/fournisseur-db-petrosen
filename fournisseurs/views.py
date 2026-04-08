from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    Case,
    Count,
    F,
    IntegerField,
    Q,
    Value,
    When,
)
from django.db import transaction
from django.db.models.functions import Cast, Round
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from fournisseurs.forms import (
    DomaineActiviteForm,
    CritereEvaluationFormSet,
    EvaluationAnnuelleForm,
    FournisseurForm,
    get_criteres_actifs,
)
from fournisseurs.models import CritereEvaluation, DomaineActivite, EvaluationAnnuelle, Fournisseur
import os

# Champs pris en compte pour le taux : raison_sociale, domaines (≥1), contact,
# fonction, téléphone, adresse, email, modalités, NINEA, RC, PDF d’agrément.
TOTAL_COMPLETION_FIELDS = 11


def _fournisseur_filled_sum_expr():
    pdf_bit = Case(
        When(Q(demande_agrement__isnull=True) | Q(demande_agrement=""), then=Value(0)),
        default=Value(1),
        output_field=IntegerField(),
    )
    return (
        Case(When(raison_sociale__gt="", then=Value(1)), default=Value(0), output_field=IntegerField())
        + Case(
            When(ndomaines__gt=0, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
        + Case(When(contact__gt="", then=Value(1)), default=Value(0), output_field=IntegerField())
        + Case(When(fonction__gt="", then=Value(1)), default=Value(0), output_field=IntegerField())
        + Case(When(telephone__gt="", then=Value(1)), default=Value(0), output_field=IntegerField())
        + Case(When(adresse__gt="", then=Value(1)), default=Value(0), output_field=IntegerField())
        + Case(When(email__gt="", then=Value(1)), default=Value(0), output_field=IntegerField())
        + Case(When(modalites_paiement__gt="", then=Value(1)), default=Value(0), output_field=IntegerField())
        + Case(When(ninea__gt="", then=Value(1)), default=Value(0), output_field=IntegerField())
        + Case(When(rc__gt="", then=Value(1)), default=Value(0), output_field=IntegerField())
        + pdf_bit
    )


def _fournisseur_completeness_percent_expr():
    return Cast(
        Round(F("filled_sum") * 100.0 / Value(float(TOTAL_COMPLETION_FIELDS)), 0),
        IntegerField(),
    )


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "fournisseurs/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = Fournisseur.objects.count()
        en_attente = Fournisseur.objects.filter(statut=Fournisseur.Statut.EN_ATTENTE).count()
        valide = Fournisseur.objects.filter(statut=Fournisseur.Statut.VALIDE).count()
        refuse = Fournisseur.objects.filter(statut=Fournisseur.Statut.REFUSE).count()

        with_document = Fournisseur.objects.exclude(
            Q(demande_agrement__isnull=True) | Q(demande_agrement="")
        ).count()

        incomplets = (
            Fournisseur.objects.annotate(ndomaines=Count("domaines", distinct=True))
            .annotate(filled_sum=_fournisseur_filled_sum_expr())
            .filter(filled_sum__lt=TOTAL_COMPLETION_FIELDS)
            .count()
        )

        validation_rate = round((valide / total) * 100, 1) if total else 0
        document_rate = round((with_document / total) * 100, 1) if total else 0
        incomplete_rate = round((incomplets / total) * 100, 1) if total else 0

        has_pdf = Case(
            When(Q(demande_agrement__isnull=True) | Q(demande_agrement=""), then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )

        to_process = (
            Fournisseur.objects.filter(statut=Fournisseur.Statut.EN_ATTENTE)
            .select_related("created_by")
            .annotate(ndomaines=Count("domaines", distinct=True))
            .annotate(filled_sum=_fournisseur_filled_sum_expr())
            .annotate(completeness=_fournisseur_completeness_percent_expr())
            .annotate(has_pdf=has_pdf)
            .order_by(
                Case(
                    When(Q(has_pdf=1) & Q(filled_sum=TOTAL_COMPLETION_FIELDS), then=Value(1)),
                    When(has_pdf=1, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                ),
                "date_creation",
            )[:20]
        )

        context["stats"] = {
            "total": total,
            "en_attente": en_attente,
            "valide": valide,
            "refuse": refuse,
            "validation_rate": validation_rate,
            "document_rate": document_rate,
            "incomplete_rate": incomplete_rate,
        }
        context["quality"] = {
            "with_document": with_document,
            "incomplete": incomplets,
        }
        context["to_process"] = to_process
        return context


class DomaineListView(LoginRequiredMixin, ListView):
    model = DomaineActivite
    template_name = "fournisseurs/domaines_list.html"
    context_object_name = "domaines"
    paginate_by = 50

    def get_queryset(self):
        # Evite les requêtes N+1 côté template (count sur ManyToMany).
        qs = DomaineActivite.objects.select_related("created_by").annotate(
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
        form.instance.created_by = self.request.user
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
            Fournisseur.objects.select_related("created_by")
            .prefetch_related("domaines")
            .order_by("-date_creation")
        )

        query = (self.request.GET.get("q") or "").strip()
        domaine_id = (self.request.GET.get("domaine") or "").strip()
        statut = (self.request.GET.get("statut") or "").strip()
        doc = (self.request.GET.get("doc") or "").strip()
        incomplet = (self.request.GET.get("incomplet") or "").strip()

        if query:
            qs = qs.filter(
                Q(raison_sociale__icontains=query) | Q(domaines__nom__icontains=query)
            )

        if domaine_id:
            qs = qs.filter(domaines__id=domaine_id)

        if statut in (
            Fournisseur.Statut.EN_ATTENTE,
            Fournisseur.Statut.VALIDE,
            Fournisseur.Statut.REFUSE,
        ):
            qs = qs.filter(statut=statut)

        if doc == "1":
            qs = qs.exclude(
                Q(demande_agrement__isnull=True) | Q(demande_agrement="")
            )

        if incomplet == "1":
            qs = (
                qs.annotate(ndomaines=Count("domaines", distinct=True))
                .annotate(filled_sum=_fournisseur_filled_sum_expr())
                .filter(filled_sum__lt=TOTAL_COMPLETION_FIELDS)
            )

        need_distinct = bool(query or domaine_id)
        return qs.distinct() if need_distinct else qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["q"] = (self.request.GET.get("q") or "").strip()
        context["domaine_id"] = (self.request.GET.get("domaine") or "").strip()
        context["statut"] = (self.request.GET.get("statut") or "").strip()
        context["doc"] = (self.request.GET.get("doc") or "").strip()
        context["incomplet"] = (self.request.GET.get("incomplet") or "").strip()

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
        return Fournisseur.objects.select_related("created_by").prefetch_related("domaines")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_eval = (
            self.object.evaluations_annuelles.prefetch_related("lignes__critere")
            .order_by("-annee", "-date_creation")
            .first()
        )
        rows = []
        if last_eval:
            for line in last_eval.lignes.all():
                rows.append(
                    {
                        "line": line,
                        "note_ponderee": round(float(line.note) * line.critere.coefficient, 2),
                    }
                )
        context["last_evaluation"] = last_eval
        context["last_evaluation_rows"] = rows
        return context


class FournisseurCreateView(LoginRequiredMixin, CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = "fournisseurs/fournisseur_form.html"

    def get_success_url(self):
        return reverse_lazy("fournisseurs:fournisseur_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
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


class FournisseurEvaluationCreateView(LoginRequiredMixin, View):
    template_name = "fournisseurs/fournisseur_evaluation_form.html"

    def get(self, request, pk, *args, **kwargs):
        fournisseur = get_object_or_404(Fournisseur, pk=pk)
        annee = self._parse_annee(request.GET.get("annee"))
        criteres = list(get_criteres_actifs())
        form = EvaluationAnnuelleForm(criteres=criteres)
        return self._render(request, fournisseur, form, annee, criteres)

    def post(self, request, pk, *args, **kwargs):
        fournisseur = get_object_or_404(Fournisseur, pk=pk)
        annee = self._parse_annee(request.POST.get("annee"))
        criteres = list(get_criteres_actifs())
        form = EvaluationAnnuelleForm(request.POST, criteres=criteres)

        if not form.is_valid():
            return self._render(request, fournisseur, form, annee, criteres)

        if EvaluationAnnuelle.objects.filter(fournisseur=fournisseur, annee=annee).exists():
            messages.error(
                request,
                f"Une évaluation existe déjà pour {annee}.",
            )
            return self._render(request, fournisseur, form, annee, criteres)

        with transaction.atomic():
            evaluation = EvaluationAnnuelle.objects.create(
                fournisseur=fournisseur,
                annee=annee,
                created_by=request.user,
            )
            form.save_lines(evaluation)

        messages.success(request, f"Évaluation {annee} enregistrée. Note finale: {evaluation.note_finale}/10.")
        return redirect("fournisseurs:fournisseur_detail", pk=fournisseur.pk)

    def _parse_annee(self, raw_value):
        from datetime import date

        current_year = date.today().year
        try:
            annee = int(raw_value)
        except (TypeError, ValueError):
            return current_year
        return annee if 2000 <= annee <= 2100 else current_year

    def _render(self, request, fournisseur, form, annee, criteres):
        total_coeff = sum(c.coefficient for c in criteres)
        return render(
            request,
            self.template_name,
            {
                "fournisseur": fournisseur,
                "form": form,
                "annee": annee,
                "criteres_count": len(criteres),
                "total_coeff": total_coeff,
            },
        )


class CritereEvaluationManageView(LoginRequiredMixin, View):
    template_name = "fournisseurs/criteres_evaluation_manage.html"

    def get(self, request, *args, **kwargs):
        queryset = CritereEvaluation.objects.all().order_by("ordre", "libelle")
        formset = CritereEvaluationFormSet(queryset=queryset)
        return render(request, self.template_name, {"formset": formset})

    def post(self, request, *args, **kwargs):
        queryset = CritereEvaluation.objects.all().order_by("ordre", "libelle")
        formset = CritereEvaluationFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Critères mis à jour.")
            return redirect("fournisseurs:criteres_evaluation_manage")
        return render(request, self.template_name, {"formset": formset})


class FournisseurClassementView(LoginRequiredMixin, TemplateView):
    template_name = "fournisseurs/fournisseurs_classement.html"

    def get_context_data(self, **kwargs):
        from datetime import date

        context = super().get_context_data(**kwargs)
        selected_year = self.request.GET.get("annee")
        selected_domaine = (self.request.GET.get("domaine") or "").strip()
        current_year = date.today().year
        try:
            annee = int(selected_year) if selected_year else current_year
        except ValueError:
            annee = current_year

        fournisseurs_qs = Fournisseur.objects.all()
        if selected_domaine:
            fournisseurs_qs = fournisseurs_qs.filter(domaines__id=selected_domaine)
        fournisseurs = list(fournisseurs_qs.distinct())
        evaluations = (
            EvaluationAnnuelle.objects.filter(annee=annee, fournisseur__in=fournisseurs)
            .select_related("fournisseur")
            .prefetch_related("lignes__critere")
        )
        evaluations_by_fournisseur_id = {
            evaluation.fournisseur_id: evaluation for evaluation in evaluations
        }

        for fournisseur in fournisseurs:
            evaluation = evaluations_by_fournisseur_id.get(fournisseur.pk)
            if evaluation:
                fournisseur.has_evaluation = 1
                fournisseur.note_finale = evaluation.note_finale
            else:
                fournisseur.has_evaluation = 0
                fournisseur.note_finale = 0.0

        fournisseurs.sort(
            key=lambda f: (
                -f.has_evaluation,
                -float(f.note_finale),
                f.raison_sociale.lower(),
            )
        )

        classement = []
        rank = 0
        for fournisseur in fournisseurs:
            if fournisseur.has_evaluation:
                rank += 1
            classement.append(
                {"rang": rank if fournisseur.has_evaluation else "—", "item": fournisseur}
            )

        context["annee"] = annee
        context["domaine_id"] = selected_domaine
        context["domaines"] = DomaineActivite.objects.all().order_by("nom")
        context["classement"] = classement
        context["has_data"] = any(row["item"].has_evaluation for row in classement)
        return context


@require_POST
def fournisseur_quick_status_update(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    status = request.POST.get("status")
    allowed = {Fournisseur.Statut.VALIDE, Fournisseur.Statut.REFUSE}
    if status not in allowed:
        messages.error(request, "Statut invalide.")
        return redirect("fournisseurs:dashboard")

    fournisseur.statut = status
    fournisseur.save(update_fields=["statut"])
    messages.success(request, f"Statut mis a jour: {fournisseur.get_statut_display()}.")
    return redirect("fournisseurs:dashboard")
