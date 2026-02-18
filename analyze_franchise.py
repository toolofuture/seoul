import csv
import sys

def analyze(input_file):
    data = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                for key in ['total_stores', 'new_open', 'terminate', 'cancel', 'transfer', 'avg_sales', 'area_sales']:
                    row[key] = int(row[key])
            except ValueError:
                continue
                
            # 이상치 필터링
            if row['new_open'] > 20000: continue # 편의점 최대 규모 고려
            if row['terminate'] + row['cancel'] > 20000: continue
            
            # 연도가 데이터로 들어간 경우 필터링 (2019~2025)
            suspicious_numbers = range(2019, 2026)
            # 신규, 종료, 해지, 명의변경 중 하나라도 연도와 같으면 의심
            if (row['new_open'] in suspicious_numbers or 
                row['terminate'] in suspicious_numbers or
                row['cancel'] in suspicious_numbers):
                # 단, 합리적인 수치일 수도 있으므로, total_stores와 비교
                # 가맹점이 10000개인데 2023개 폐점은 가능.
                # 그러나 가맹점이 10개인데 2023개 폐점은 불가능.
                if row['total_stores'] < 1000:
                    continue
            
            # 평균 매출액 필터링 (50억 이상 제외 - 단위 천원 기준 5,000,000)
            if row['avg_sales'] > 5000000: continue
            
            net_growth = row['new_open'] - (row['terminate'] + row['cancel'])
            row['net_growth'] = net_growth
            
            if row['total_stores'] > 0:
                row['growth_rate'] = net_growth / row['total_stores']
                row['failure_rate'] = (row['terminate'] + row['cancel']) / row['total_stores']
            else:
                row['growth_rate'] = 0
                row['failure_rate'] = 0
            
            data.append(row)

    sorted_by_new = sorted(data, key=lambda x: x['new_open'], reverse=True)
    sorted_by_net_growth = sorted(data, key=lambda x: x['net_growth'], reverse=True)
    sorted_by_sales = sorted(data, key=lambda x: x['avg_sales'], reverse=True)
    sorted_by_close = sorted(data, key=lambda x: (x['terminate'] + x['cancel']), reverse=True)

    print("=== 신규 개점 Top 10 ===")
    for item in sorted_by_new[:10]:
        print(f"{item['brand']}: {item['new_open']}개 (전체 {item['total_stores']})")
        
    print("\n=== 순증가(성장) Top 10 ===")
    for item in sorted_by_net_growth[:10]:
        print(f"{item['brand']}: +{item['net_growth']} (신규 {item['new_open']}, 폐점 {item['terminate']+item['cancel']})")

    print("\n=== 평균 매출 Top 10 (단위:천원) ===")
    for item in sorted_by_sales[:10]:
        print(f"{item['brand']}: {item['avg_sales']:,} (가맹점 {item['total_stores']})")
        
    print("\n=== 폐점(종료+해지) Top 10 ===")
    for item in sorted_by_close[:10]:
        print(f"{item['brand']}: {item['terminate']+item['cancel']} (전체 {item['total_stores']})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_franchise.py <csv_file>")
        sys.exit(1)
    analyze(sys.argv[1])
