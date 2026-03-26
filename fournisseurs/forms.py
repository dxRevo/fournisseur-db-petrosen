from __future__ import annotations

import os

from django import forms

from fournisseurs.models import DomaineActivite, Fournisseur


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
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "modalites_paiement": forms.TextInput(attrs={"class": "form-control"}),
            "ninea": forms.TextInput(attrs={"class": "form-control"}),
            "rc": forms.TextInput(attrs={"class": "form-control"}),
            "demande_agrement": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "statut": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Plus lisible : titres/labels côté template.
        self.fields["demande_agrement"].required = False

    def clean_raison_sociale(self):
        valeur = self.cleaned_data.get("raison_sociale", "")
        return valeur.strip()

    def clean_email(self):
        email = self.cleaned_data.get("email") or ""
        email = email.strip()
        return email.lower() if email else email

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

