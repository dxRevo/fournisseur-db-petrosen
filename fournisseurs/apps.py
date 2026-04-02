from django.apps import AppConfig


class FournisseursConfig(AppConfig):
    name = "fournisseurs"

    def ready(self):
        import fournisseurs.signals  # noqa: F401
