from django.urls import path
from .views import LedgerListView

urlpatterns = [
    path(
        "merchants/<uuid:merchant_id>/ledger/",
        LedgerListView.as_view(),
        name="ledger-list",
    ),
]
