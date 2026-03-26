from django.core.management.base import BaseCommand

from fournisseurs.models import DomaineActivite


DOMAINS = [
    "Graphisme et objets de promotion",
    "Géolocalisation",
    "Contrôle d’accès",
    "Mobilier de bureau",
    "Communication",
    "Climatisation",
    "Menuiserie aluminium",
    "Film adhésif et store",
    "Fourniture de bureau",
    "Agence de Voyage",
    "Hôtellerie et Restauration",
    "Plomberie Sanitaire et carrelage",
    "Société de nettoiement",
    "QHSE",
    "Électroménager",
    "Location équipement audiovisuel",
    "Société de déménagement",
    "Garage auto et vente de pièces détachées",
    "Fourniture eau potable",
    "Courrier express",
    "Bâtiments et travaux publics",
    "Location de véhicules",
    "Consommables informatique",
    "Réparation matériel informatique",
    "Société logistique et transit",
    "Cabinets d’avocat et audit",
    "Désinfection et dératisation",
    "Structure médicale d’urgence",
]


class Command(BaseCommand):
    help = "Précharge les domaines d'activité de fournisseurs"

    def handle(self, *args, **options):
        created = 0
        existing = 0

        for nom in DOMAINS:
            _, was_created = DomaineActivite.objects.get_or_create(nom=nom)
            if was_created:
                created += 1
            else:
                existing += 1

        self.stdout.write(self.style.SUCCESS(f"Domaines: {created} créés, {existing} déjà existants."))

