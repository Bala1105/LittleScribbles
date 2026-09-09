from django.core.management.base import BaseCommand
from django.utils.text import slugify

from shop.models import Category, Product

CATEGORIES = ['Bodysuits', 'Dresses', 'Sleepwear', 'Sets & Outfits']

PRODUCTS = [
    ('Sunshine Cotton Bodysuit', 'Bodysuits', 499, True),
    ('Cloud Soft Romper', 'Bodysuits', 549, False),
    ('Rainbow Frock Dress', 'Dresses', 899, True),
    ('Floral Party Dress', 'Dresses', 999, False),
    ('Starry Night Pajama Set', 'Sleepwear', 649, True),
    ('Cozy Bear Sleepsuit', 'Sleepwear', 599, False),
    ('Little Explorer Outfit Set', 'Sets & Outfits', 1199, True),
    ('Weekend Play Set', 'Sets & Outfits', 999, False),
]


class Command(BaseCommand):
    help = 'Seed the shop with sample categories and products.'

    def handle(self, *args, **options):
        category_objs = {}
        for name in CATEGORIES:
            category, _ = Category.objects.get_or_create(name=name, slug=slugify(name))
            category_objs[name] = category

        created = 0
        for name, category_name, price, is_featured in PRODUCTS:
            _, was_created = Product.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    'name': name,
                    'category': category_objs[category_name],
                    'price': price,
                    'stock': 25,
                    'is_featured': is_featured,
                    'description': f'A comfortable and adorable {name.lower()} for your little one.',
                },
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(category_objs)} categories and {created} new products.'
        ))
