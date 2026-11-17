#!/usr/bin/env python3
import os
sys = __import__('sys')
json = __import__('json')
math = __import__('math')
from datetime import datetime, timedelta

def parse_iso(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except Exception:
        return None

def round_2dec(x):
    val = math.floor(x * 100 + 0.5) / 100
    if math.isclose(val, round(val), abs_tol=1e-9):
        return int(round(val))
    return val

def percentile(sorted_list, p):
    if not sorted_list:
        return 0.0
    n = len(sorted_list)
    if n == 1:
        return sorted_list[0]
    idx = p * (n - 1)
    i = int(idx)
    frac = idx - i
    if i + 1 < n:
        return sorted_list[i] * (1 - frac) + sorted_list[i + 1] * frac
    return sorted_list[i]

def median(lst):
    if not lst:
        return 0.0
    s = sorted(lst)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    else:
        return (s[n // 2 - 1] + s[n // 2]) / 2.0

def process_case(data):
    day_start_str = data.get('day_start')
    day_dt = parse_iso(day_start_str)
    
    # 1. Anchor on hour 1 (p1) - find row whose "hour" is 1
    p1 = 1.0
    known = data.get('known', [])
    hour1_found = False
    if known and isinstance(known, list):
        for row in known:
            if row.get('hour') == 1:
                v = row.get('viewers')
                if v is not None:
                    p1 = max(1.0, float(v))
                    hour1_found = True
                    break
    if not hour1_found:
        history = data.get('history', [])
        if history:
            last_pt = history[-1]
            v = last_pt.get('viewers')
            if v is not None:
                p1 = max(1.0, float(v))
                
    # Pre-release baseline of target game
    base = p1
    history = data.get('history', [])
    if day_dt and history:
        start_72 = day_dt - timedelta(hours=72)
        pre_viewers = []
        for pt in history:
            dt = parse_iso(pt.get('at'))
            if dt and start_72 <= dt < day_dt:
                v = pt.get('viewers')
                if v is not None:
                    pre_viewers.append(float(v))
        if pre_viewers:
            base = max(pre_viewers)
    r = p1 / max(1.0, base)
    
    # 2. Donor pool
    comparables = data.get('comparables', [])
    donors = []
    for comp in comparables:
        unlock = comp.get('unlock', '')
        if 'Tier: comparable' not in unlock:
            continue
        comp_day_str = comp.get('day_start')
        comp_day_dt = parse_iso(comp_day_str)
        if not comp_day_dt:
            continue
        hourly = comp.get('hourly', [])
        if not hourly:
            continue
            
        # Build release-day hourly map for hour 1 to 24
        comp_hourly_map = {}
        for pt in hourly:
            dt = parse_iso(pt.get('from'))
            if not dt:
                continue
            # Check which hour h (1 to 24)
            diff_hours = (dt - comp_day_dt).total_seconds() / 3600.0
            h = int(math.floor(diff_hours)) + 1
            if 1 <= h <= 24:
                v = pt.get('viewers')
                if v is not None and h not in comp_hourly_map:
                    comp_hourly_map[h] = float(v)
                    
        if 1 not in comp_hourly_map:
            continue
        v1_comp = comp_hourly_map[1]
        if v1_comp <= 0:
            continue
            
        # Comp pre-release baseline (hourly points in 72 hours before comp day_start)
        comp_base = v1_comp
        comp_start_72 = comp_day_dt - timedelta(hours=72)
        comp_pre_viewers = []
        for pt in hourly:
            dt = parse_iso(pt.get('from'))
            if dt and comp_start_72 <= dt < comp_day_dt:
                v = pt.get('viewers')
                if v is not None:
                    comp_pre_viewers.append(float(v))
        if comp_pre_viewers:
            comp_base = max(comp_pre_viewers)
            
        rd = v1_comp / max(1.0, comp_base)
        
        # Log-ratios for hours 2 to 24
        log_ratios = {}
        for h in range(2, 25):
            if h in comp_hourly_map:
                vh = comp_hourly_map[h]
                if vh > 0:
                    log_ratios[h] = math.log(vh / v1_comp)
                    
        donors.append({
            'rd': rd,
            'log_rd': math.log(rd),
            'log_ratios': log_ratios
        })
        
    # 3. Donor selection
    target_log_r = math.log(r)
    selected_donors = []
    for d in donors:
        if abs(d['log_rd'] - target_log_r) <= math.log(2):
            selected_donors.append(d)
            
    if len(selected_donors) < 8:
        # Sort all donors by absolute difference in log ratios
        sorted_donors = sorted(donors, key=lambda d: abs(d['log_rd'] - target_log_r))
        selected_donors = sorted_donors[:8]
        
    # 4 & 5. Shape and Spread for hours 2 to 24
    hours_result = []
    z_vals = [-1.645, -0.674, 0.0, 0.674, 1.645]
    
    for h in range(2, 25):
        h_log_ratios = []
        for d in selected_donors:
            if h in d['log_ratios']:
                h_log_ratios.append(d['log_ratios'][h])
                
        if h_log_ratios:
            m_h = median(h_log_ratios)
            sorted_hr = sorted(h_log_ratios)
            q25 = percentile(sorted_hr, 0.25)
            q75 = percentile(sorted_hr, 0.75)
            iqr = q75 - q25
            s_h = iqr / 1.349
        else:
            m_h = 0.0
            s_h = 0.0
            
        spread_h = max(s_h, 0.15 * math.sqrt(h - 1))
        
        row_q = []
        for z in z_vals:
            val = p1 * math.exp(m_h + z * spread_h)
            row_q.append(val)
            
        # Round half up to 2 decimals
        rounded_q = [round_2dec(val) for val in row_q]
        
        # Clamp min 0.01 and max 1e9 BEFORE strictly increasing fix
        clamped_q = [min(1e9, max(0.01, q)) for q in rounded_q]
        
        # Enforce strictly increasing: going left to right, if not greater than previous, raise to previous + 0.01
        final_q = [clamped_q[0]]
        for i in range(1, len(clamped_q)):
            prev = final_q[-1]
            curr = clamped_q[i]
            if curr <= prev:
                curr = round_2dec(prev + 0.01)
            final_q.append(curr)
            
        # Re-check upper bound 1e9
        final_q = [min(1e9, q) for q in final_q]
        
        hours_result.append({
            'hour': h,
            'q': final_q
        })
        
    return {'hours': hours_result}

def main():
    input_dir = os.environ.get('MAKEFUN_INPUT_DIR', '/input')
    output_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    if not os.path.exists(input_dir):
        return
        
    in_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.in')])
    for fname in in_files:
        in_path = os.path.join(input_dir, fname)
        base_id = fname[:-3]
        out_name = base_id + '.out'
        out_path = os.path.join(output_dir, out_name)
        
        try:
            with open(in_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
            
        result = process_case(data)
        
        json_str = json.dumps(result, separators=(',', ':'))
        output_content = json_str + '\n'
        
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(output_content)

if __name__ == '__main__':
    main()
