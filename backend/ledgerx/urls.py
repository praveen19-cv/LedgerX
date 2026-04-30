from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy", "service": "LedgerX API"})

urlpatterns = [
    path("", health_check),
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.merchants.urls")),
    path("api/v1/", include("apps.ledger.urls")),
    path("api/v1/", include("apps.payouts.urls")),
]
