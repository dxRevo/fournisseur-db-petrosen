from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("fournisseurs", "0005_fournisseur_optional_contact_fonction_email_text"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CritereEvaluation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=80, unique=True)),
                ("libelle", models.CharField(max_length=255)),
                (
                    "coefficient",
                    models.PositiveSmallIntegerField(
                        validators=[MinValueValidator(1), MaxValueValidator(5)]
                    ),
                ),
                ("ordre", models.PositiveSmallIntegerField(default=1)),
                ("actif", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Critère d’évaluation",
                "verbose_name_plural": "Critères d’évaluation",
                "ordering": ["ordre", "libelle"],
            },
        ),
        migrations.CreateModel(
            name="EvaluationAnnuelle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("annee", models.PositiveSmallIntegerField()),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("date_modification", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="evaluations_annuelles_creees",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "fournisseur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluations_annuelles",
                        to="fournisseurs.fournisseur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Évaluation annuelle",
                "verbose_name_plural": "Évaluations annuelles",
                "ordering": ["-annee", "-date_creation"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("fournisseur", "annee"),
                        name="uniq_eval_annuelle_fournisseur_annee",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="EvaluationAnnuelleLigne",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "note",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=4,
                        validators=[MinValueValidator(0), MaxValueValidator(10)],
                    ),
                ),
                (
                    "critere",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lignes_evaluation",
                        to="fournisseurs.critereevaluation",
                    ),
                ),
                (
                    "evaluation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lignes",
                        to="fournisseurs.evaluationannuelle",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ligne d’évaluation annuelle",
                "verbose_name_plural": "Lignes d’évaluation annuelle",
                "ordering": ["critere__ordre", "critere__libelle"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("evaluation", "critere"),
                        name="uniq_eval_annuelle_ligne_par_critere",
                    )
                ],
            },
        ),
    ]
