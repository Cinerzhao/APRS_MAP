import pandas as pd
import aprslib
import folium
from folium.features import DivIcon
from folium.plugins import MousePosition
import re
import os
import math
from collections import Counter, defaultdict


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PATH_EXCEL = os.path.join(BASE_DIR, "APRS_DATA.xlsx")
PATH_HTML = os.path.join(BASE_DIR, "my_aprs_map.html")


# ==========================================
# 线条参数和呼号设置
# ==========================================
MY_CALLSIGN = "ABCDEF-7"
LINE_COLOR = "#0078D7"       
MY_LINE_COLOR = "#FF4500"    
STATION_LABEL_COLOR = "#00008B"
MY_ICON_COLOR = "red"        
STATION_ICON_COLOR = "blue"  

# 连线宽度范围和聚类半径（单位：米）
MIN_WEIGHT = 2               
MAX_WEIGHT = 8               
CLUSTER_RADIUS_M = 500

# 这里绝对路径可以根据需要替换
# PATH_EXCEL = r"D:\Code\HAM\APRS\Local_APRS\上传Github\APRS_DATA.xlsx"
# PATH_HTML = r"D:\Code\HAM\APRS\Local_APRS\上传Github\my_aprs_map.html"
# ==========================================

def haversine(pos1, pos2):
    lat1, lon1 = pos1; lat2, lon2 = pos2
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def dms_to_dd(dms_str):
    nums = re.findall(r"(\d+(?:\.\d+)?)", dms_str)
    if len(nums) < 3: return None
    d, m, s = map(float, nums[:3])
    return d + m/60 + s/3600

