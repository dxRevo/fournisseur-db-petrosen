from __future__ import annotations

import os
from decimal import Decimal

from django import forms
from django.forms import modelformset_factory

from fournisseurs.models import (
    CritereEvaluation,
    DomaineActivite,
    EvaluationAnnuelleLigne,
    Fournisseur,
)


class DomaineActiviteForm(forms.ModelForm):
    class Meta:
        model = DomaineActivite
        fields = ["nom"]
        widgets = {
            "nom": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nom du domaine",
                }
            ),
        }


class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = [
            "raison_sociale",
            "domaines",
            "contact",
            "fonction",
            "telephone",
            "adresse",
            "email",
            "modalites_paiement",
            "ninea",
            "rc",
            "demande_agrement",
            "statut",
        ]
        widgets = {
            "raison_sociale": forms.TextInput(attrs={"class": "form-control"}),
            "domaines": forms.CheckboxSelectMultiple(),
            "contact": forms.TextInput(attrs={"class": "form-control"}),
            "fonction": forms.TextInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "adresse": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "email": forms.TextInput(attrs={"class": "form-control"}),
            "modalites_paiement": forms.TextInput(attrs={"class": "form-control"}),
            "ninea": forms.TextInput(attrs={"class": "form-control"}),
            "rc": forms.TextInput(attrs={"class": "form-control"}),
            "demande_agrement": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "statut": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact"].required = False
        self.fields["fonction"].required = False
        # Plus lisible : titres/labels côté template.
        self.fields["demande_agrement"].required = False

    def clean_raison_sociale(self):
        valeur = self.cleaned_data.get("raison_sociale", "")
        return valeur.strip()

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip()

    def clean_demande_agrement(self):
        f = self.cleaned_data.get("demande_agrement")
        if not f:
            return f

        filename = f.name or ""
        ext = os.path.splitext(filename)[1].lower()
        if ext != ".pdf":
            raise forms.ValidationError("Le fichier de demande d’agrément doit être un PDF.")

        content_type = getattr(f, "content_type", "") or ""
        if content_type and content_type != "application/pdf":
            # On garde la vérif légère : extension OK => souvent suffisant.
            raise forms.ValidationError("Le fichier doit être un PDF (application/pdf).")

        return f


class EvaluationAnnuelleForm(forms.Form):
    def __init__(self, *args, criteres=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.criteres = list(criteres or [])
        for critere in self.criteres:
            field_name = f"critere_{critere.pk}"
            self.fields[field_name] = forms.DecimalField(
                label=critere.libelle,
                min_value=Decimal("0"),
                max_value=Decimal("10"),
                decimal_places=2,
                max_digits=4,
                widget=forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "step": "0.01",
                        "min": "0",
                        "max": "10",
                    }
                ),
            )

    def iter_fields(self):
        for critere in self.criteres:
            yield {
                "critere": critere,
                "field": self[f"critere_{critere.pk}"],
            }

    def save_lines(self, evaluation):
        lines = []
        for critere in self.criteres:
            note = self.cleaned_data[f"critere_{critere.pk}"]
            lines.append(
                EvaluationAnnuelleLigne(
                    evaluation=evaluation,
                    critere=critere,
                    note=note,
                )
            )
        EvaluationAnnuelleLigne.objects.bulk_create(lines)


def get_criteres_actifs():
    return CritereEvaluation.objects.filter(actif=True).order_by("ordre", "libelle")


class CritereEvaluationForm(forms.ModelForm):
    class Meta:
        model = CritereEvaluation
        fields = ["libelle", "coefficient", "ordre", "actif"]
        widgets = {
            "libelle": forms.TextInput(attrs={"class": "form-control"}),
            "coefficient": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 5}
            ),
            "ordre": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


CritereEvaluationFormSet = modelformset_factory(
    CritereEvaluation,
    form=CritereEvaluationForm,
    extra=0,
    can_delete=False,
)

