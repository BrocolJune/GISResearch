import os
import sys
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

shp_path      = r"C:\Users\user\Desktop\Junkyo\2025\Jeju_Sectorcoupling\GIS\LSMD_ADM_SECT_UMD_50_202503.shp"
raster_folder = r"D:\Junkyo\2025\Jeju_Sectorcoupling\mask_Final"
output_csv    = r"C:\Users\user\Desktop\Junkyo\2025\Jeju_Sectorcoupling\ValidCell\PowerArea_Final.csv"

raster_files = sorted([f for f in os.listdir(raster_folder) if f.lower().endswith('.tif')])
if not raster_files:
    print("[오류] 래스터 파일이 없습니다.")
    sys.exit(1)
first_raster_path = os.path.join(raster_folder, raster_files[0])
with rasterio.open(first_raster_path) as src:
    raster_crs = src.crs

shp_gdf = gpd.read_file(shp_path)
shp_crs = shp_gdf.crs
print(f"[CRS CHECK] First raster CRS: {raster_crs}")
print(f"[CRS CHECK] Shapefile CRS: {shp_crs}")

# 좌표계가 다르면 자동 변환
if raster_crs is not None and shp_crs is not None and raster_crs != shp_crs:
    print("[경고] 좌표계가 다릅니다. Shapefile을 래스터 CRS로 변환합니다.")
    shp_gdf = shp_gdf.to_crs(raster_crs)

gdf = shp_gdf
emd_codes = gdf["EMD_CD"].astype(str).tolist()

def count_valid_cells(args):
    fname, gdf = args
    raster_path = os.path.join(raster_folder, fname)
    result = {"RasterFile": fname}
    try:
        with rasterio.open(raster_path) as src:
            gdf_proj = gdf.to_crs(src.crs)
            for idx, row in gdf_proj.iterrows():
                emd_code = str(row["EMD_CD"])
                geom = [mapping(row.geometry)]
                try:
                    out_img, _ = mask(
                        src,
                        geom,
                        all_touched=False,
                        crop=False,
                        filled=False
                    )
                    masked = out_img[0].astype("float32")
                    masked[masked.mask] = np.nan
                    valid_mask = (~np.isnan(masked)) & (masked >= 1) & (masked <= 256)
                    valid_count = np.count_nonzero(valid_mask)
                    result[emd_code] = valid_count
                except Exception as e:
                    result[emd_code] = 0
                    print(f"[경고] {fname}의 {emd_code} 영역 처리 중 오류 발생: {e}")
    except Exception as e:
        print(f"[오류] {fname} 처리 중 오류 발생: {e}")
    return result

if __name__ == "__main__":
    args_list = [(fname, gdf) for fname in raster_files]
    with Pool(cpu_count()) as pool:
        stats_list = list(tqdm(pool.imap(count_valid_cells, args_list), total=len(raster_files), desc="래스터 병렬 처리중"))
    stats_df = pd.DataFrame(stats_list)
    stats_df.to_csv(output_csv, index=False, encoding="utf-8")
    print("CSV 파일이 생성되었습니다:", output_csv)