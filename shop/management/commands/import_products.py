import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from PIL import Image, ImageOps

from shop.models import Category, Product, ProductImage

# Maps each raw source folder (under static/images/) to the catalog entry
# to build from it. Price/stock/age-group/featured are starting placeholders
# meant to be corrected in /admin/ once real pricing and stock are known.
PRODUCT_SOURCES = {
    'Littlescribbles brain booster': {
        'name': 'Brain Booster Activity Book',
        'category': 'Ages 4-8',
        'price': 299,
        'is_featured': True,
    },
    'Littlescribbles brain gym': {
        'name': 'Brain Gym Activity Book',
        'category': 'Ages 4-8',
        'price': 299,
        'is_featured': False,
    },
    'Littlescribbles keep me busy': {
        'name': 'Keep Me Busy Activity Book',
        'category': 'Ages 4-8',
        'price': 299,
        'is_featured': False,
        'video': 'VID_20260707_214930_347_bsl.mp4',
    },
    'Littlescribbles tracing book': {
        'name': 'Tracing Book',
        'category': 'Ages 3-6',
        'price': 249,
        'is_featured': False,
    },
    'Pillow cushion book': {
        'name': 'Pillow Cushion Book',
        'category': 'Ages 2-4',
        'price': 799,
        'is_featured': True,
    },
    'Wooden tracing alphabet': {
        'name': 'Wooden Tracing Board - Alphabet',
        'category': 'Ages 3-6',
        'price': 499,
        'is_featured': True,
    },
    'Wooden tracing cursive': {
        'name': 'Wooden Tracing Board - Cursive',
        'category': 'Ages 3-6',
        'price': 499,
        'is_featured': False,
    },
    'Wooden tracing hindi': {
        'name': 'Wooden Tracing Board - Hindi',
        'category': 'Ages 3-6',
        'price': 499,
        'is_featured': False,
    },
    'Wooden tracing lines and curves': {
        'name': 'Wooden Tracing Board - Lines & Curves',
        'category': 'Ages 3-6',
        'price': 499,
        'is_featured': False,
    },
    'Wooden tracing tamil': {
        'name': 'Wooden Tracing Board - Tamil',
        'category': 'Ages 3-6',
        'price': 499,
        'is_featured': False,
    },
}

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
MAX_DIMENSION = 1200
MAX_VIDEO_WIDTH = 720
DEFAULT_STOCK = 15


class Command(BaseCommand):
    help = 'Import real product photos from static/images/<folder> into the catalog, resizing them for the web.'

    def handle(self, *args, **options):
        source_root = Path(settings.BASE_DIR) / 'static' / 'images'
        products_created = 0
        images_imported = 0

        for folder_name, info in PRODUCT_SOURCES.items():
            source_dir = source_root / folder_name
            if not source_dir.is_dir():
                self.stderr.write(self.style.WARNING(f'Skipping missing folder: {folder_name}'))
                continue

            category, _ = Category.objects.get_or_create(
                name=info['category'], defaults={'slug': slugify(info['category'])}
            )

            slug = slugify(info['name'])
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': info['name'],
                    'category': category,
                    'price': info['price'],
                    'stock': DEFAULT_STOCK,
                    'is_featured': info['is_featured'],
                    'description': (
                        f"{info['name']} from LittleScribbles - a fun, hands-on activity "
                        f"designed for curious minds ({info['category']})."
                    ),
                },
            )
            if created:
                products_created += 1
            else:
                product.category = category
                product.save()

            product.images.all().delete()
            dest_dir = Path(settings.MEDIA_ROOT) / 'products' / slug
            dest_dir.mkdir(parents=True, exist_ok=True)

            image_files = sorted(
                p for p in source_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS
            )
            for order, source_path in enumerate(image_files):
                dest_name = f'{order:02d}.jpg'
                dest_path = dest_dir / dest_name
                self._resize_and_save(source_path, dest_path)
                ProductImage.objects.create(
                    product=product,
                    image=f'products/{slug}/{dest_name}',
                    order=order,
                )
                images_imported += 1

            video_filename = info.get('video')
            if video_filename:
                if self._transcode_video(source_dir / video_filename, dest_dir / 'video.mp4'):
                    product.video = f'products/{slug}/video.mp4'
                    product.save()

        self.stdout.write(self.style.SUCCESS(
            f'Imported {products_created} new products and {images_imported} images.'
        ))

    def _resize_and_save(self, source_path: Path, dest_path: Path):
        with Image.open(source_path) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img.convert('RGBA'), mask=img.convert('RGBA').split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(dest_path, format='JPEG', quality=82, optimize=True)

    def _transcode_video(self, source_path: Path, dest_path: Path) -> bool:
        if not source_path.is_file():
            self.stderr.write(self.style.WARNING(f'Skipping missing video: {source_path}'))
            return False
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            self.stderr.write(self.style.WARNING(
                'ffmpeg not found on PATH - skipping video transcode. Install ffmpeg and re-run to include it.'
            ))
            return False
        subprocess.run(
            [
                ffmpeg, '-y', '-i', str(source_path),
                '-vf', f"scale='min({MAX_VIDEO_WIDTH},iw)':-2",
                '-c:v', 'libx264', '-profile:v', 'main', '-preset', 'medium', '-crf', '26',
                '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart',
                str(dest_path),
            ],
            check=True,
            capture_output=True,
        )
        return True
