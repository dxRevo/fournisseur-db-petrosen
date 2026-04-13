from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
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
        EN_ATTENTE = "en_attente", "En attente de validation"
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


class CritereEvaluation(models.Model):
    code = models.CharField(max_length=80, unique=True)
    libelle = models.CharField(max_length=255)
    coefficient = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    ordre = models.PositiveSmallIntegerField(default=1)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Critère d’évaluation"
        verbose_name_plural = "Critères d’évaluation"
        ordering = ["ordre", "libelle"]

    def __str__(self) -> str:
        return f"{self.libelle} (coef. {self.coefficient})"


class EvaluationAnnuelle(models.Model):
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.CASCADE, related_name="evaluations_annuelles"
    )
    annee = models.PositiveSmallIntegerField()
    created_by = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="evaluations_annuelles_creees",
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Évaluation annuelle"
        verbose_name_plural = "Évaluations annuelles"
        ordering = ["-annee", "-date_creation"]
        constraints = [
            models.UniqueConstraint(
                fields=["fournisseur", "annee"],
                name="uniq_eval_annuelle_fournisseur_annee",
            )
        ]

    def __str__(self) -> str:
        return f"{self.fournisseur} - {self.annee}"

    @property
    def note_finale(self):
        lignes = self.lignes.select_related("critere").all()
        total_coeff = sum(item.critere.coefficient for item in lignes)
        if total_coeff == 0:
            return 0
        total_pondere = sum(float(item.note) * item.critere.coefficient for item in lignes)
        return round(total_pondere / total_coeff, 2)


class EvaluationAnnuelleLigne(models.Model):
    evaluation = models.ForeignKey(
        EvaluationAnnuelle, on_delete=models.CASCADE, related_name="lignes"
    )
    critere = models.ForeignKey(
        CritereEvaluation, on_delete=models.PROTECT, related_name="lignes_evaluation"
    )
    note = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )

    class Meta:
        verbose_name = "Ligne d’évaluation annuelle"
        verbose_name_plural = "Lignes d’évaluation annuelle"
        ordering = ["critere__ordre", "critere__libelle"]
        constraints = [
            models.UniqueConstraint(
                fields=["evaluation", "critere"],
                name="uniq_eval_annuelle_ligne_par_critere",
            )
        ]

    def __str__(self) -> str:
        return f"{self.evaluation} - {self.critere.libelle}"
