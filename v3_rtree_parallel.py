# v3_rtree_parallel.py
"""
Hillshade Masking (Parallel, rtree, Windows/CLI용)
Jupyter Notebook에서는 동작하지 않으니 반드시 커맨드라인에서 실행하세요.
"""
import os
import rasterio
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

raster_dir = r"D:\Junkyo\2025\Jeju_Sectorcoupling\Hillshade"
mask_shp = r"C:\Users\user\Desktop\Junkyo\2025\Jeju_Sectorcoupling\GIS\Jeju_Mask.shp"
output_dir = r"D:\Junkyo\2025\Jeju_Sectorcoupling\Mask"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

mask_gdf = gpd.read_file(mask_shp).to_crs(epsg=4326)
raster_files = [f for f in os.listdir(raster_dir) if f.lower().endswith('.tif')]

def mask_one_raster(fname):
    raster_path = os.path.join(raster_dir, fname)
    with rasterio.open(raster_path) as src:
        data = src.read(1)
        profile = src.profile.copy()
        transform = src.transform
        nodata = src.nodata if src.nodata is not None else 0
        height, width = data.shape

        rows, cols = np.indices((height, width))
        xs, ys = rasterio.transform.xy(transform, rows, cols, offset="center")
        flat_points = [Point(x, y) for x, y in zip(np.ravel(xs), np.ravel(ys))]
        points_gdf = gpd.GeoDataFrame(geometry=flat_points, crs=mask_gdf.crs)

        joined = gpd.sjoin(points_gdf, mask_gdf, how="left", predicate="within")
        mask = ~joined.index_right.isna().values.reshape(data.shape)

        masked_data = data.copy()
        masked_data[mask] = nodata

        output_path = os.path.join(output_dir, fname)
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(masked_data, 1)
    return fname

if __name__ == "__main__":
    with Pool(cpu_count()) as pool:
        list(tqdm(pool.imap(mask_one_raster, raster_files), total=len(raster_files), desc="Hillshade Masking (Parallel)"))
