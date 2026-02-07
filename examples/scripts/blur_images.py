#!/usr/bin/env python3
"""
Script para anonimizar imágenes de reportes mediante Gaussian Blur.

Uso:
    python blur_images.py <input_dir> <output_dir> [--radius 15]
    
Ejemplo:
    python blur_images.py ../../data/reports/imgs ../reports/imgs --radius 15
"""

import argparse
from pathlib import Path
from PIL import Image, ImageFilter
import sys


def blur_image(input_path: Path, output_path: Path, radius: int = 15) -> None:
    """
    Aplica Gaussian Blur a una imagen para anonimización.
    
    Args:
        input_path: Ruta de la imagen original
        output_path: Ruta donde guardar la imagen blurred
        radius: Radio del blur (mayor = más blur). Default: 15
    """
    try:
        # Abrir imagen
        img = Image.open(input_path)
        
        # Aplicar Gaussian Blur
        blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
        
        # Guardar con calidad optimizada
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determinar formato de salida
        if input_path.suffix.lower() in ['.jpg', '.jpeg']:
            blurred.save(output_path, 'JPEG', quality=85, optimize=True)
        elif input_path.suffix.lower() == '.png':
            blurred.save(output_path, 'PNG', optimize=True)
        else:
            blurred.save(output_path)
        
        print(f"✓ Blurred: {input_path.name} → {output_path.name}")
        
    except Exception as e:
        print(f"✗ Error processing {input_path.name}: {e}", file=sys.stderr)


def blur_directory(input_dir: Path, output_dir: Path, radius: int = 15, 
                   pattern: str = "*.jpg") -> None:
    """
    Procesa todas las imágenes en un directorio.
    
    Args:
        input_dir: Directorio con imágenes originales
        output_dir: Directorio donde guardar imágenes blurred
        radius: Radio del blur
        pattern: Patrón de archivos a procesar (default: "*.jpg")
    """
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Encontrar todas las imágenes
    images = list(input_dir.glob(pattern))
    
    if not images:
        print(f"Warning: No images found matching pattern '{pattern}' in {input_dir}")
        return
    
    print(f"Found {len(images)} images to process")
    print(f"Blur radius: {radius}px")
    print(f"Output directory: {output_dir}\n")
    
    # Procesar cada imagen
    for img_path in images:
        output_path = output_dir / img_path.name
        blur_image(img_path, output_path, radius)
    
    print(f"\n✓ Processed {len(images)} images")


def main():
    parser = argparse.ArgumentParser(
        description="Anonimizar imágenes mediante Gaussian Blur",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Blurear todas las imágenes JPG con radio por defecto (15px)
  python blur_images.py ../../data/reports/imgs ../reports/imgs
  
  # Blurear con radio personalizado
  python blur_images.py input/ output/ --radius 20
  
  # Procesar solo archivos PNG
  python blur_images.py input/ output/ --pattern "*.png"
  
  # Blurear imagen individual
  python blur_images.py single.jpg output/single_blurred.jpg --radius 10
        """
    )
    
    parser.add_argument(
        'input',
        type=Path,
        help='Ruta al directorio o archivo de entrada'
    )
    
    parser.add_argument(
        'output',
        type=Path,
        help='Ruta al directorio o archivo de salida'
    )
    
    parser.add_argument(
        '--radius',
        type=int,
        default=15,
        help='Radio del Gaussian Blur (default: 15). Mayor = más blur'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.jpg',
        help='Patrón de archivos a procesar (default: *.jpg)'
    )
    
    args = parser.parse_args()
    
    # Determinar si es archivo o directorio
    if args.input.is_file():
        # Procesar archivo individual
        blur_image(args.input, args.output, args.radius)
    elif args.input.is_dir():
        # Procesar directorio
        blur_directory(args.input, args.output, args.radius, args.pattern)
    else:
        print(f"Error: Input path does not exist: {args.input}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