def generate_map():
    print("正在读取数据并生成地图...")
    if not os.path.exists(PATH_EXCEL):
        print(f"找不到文件: {PATH_EXCEL}")
        return

    xl = pd.ExcelFile(PATH_EXCEL)
    df_stations = pd.read_excel(xl, sheet_name='Station')
    station_db = {}
    station_popups = {}
    
    for _, row in df_stations.iterrows():
        call = str(row.iloc[0]).strip()
        msg = str(row.iloc[1]) if pd.notna(row.iloc[1]) else "无"
        coord_raw = str(row.iloc[2])
        extra_info = str(row.iloc[3]) if pd.notna(row.iloc[3]) else "无"
        device = str(row.iloc[4]) if pd.notna(row.iloc[4]) else "未知"
        parts = coord_raw.split(' E ')
        if len(parts) == 2:
            lon, lat = dms_to_dd(parts[0]), dms_to_dd(parts[1])
            if lon and lat:
                station_db[call] = (lat, lon)
                html = f"""
                <div style="white-space:nowrap; font-family: Microsoft YaHei, sans-serif; font-size:12px; line-height:1.2;">
                    <p style="margin:0;"><b style="color:{STATION_LABEL_COLOR}; font-size:14px;">台站: {call}</b></p>
                    <hr style='margin:3px 0; border:0; border-top:1px solid #ccc;'>
                    <p style="margin:0;"><b>坐标:</b> {coord_raw}</p>
                    <p style="margin:0;"><b>消息:</b> {msg}</p>
                    <p style="margin:0;"><b>设备:</b> {device}</p>
                </div>
                """
                station_popups[call] = html

    df_logs = pd.read_excel(xl, sheet_name='DATA')
    physical_hops = []
    daily_paths = set()
    my_clusters = []
    hop_logs = defaultdict(list)
    date_buckets = defaultdict(list)

    for _, row in df_logs.iterrows():
        time_str = str(row.iloc[0]).strip()
        raw_packet = str(row.iloc[1]).strip()
        date = time_str.split(' ')[0]
        try:
            data = aprslib.parse(raw_packet)
            if data['latitude'] == 0: continue
            raw_pos = (data['latitude'], data['longitude'])
            final_pos = raw_pos
            for c_pos in my_clusters:
                if haversine(raw_pos, c_pos) < CLUSTER_RADIUS_M:
                    final_pos = c_pos
                    break
            if final_pos == raw_pos: my_clusters.append(raw_pos)
            p_list = [h.replace('*','') for h in data['path']]
            path_key = f"{date}:{data['from']}>{'>'.join(p_list)}"
            if path_key in daily_paths: continue
            daily_paths.add(path_key)

            origin = final_pos
            is_first = True
            for hop in p_list:
                if hop in station_db:
                    target = station_db[hop]
                    seg_key = (origin, target)
                    physical_hops.append((origin, target, is_first))
                    log_entry = f"<div style='white-space:nowrap; border-bottom:1px solid #ddd; padding:2px 0; line-height:1.2;'><b>时间:</b> {time_str}<br><b>Log:</b> <code>{raw_packet}</code></div>"
                    hop_logs[seg_key].append(log_entry)
                    date_buckets[date].append({'start': origin, 'end': target, 'is_my': is_first, 'seg_key': seg_key, 'my_pos': final_pos if is_first else None})
                    origin = target
                    is_first = False
        except: continue

    m = folium.Map(location=[39.98, 116.35], zoom_start=11)
    MousePosition(position='topright', separator=' | ', prefix='坐标:', lng_first=True).add_to(m)

    for name, pos in station_db.items():
        folium.Marker(pos, icon=folium.Icon(color=STATION_ICON_COLOR, icon='tower'), popup=folium.Popup(station_popups.get(name, name), max_width=500)).add_to(m)
        folium.Marker(pos, icon=DivIcon(icon_size=(150,36), icon_anchor=(7, 18), html=f'<div style="font-size:11pt;color:{STATION_LABEL_COLOR};font-weight:bold;white-space:nowrap;">{name}</div>')).add_to(m)

    hop_stats = Counter([(h[0], h[1]) for h in physical_hops])
    if not hop_stats: return
    max_f, min_f = max(hop_stats.values()), min(hop_stats.values())
    sorted_dates = sorted(date_buckets.keys())
    
    for date in sorted_dates:
        fg = folium.FeatureGroup(name=date, show=True)
        day_draw_pos = set()
        for item in date_buckets[date]:
            freq = hop_stats[item['seg_key']]
            w = MIN_WEIGHT + (freq-min_f)/(max_f-min_f)*(MAX_WEIGHT-MIN_WEIGHT) if max_f > min_f else MIN_WEIGHT
            color = MY_LINE_COLOR if item['is_my'] else LINE_COLOR
            dist_km = haversine(item['start'], item['end']) / 1000
            combined_logs = f"<div style='max-height: 250px; overflow-y: auto; padding:5px; min-width:320px; line-height:1.2;'><b style='color:red;'>[ 距离: {dist_km:.2f} km ]</b>" + "".join(hop_logs[item['seg_key']]) + "</div>"
            
            folium.PolyLine([item['start'], item['end']], color=color, weight=w + (1.5 if item['is_my'] else 0), opacity=0.8).add_to(fg)
            folium.PolyLine([item['start'], item['end']], color=color, weight=25, opacity=0, popup=folium.Popup(combined_logs, max_width=600)).add_to(fg)
            
            if item['my_pos'] and item['my_pos'] not in day_draw_pos:
                p = item['my_pos']
                my_popup_html = f"""
                <div style="white-space:nowrap; font-size:12px; line-height:1.2;">
                    <p style="margin:0;"><b style="color:{MY_LINE_COLOR}; font-size:14px;">发射端: {MY_CALLSIGN}</b></p>
                    <hr style='margin:3px 0; border:0; border-top:1px solid #ccc;'>
                    <p style="margin:0;"><b>纬度:</b> {p[0]:.5f}</p>
                    <p style="margin:0;"><b>经度:</b> {p[1]:.5f}</p>
                </div>
                """
                folium.Marker(p, icon=folium.Icon(color=MY_ICON_COLOR, icon='user'), popup=folium.Popup(my_popup_html, max_width=300)).add_to(fg)
                day_draw_pos.add(p)
        fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    select_all_script = """
    <script>
    window.onload = function() {
        var container = document.querySelector('.leaflet-control-layers-list');
        if (!container) return;
        var btnDiv = document.createElement('div');
        btnDiv.style.padding = '5px 0'; btnDiv.style.borderBottom = '1px solid #ccc'; btnDiv.style.marginBottom = '5px';
        btnDiv.innerHTML = '<button id="selectAll" style="padding:2px 5px; cursor:pointer;">全选</button> ' + 
                           '<button id="deselectAll" style="padding:2px 5px; cursor:pointer;">清空</button>';
        container.prepend(btnDiv);
        document.getElementById('selectAll').onclick = function() {
            var inputs = container.querySelectorAll('input[type="checkbox"]');
            inputs.forEach(input => { if(!input.checked) input.click(); });
        };
        document.getElementById('deselectAll').onclick = function() {
            var inputs = container.querySelectorAll('input[type="checkbox"]');
            inputs.forEach(input => { if(input.checked) input.click(); });
        };
    };
    </script>
    """
    m.get_root().html.add_child(folium.Element(select_all_script))

    m.save(PATH_HTML)
    print(f"地图已生成{PATH_HTML}")

if __name__ == "__main__":
    generate_map()