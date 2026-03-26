from django.db import models


class DomaineActivite(models.Model):
    nom = models.CharField(max_length=150, unique=True)

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

    contact = models.CharField(max_length=255)
    fonction = models.CharField(max_length=255)
    telephone = models.CharField(max_length=50, blank=True)
    adresse = models.TextField(blank=True)
    email = models.EmailField(blank=True, db_index=True)
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
