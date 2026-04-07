from django.core.management.base import BaseCommand

from fournisseurs.models import CritereEvaluation


CRITERES = [
    (
        "respect_delais",
        "Respect des engagements et des delais de livraison",
        5,
        1,
    ),
    (
        "qualite_services",
        "Qualite des services (Composants/Produits/Matieres)",
        5,
        2,
    ),
    ("competitivite_prix", "Competitivite des prix", 4, 3),
    ("competitivite_conditions", "Competitivite des conditions", 3, 4),
    ("solvabilite", "Solvabilite", 4, 5),
    ("situation_financiere", "Situation financiere generale", 4, 6),
    ("expertise_technique", "Expertise du personnel technique", 3, 7),
    ("reactivite", "Reactivite", 4, 8),
]


class Command(BaseCommand):
    help = "Precharge les criteres d'evaluation annuelle fournisseurs"

    def handle(self, *args, **options):
        created = 0
        existing = 0
        for code, libelle, coefficient, ordre in CRITERES:
            _, was_created = CritereEvaluation.objects.get_or_create(
                code=code,
                defaults={
                    "libelle": libelle,
                    "coefficient": coefficient,
                    "ordre": ordre,
                    "actif": True,
                },
            )
            if was_created:
                created += 1
            else:
                existing += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Criteres evaluation: {created} crees, {existing} deja existants."
            )
        )
