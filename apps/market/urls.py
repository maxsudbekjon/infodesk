from django.urls import path

from apps.market.views import (
    MarketOrderCreateAPIView,
    MarketOrderMeAPIView,
    MarketProductListAPIView,
)

urlpatterns = [
    path("products/", MarketProductListAPIView.as_view(), name="market-product-list"),
    path("orders/", MarketOrderCreateAPIView.as_view(), name="market-order-create"),
    path("orders/me/", MarketOrderMeAPIView.as_view(), name="market-order-me"),
]
