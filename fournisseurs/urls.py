from django.urls import path

from fournisseurs.views import (
    CritereEvaluationManageView,
    DashboardView,
    DomaineCreateView,
    DomaineDeleteView,
    DomaineListView,
    DomaineUpdateView,
    DemandeAgrementFileView,
    FournisseurEvaluationCreateView,
    FournisseurClassementView,
    FournisseurCreateView,
    FournisseurDeleteView,
    FournisseurDetailView,
    FournisseurListView,
    FournisseurUpdateView,
    fournisseur_quick_status_update,
)

app_name = "fournisseurs"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("fournisseurs/", FournisseurListView.as_view(), name="fournisseurs_list"),
    path("fournisseurs/creer/", FournisseurCreateView.as_view(), name="fournisseur_create"),
    path("fournisseurs/<int:pk>/", FournisseurDetailView.as_view(), name="fournisseur_detail"),
    path(
        "fournisseurs/<int:pk>/demande-agrement/",
        DemandeAgrementFileView.as_view(),
        name="demande_agrement",
    ),
    path("fournisseurs/<int:pk>/modifier/", FournisseurUpdateView.as_view(), name="fournisseur_update"),
    path(
        "fournisseurs/<int:pk>/evaluation-annuelle/",
        FournisseurEvaluationCreateView.as_view(),
        name="fournisseur_evaluation_create",
    ),
    path(
        "fournisseurs/<int:pk>/status/",
        fournisseur_quick_status_update,
        name="fournisseur_quick_status_update",
    ),
    path("fournisseurs/<int:pk>/supprimer/", FournisseurDeleteView.as_view(), name="fournisseur_delete"),
    path("domaines/", DomaineListView.as_view(), name="domaines_list"),
    path("domaines/creer/", DomaineCreateView.as_view(), name="domaine_create"),
    path("domaines/<int:pk>/modifier/", DomaineUpdateView.as_view(), name="domaine_update"),
    path("domaines/<int:pk>/supprimer/", DomaineDeleteView.as_view(), name="domaine_delete"),
    path(
        "evaluations/criteres/",
        CritereEvaluationManageView.as_view(),
        name="criteres_evaluation_manage",
    ),
    path(
        "evaluations/classement/",
        FournisseurClassementView.as_view(),
        name="fournisseurs_classement",
    ),
]

