from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .cart import Cart
from .forms import AddToCartForm, ShopAuthenticationForm, SignUpForm
from .models import Category, Product


def home(request):
    featured_products = Product.objects.filter(is_featured=True)[:8]
    categories = Category.objects.all()
    return render(request, 'shop/home.html', {
        'featured_products': featured_products,
        'categories': categories,
    })


def product_list(request):
    products = Product.objects.select_related('category').all()
    categories = Category.objects.all()

    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'shop/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'query': query or '',
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            cart = Cart(request)
            cart.add(product, quantity=form.cleaned_data['quantity'])
            messages.success(request, f'Added {product.name} to your cart.')
            return redirect('shop:cart_detail')
    else:
        form = AddToCartForm()
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'form': form,
    })


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart_detail.html', {'cart': cart})


def cart_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart.set_quantity(product, quantity)
    return redirect('shop:cart_detail')


def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    messages.info(request, f'Removed {product.name} from your cart.')
    return redirect('shop:cart_detail')


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('shop:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        auth_login(self.request, self.object)
        messages.success(self.request, 'Welcome to LittleScribbles!')
        return response


class ShopLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = ShopAuthenticationForm
