from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from fournisseurs.models import (
    CritereEvaluation,
    DomaineActivite,
    EvaluationAnnuelle,
    EvaluationAnnuelleLigne,
    Fournisseur,
    UserProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "must_change_password")
    list_filter = ("must_change_password",)
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user",)


@admin.register(DomaineActivite)
class DomaineActiviteAdmin(admin.ModelAdmin):
    list_display = ("nom", "created_by", "fournisseurs_count")
    search_fields = ("nom",)
    ordering = ("nom",)
    list_per_page = 25

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(nb_fournisseurs=Count("fournisseurs", distinct=True))

    @admin.display(description="Fournisseurs")
    def fournisseurs_count(self, obj: DomaineActivite) -> int:
        return getattr(obj, "nb_fournisseurs", None) or obj.fournisseurs.count()


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = (
        "raison_sociale",
        "created_by",
        "statut",
        "email",
        "date_creation",
        "domaines_display",
        "demande_agrement_link",
    )
    search_fields = ("raison_sociale", "email", "contact", "ninea", "rc")
    list_filter = ("statut", "domaines", "date_creation")
    ordering = ("-date_creation",)
    list_per_page = 25
    filter_horizontal = ("domaines",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("domaines")

    @admin.display(description="Domaines")
    def domaines_display(self, obj: Fournisseur) -> str:
        names = list(obj.domaines.values_list("nom", flat=True))
        if len(names) <= 3:
            return ", ".join(names)
        return ", ".join(names[:3]) + f" (+{len(names) - 3})"

    @admin.display(description="Demande d’agrément")
    def demande_agrement_link(self, obj: Fournisseur):
        if not obj.demande_agrement:
            return "—"
        url = reverse("fournisseurs:demande_agrement", args=[obj.pk])
        return format_html('<a href="{}" target="_blank" rel="noopener">Ouvrir</a>', url)


class EvaluationAnnuelleLigneInline(admin.TabularInline):
    model = EvaluationAnnuelleLigne
    extra = 0


@admin.register(CritereEvaluation)
class CritereEvaluationAdmin(admin.ModelAdmin):
    list_display = ("libelle", "code", "coefficient", "ordre", "actif")
    list_filter = ("actif", "coefficient")
    search_fields = ("libelle", "code")
    ordering = ("ordre", "libelle")


@admin.register(EvaluationAnnuelle)
class EvaluationAnnuelleAdmin(admin.ModelAdmin):
    list_display = ("fournisseur", "annee", "created_by", "date_creation", "note_finale_display")
    list_filter = ("annee",)
    search_fields = ("fournisseur__raison_sociale",)
    autocomplete_fields = ("fournisseur", "created_by")
    inlines = (EvaluationAnnuelleLigneInline,)

    @admin.display(description="Note finale")
    def note_finale_display(self, obj: EvaluationAnnuelle):
        return f"{obj.note_finale}/10"
