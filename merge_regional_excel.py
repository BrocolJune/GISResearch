import os
import pandas as pd

# 입력 폴더 및 출력 파일 경로
input_dir = r"C:\Users\user\Desktop\Junkyo\2025\Jeju_Sectorcoupling\ElectricityUse\Regional\regional_v2"
output_path = os.path.join(input_dir, "regional.xlsx")

# 엑셀 파일 목록(숫자 오름차순)
excel_files = sorted(
    [f for f in os.listdir(input_dir) if f.lower().endswith(('.xls', '.xlsx'))],
    key=lambda x: int(''.join(filter(str.isdigit, x)) or 0)
)

merged_df = None
header = None
for idx, fname in enumerate(excel_files):
    file_path = os.path.join(input_dir, fname)
    df = pd.read_excel(file_path)
    # C열이 '제주특별자치도'인 행만 필터링
    filtered_df = df[df.iloc[:,2] == '제주특별자치도']
    if idx == 0:
        merged_df = filtered_df.copy()
        header = merged_df.columns
    else:
        # 열 순서 맞추기
        filtered_df = filtered_df.reindex(columns=header)
        merged_df = pd.concat([merged_df, filtered_df.iloc[1:]], ignore_index=True)

# 결과 저장
merged_df.to_excel(output_path, index=False)
print(f"병합된 파일이 저장되었습니다: {output_path}")
