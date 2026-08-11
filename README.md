# vehicle-table — 車款持有成本參考表

用來記錄每個車款的折價率與保養費用，作為購車成本評估的參考值。
稅金、保險刻意不記（與車種幾乎無關）。

## 檔案結構

| 路徑 | 用途 |
|---|---|
| `schema/vehicle.schema.json` | JSON Schema，定義欄位與規則 |
| `data/vehicles.json` | 正式資料（array，一台車一個 element） |
| `examples/vehicles.example.json` | 填寫範例（數字是示意，非真實行情） |
| `validate.py` | 驗證 + 自動重算衍生欄位 |

## 欄位對照（你的原始名詞 → schema 欄位）

| 原始名詞 | 欄位 | 說明 |
|---|---|---|
| 買入費用 | `purchase.list_price` | 牌價 |
| 真實買入費用 | `purchase.real_cost` | 實際付的：牌價 − 折讓 + 領牌雜費 |
| 賣出費用 | `selling_costs.total` | 賣車時的交易成本（過戶、整備、平台費） |
| 自行賣出估價 (1,3,5,7,10 年) | `value_checkpoints[].private_sale_price` | 每個年份一筆 |
| （備用）車商收購價 | `value_checkpoints[].dealer_tradein_price` | 選填 |
| 保養粗估費用 | `maintenance.checkpoints[].period_cost` | 「距上一個檢查點」的花費，不是累計 |

## 填寫規則

1. **一台車 = 一個 document**，`id` 用 slug（`toyota-corolla-cross-2024-hybrid`）。
   同車款不同動力（油電 vs 純油）拆成不同 document，因為折價曲線差很多。
2. **年份只准 1 / 3 / 5 / 7 / 10**，每台車都用同一組檢查點才能互相比較。
3. **每個估價都要填 `assumed_km`**：行情是看里程帶報價的。你一年開 6000–8000 km，
   低於台灣平均（約 10000–15000 km），所以你的車在同年份會落在「低里程」帶，
   估價時要拿低里程的成交價來填，這就是為什麼 km 要記下來。
4. **比例一律以 `real_cost` 為分母**：折價是相對「你實際付了多少」，不是牌價。
5. **每筆估價都要填 `source` / `confidence` / `as_of`**：行情會變，
   之後回頭看才知道這個數字是幾月、根據什麼、多可信。大約一年回頭更新一次。
6. **標了 DERIVED 的欄位不要手算**（`retention_ratio`、`depreciation_amount`、
   `cumulative_cost`、整個 `cost_summary`），填完原始數字後跑：

   ```sh
   python3 validate.py data/vehicles.json --fix
   ```

   它會重算所有衍生欄位並寫回檔案。不帶 `--fix` 則只檢查、不改檔。

## 新增一台車的流程

1. 從 `examples/vehicles.example.json` 複製一個 element 到 `data/vehicles.json`。
2. 填 `purchase`（牌價、折讓、雜費、實付）。
3. 到 8891 / 車商報價查該車款 1/3/5/7/10 年、對應低里程帶的售價，
   填進 `value_checkpoints[].private_sale_price`。
4. 查原廠保養手冊或車主社群，粗估各區間保養費填 `period_cost`。
5. 跑 `python3 validate.py data/vehicles.json --fix`。
6. `cost_summary` 就是答案：每年攤提成本 (`cost_per_year`) 與每公里成本 (`cost_per_km`)，
   拿這兩個數字跨車款比較。
