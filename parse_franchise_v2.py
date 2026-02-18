import re
import sys
import glob
import os
import csv

def remove_tags(text):
    return re.sub(r'<[^>]+>', ' ', text)

def parse_int(s):
    if s == '-': return 0
    s = s.replace(',', '')
    try:
        return int(float(s))
    except:
        return 0

def get_brand_name(filename):
    name = filename.replace('.html', '')
    parts = name.split('_')
    # 정보공개서_... 패턴 처리
    if parts[0] == '정보공개서':
        # parts가 ['정보공개서', '법인명', '브랜드명', '2024'] 이런 식일 수 있음
        # 또는 ['정보공개서', '브랜드명', '2024']
        
        # 날짜 제외하고 뒤에서부터 브랜드명 추측
        candidates = [p for p in parts if not re.match(r'^20\d\d$', p) and p != '정보공개서']
        if len(candidates) >= 2:
            # 보통 법인명_브랜드명 순서이거나 브랜드명_법인명 순서임.
            # 하지만 브랜드명이 더 중요함. 파일명을 보면 '정보공개서_(주)본아이에프_본죽_2024' -> 본죽 (뒤쪽)
            return candidates[-1]
        elif candidates:
            return candidates[0]
    else:
        # 고래국밥1980_고래드림_2024 -> 고래국밥1980 (앞쪽)
        return parts[0]
        
    return name

def parse_file(filepath):
    filename = os.path.basename(filepath)
    brand_name = get_brand_name(filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return None

    match = re.search(r'(Ⅱ|II)\s*\.\s*.*?(Ⅲ|III)\s*\.\s*', content, re.DOTALL)
    if match:
        content = match.group(0)
    
    content = remove_tags(content)
    tokens = [t.strip() for t in content.split() if t.strip()]
    
    data = {
        'brand': brand_name,
        'year': 0,
        'new_open': 0,
        'terminate': 0,
        'cancel': 0,
        'transfer': 0,
        'total_stores': 0,
        'avg_sales': 0,
        'area_sales': 0
    }
    
    years_data = []
    for i, token in enumerate(tokens):
        if re.match(r'^20[12][0-9]$', token):
             if i + 6 < len(tokens):
                 valid = True
                 for k in range(1, 7):
                     if not re.match(r'^[\d,-]+$', tokens[i+k]):
                         valid = False
                         break
                 if valid:
                     years_data.append(i)
    
    if years_data:
        last_idx = years_data[-1]
        data['year'] = tokens[last_idx]
        data['new_open'] = parse_int(tokens[last_idx+2])
        data['terminate'] = parse_int(tokens[last_idx+3])
        data['cancel'] = parse_int(tokens[last_idx+4])
        data['transfer'] = parse_int(tokens[last_idx+5])
        data['total_stores'] = parse_int(tokens[last_idx+6]) 

    total_indices = [i for i, x in enumerate(tokens) if x == '전체']
    
    for idx in reversed(total_indices):
        if idx + 2 < len(tokens):
            t1 = tokens[idx+1]
            t2 = tokens[idx+2]
            
            if re.match(r'^[\d,-]+$', t1) and re.match(r'^[\d,-]+$', t2):
                v1 = parse_int(t1)
                v2 = parse_int(t2)
                
                t3 = '0'
                if idx + 3 < len(tokens) and re.match(r'^[\d,-]+$', tokens[idx+3]):
                    t3 = tokens[idx+3]
                
                v3 = parse_int(t3)
                
                data['avg_sales'] = v2
                data['area_sales'] = v3
                break
                
    return data

def main():
    if len(sys.argv) < 3:
        print("Usage: python parse_franchise_v2.py <input_dir> <output_csv>")
        sys.exit(1)
        
    input_dir = sys.argv[1]
    output_file = sys.argv[2]
    
    files = glob.glob(os.path.join(input_dir, "*.html"))
    
    headers = ['brand', 'year', 'total_stores', 'new_open', 'terminate', 'cancel', 'transfer', 'avg_sales', 'area_sales']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        count = 0
        for i, filepath in enumerate(files):
            if i % 100 == 0:
                print(f"Processing {i}/{len(files)}...", file=sys.stderr)
                
            res = parse_file(filepath)
            if res and (res['total_stores'] > 0 or res['new_open'] > 0 or res['avg_sales'] > 0):
                row = {k: res.get(k, 0) for k in headers}
                writer.writerow(row)
                count += 1
                
    print(f"Done. {count} items saved to {output_file}")

if __name__ == "__main__":
    main()
