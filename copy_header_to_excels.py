import os
import pandas as pd

# 입력 폴더 및 출력 폴더 경로
input_dir = r"C:\Users\user\Desktop\Junkyo\2025\Jeju_Sectorcoupling\ElectricityUse\Regional"
output_dir = os.path.join(input_dir, "regional_v2")
os.makedirs(output_dir, exist_ok=True)

# 엑셀 파일 목록(숫자 오름차순)
excel_files = sorted(
    [f for f in os.listdir(input_dir) if f.lower().endswith(('.xls', '.xlsx'))],
    key=lambda x: int(''.join(filter(str.isdigit, x)) or 0)
)

# 첫번째 파일 헤더 추출
first_file_path = os.path.join(input_dir, excel_files[0])
first_df = pd.read_excel(first_file_path)
header = first_df.columns.tolist()

for idx, fname in enumerate(excel_files):
    file_path = os.path.join(input_dir, fname)
    df = pd.read_excel(file_path, header=None if idx > 0 else 0)
    if idx == 0:
        # 첫 파일은 그대로 저장
        out_df = df.copy()
    else:
        # 두번째 이후 파일: 첫번째 파일 헤더로 덮어쓰기
        out_df = df.copy()
        out_df.columns = header
    output_path = os.path.join(output_dir, fname)
    out_df.to_excel(output_path, index=False)
    print(f"헤더 복사 완료: {output_path}")
