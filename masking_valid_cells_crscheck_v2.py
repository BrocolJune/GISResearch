# masking_valid_cells_crscheck_v2.py
"""
1. shp, raster 파일 간 지리좌표계 확인, 불일치 시 바로 종료
2. shp 필드 내 EMD_CD를 이용해 polygon 구분
3. 각 폴리곤 내부에 있는 셀들에 대해 no data와 0인 셀을 제외하고 1~256 범위 내에 존재하는 셀 개수 확인
4. 해당 셀 개수를 csv로 출력
"""
import os
import sys
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping
import geopandas as gpd
import pandas as pd
from tqdm import tqdm

# 경로 설정
shp_path      = r"C:\Users\user\Desktop\Junkyo\2025\Jeju_Sectorcoupling\GIS\Jeju_Polygon.shp"
raster_folder = r"D:\Junkyo\2025\Jeju_Sectorcoupling\mask_v5"
output_csv    = r"C:\Users\user\Desktop\Junkyo\2025\Jeju_Sectorcoupling\ValidCell\PowerArea_v5.csv"

# --- CRS check for first raster and shapefile ---
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
if raster_crs is not None and shp_crs is not None and raster_crs != shp_crs:
    print("[오류] 첫번째 래스터와 Shapefile의 CRS가 다릅니다! 좌표계 변환 후 다시 실행하세요.")
    sys.exit(1)

# Shapefile 불러오기 및 CRS 확인
gdf = shp_gdf
if gdf.crs is None or gdf.crs.to_epsg() != 2097:
    gdf = gdf.set_crs(epsg=2097, allow_override=True)

# 1행: EMD_CD 필드값 출력
print('EMD_CD 목록:', gdf['EMD_CD'].astype(str).tolist())

# 2행: 각 EMD_CD에 해당하는 NEAR_FID 필드값 출력
for emd_cd in gdf['EMD_CD'].astype(str).tolist():
    near_fid_values = gdf[gdf['EMD_CD'].astype(str) == emd_cd]['NEAR_FID'].tolist()
    print(f'EMD_CD: {emd_cd}, NEAR_FID: {near_fid_values}')

# EMD_CD 목록 추출
emd_codes = gdf["EMD_CD"].astype(str).tolist()

# 결과 저장 리스트
stats_list = []

for fname in tqdm(raster_files, desc="래스터 처리중"):
    raster_path = os.path.join(raster_folder, fname)

    with rasterio.open(raster_path) as src:
        # 좌표계 변환
        gdf_proj = gdf.to_crs(src.crs)

        # 파일 결과 저장용 딕셔너리 (파일명 + 각 지역 유효 셀 수)
        result = {"RasterFile": fname}

        for idx, row in gdf_proj.iterrows():
            emd_codes = str(row["EMD_CD"])
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

                # 1~256 범위 내 값만 카운트
                valid_mask = (~np.isnan(masked)) & (masked >= 1) & (masked <= 256)
                valid_count = np.count_nonzero(valid_mask)
                result[emd_codes] = valid_count

            except Exception as e:
                # 예외 발생 시 해당 구역은 0으로 간주
                result[emd_codes] = 0
                print(f"[경고] {fname}의 {emd_codes} 영역 처리 중 오류 발생: {e}")

        stats_list.append(result)

# 결과 DataFrame 생성 및 저장
stats_df = pd.DataFrame(stats_list)
stats_df.to_csv(output_csv, index=False, encoding="utf-8")

print("CSV 파일이 생성되었습니다:", output_csv)
