from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    must_change_password = models.BooleanField(
        default=False,
        verbose_name="doit changer le mot de passe",
    )

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateur"

    def __str__(self) -> str:
        return f"Profil de {self.user}"


class DomaineActivite(models.Model):
    nom = models.CharField(max_length=150, unique=True)
    created_by = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="domaines_crees",
    )

    class Meta:
        verbose_name = "Domaine d’activité"
        verbose_name_plural = "Domaines d’activités"
        ordering = ["nom"]

    def __str__(self) -> str:
        return self.nom


class Fournisseur(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        VALIDE = "valide", "Validé"
        REFUSE = "refuse", "Refusé"

    raison_sociale = models.CharField(max_length=255, db_index=True)
    domaines = models.ManyToManyField(DomaineActivite, related_name="fournisseurs", blank=True)
    created_by = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fournisseurs_crees",
    )

    contact = models.CharField(max_length=255, blank=True)
    fonction = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    adresse = models.TextField(blank=True)
    email = models.CharField(max_length=254, blank=True, db_index=True)
    modalites_paiement = models.CharField(max_length=255, blank=True)
    ninea = models.CharField(max_length=100, blank=True)
    rc = models.CharField(max_length=100, blank=True)

    demande_agrement = models.FileField(upload_to="agrements/", blank=True, null=True)

    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE, db_index=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["raison_sociale"]),
            models.Index(fields=["statut"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return self.raison_sociale
