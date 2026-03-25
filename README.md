# APRS私人通联历史数据可视化地图

## Before Start
### 依赖
运行本项目需要安装以下 Python 核心库：
```
pip install pandas aprslib folium re os math collections
```
### EXCEL文件和HTML文件路径
- 本项目已适配 **相对路径自适应** 逻辑，无需手动修改代码中的 `D:\...` 绝对路径，程序会自动获取当前脚本所在的目录 (`BASE_DIR`)。
- 请确保你的数据文件名为 **`APRS_DATA.xlsx`**，并将其放置在与 `aprs_radar.py` 相同的文件夹下。
## Start
### EXCEL表格构建
- DATA的第一列输入时间，保持`yyyy-m-d hh:mm:ss`格式。
- DATA的第二列输入原始数据，可从[aprs.tv](aprs.tv)或者[aprs.fi](aprs.fi )网站中获取，例如`ABCDEF-7>APOG77,CCCCCC-3*,WIDE1*,WIDE2-1,qAS,DDDDDD-10:!/::!!kk!!0  !test`。

- Station第一列填入`呼号+SSID`，例如`ABCDEF-11`，手动从网站获取（必填）。
- Station第二列，第四列，第五列可填入对应信息。
- Station第三列填入对应台站定位坐标，例如`116°3'48" E 39°51'55" N`（必填）。

## 运行逻辑
- **自动聚类**: 代码内置 `CLUSTER_RADIUS_M = 500`。发射端 500 米内的移动坐标将被自动聚合为同一个固定点，防止地图上出现细碎乱点。
- **路径追踪**:
    - 自动识别并绘制 **发射端 -> 转发站 -> 接收网关** 的物理跳点。
    - **红色连线** 表示发射端的第一跳，**蓝色连线** 表示后续转发路径。
- **UI 优化**:
    - **Popups 压缩**: 通过内联 CSS (`line-height:1.2; margin:0;`) 极限压缩台站和路径的弹窗高度，显示更多信息。
    - **全选/清空**: 地图右侧图层控制台增加了原生 JavaScript 注入的“全选”和“清空”按钮，方便按日期快速筛选。
	- **`MIN_WEIGHT` (2)** & **`MAX_WEIGHT` (8)**: 系统会根据同一路径出现的**频率**自动计算粗细，频率越高（热点路径），线条越粗，视觉上实现“热力路径”的效果。
	- **`MY_CALLSIGN`**: 设置你的呼号（如 `ABCDEF-7`）。
## 运行
```
python APRS_extract_3.0.py
```
- 直接使用浏览器打开网页即可
## 显示效果
### 中继及网关路径图
<img width="843" height="923" alt="图片" src="https://github.com/user-attachments/assets/23a7185c-b12b-4ad7-8069-0dfc62da39ac" />

### 点击通联路径显示原始数据
<img width="562" height="174" alt="图片" src="https://github.com/user-attachments/assets/5d5a6818-0d32-4dff-a09a-29e15cf169e4" />

### 时间筛选（右上角）
<img width="109" height="125" alt="图片" src="https://github.com/user-attachments/assets/5785dbe0-70d5-4962-94ef-7a56581161c1" />

### 自动聚类坐标合并
<img width="197" height="162" alt="图片" src="https://github.com/user-attachments/assets/b785fa13-4636-4024-8dc1-528e5c7c6ddd" />

## 建议箱
感谢大家留下宝贵意见及建议
Email： cinerzhao@outlook.com

## Star History
<a href="https://star-history.com/#Cinerzhao/APRS_MAP&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Cinerzhao/APRS_MAP&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Cinerzhao/APRS_MAP&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Cinerzhao/APRS_MAP&type=Date" />
 </picture>
</a>
