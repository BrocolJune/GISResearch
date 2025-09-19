# v4_mask_simple.py
"""
Hillshade Masking (간소화 버전, 셀 중심 좌표 생성 없이 polygon mask)
폴리곤 내부 NoData, 외부는 기존값 유지로 마스킹
"""
import os
import rasterio
import geopandas as gpd
from rasterio.mask import mask
from tqdm import tqdm

raster_dir = r"D:\Junkyo\2025\Jeju_Sectorcoupling\Hillshade"
mask_shp = r"C:\Users\user\Desktop\Junkyo\2025\Jeju_Sectorcoupling\GIS\Jeju_Mask.shp"
output_dir = r"D:\Junkyo\2025\Jeju_Sectorcoupling\mask_nonsolargen"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

mask_gdf = gpd.read_file(mask_shp).to_crs(epsg=4326)
mask_geom = [g for g in mask_gdf.geometry]

raster_files = [f for f in os.listdir(raster_dir) if f.lower().endswith('.tif')]

for fname in tqdm(raster_files, desc="Hillshade Masking (Simple)"):
    raster_path = os.path.join(raster_dir, fname)
    with rasterio.open(raster_path) as src:
        out_image, out_transform = mask(src, mask_geom, invert=True, crop=False)
        out_meta = src.meta.copy()
        out_meta.update({"transform": out_transform, "height": out_image.shape[1], "width": out_image.shape[2]})
        output_path = os.path.join(output_dir, fname)
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(out_image)
