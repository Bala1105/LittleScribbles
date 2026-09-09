from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.ShopLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
