from django.shortcuts import redirect

from fournisseurs.models import UserProfile


class ForcePasswordChangeMiddleware:
    """Redirige vers le changement de mot de passe si le profil l'exige."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        path = request.path
        if path.startswith("/login") or path.startswith("/logout"):
            return self.get_response(request)
        if path.startswith("/compte/mot-de-passe"):
            return self.get_response(request)
        if path.startswith("/static/") or path.startswith("/media/"):
            return self.get_response(request)

        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={"must_change_password": True},
        )

        if profile.must_change_password:
            return redirect("password_change")

        return self.get_response(request)
