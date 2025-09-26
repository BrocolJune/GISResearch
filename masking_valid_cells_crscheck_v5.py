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

shp_path      = r"D:\Jeju_SectorCoupling_final\Jeju_wgs1984.shp"
raster_folder = r"D:\Jeju_SectorCoupling_final\mask_Final"
output_csv    = r"D:\Jeju_SectorCoupling_final\PowerArea_Final.csv"

raster_files = sorted([f for f in os.listdir(raster_folder) if f.lower().endswith('.tif')])
if not raster_files:
    print("[오류] 래스터 파일이 없습니다.")
    sys.exit(1)

gdf = gpd.read_file(shp_path)
emd_codes = gdf["EMD_CD"].astype(str).tolist()

def count_valid_cells(fname):
    raster_path = os.path.join(raster_folder, fname)
    result = {"RasterFile": fname}
    
    # 파일 처리 시작 알림
    print(f"[시작] {fname} 처리 중...")
    
    try:
        with rasterio.open(raster_path) as src:
            total_emd = len(gdf)
            processed_count = 0
            
            for idx, row in gdf.iterrows():
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
                    
                    processed_count += 1
                    
                    # 25%, 50%, 75% 진행도에서만 출력 (성능 최적화)
                    progress_percent = (processed_count / total_emd) * 100
                    if progress_percent in [25, 50, 75] or processed_count == total_emd:
                        print(f"  └─ {fname}: {processed_count}/{total_emd} EMD 구역 완료 ({progress_percent:.0f}%)")
                        
                except Exception as e:
                    result[emd_code] = 0
                    print(f"[경고] {fname}의 {emd_code} 영역 처리 중 오류 발생: {e}")
                    processed_count += 1
                    
    except Exception as e:
        print(f"[오류] {fname} 처리 중 오류 발생: {e}")
        return result
    
    # 파일 처리 완료 알림
    print(f"[완료] {fname} 처리 완료 ✓")
    return result

if __name__ == "__main__":
    with Pool(cpu_count()) as pool:
        stats_list = list(tqdm(pool.imap(count_valid_cells, raster_files), total=len(raster_files), desc="래스터 병렬 처리중"))
    stats_df = pd.DataFrame(stats_list)
    stats_df.to_csv(output_csv, index=False, encoding="utf-8")
    print("CSV 파일이 생성되었습니다:", output_csv)
