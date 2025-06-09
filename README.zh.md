# TDI 自動交易系統

本專案實現基於 **Traders Dynamic Index (TDI)** 指標的加密貨幣自動交易系統，並結合多週期分析與風險控管機制。程式以 Python 撰寫，可透過命令列或 Docker 部署，也提供基礎的 Flask Web 介面。

## 主要功能

- **TDI 指標與信號產生**：在不同時間週期計算 RSI、均線、波動帶等組合指標，判斷多空趨勢及進出場時機。
- **多週期交易策略**：整合週、日、4 小時與 1 小時等時間框架以確認趨勢與交易點位。
- **風險管理**：依波動度計算部位大小，使用 fractal/ATR 停損、分批獲利與移動停損等機制。
- **Binance API 介接**：可透過 API 在實盤或測試網下單並取得市場資料。
- **Docker 化與 Web 介面**：提供 docker-compose 環境與簡易前端，可在瀏覽器調整參數並啟動策略。

## 系統架構

```
TDI-Auto-Trading/
├── main.py              # 交易系統主程式
├── docker-compose.yml   # Docker Compose 設定
├── Dockerfile           # 建構映像檔設定
├── docker-run.sh        # Docker 輔助腳本
├── src/
│   ├── api/             # 與交易所溝通的封裝
│   ├── config/          # 讀取 .env 的設定檔
│   ├── indicators/      # TDI 指標實作
│   ├── strategies/      # 交易策略邏輯
│   ├── utils/           # 資料與風險管理工具
│   └── web/             # Flask Web 介面
```

## 部署方式

### 1. 一般安裝

1. 安裝依賴程式庫（需先安裝 TA-Lib）：
   ```bash
   pip install -r requirements.txt
   ```
2. 複製 `.env.template` 為 `.env`，填入 Binance API 金鑰與各項參數。
3. 直接執行主程式即可啟動交易：
   ```bash
   python main.py
   ```
   可加上 `--interval 30` 調整每次檢查間隔。

### 2. 使用 Docker

1. 確認已安裝 Docker 與 Docker Compose。
2. 複製 `.env.template` 成 `.env` 並設定參數。
3. 使腳本可執行並啟動容器：
   ```bash
   chmod +x docker-run.sh
   ./docker-run.sh start-all
   ```
   其中 `start-all` 會同時啟動交易系統與 Web 介面，Web 介面預設於 http://localhost:5001 。
4. 查看日誌或其他操作可執行 `./docker-run.sh logs`、`./docker-run.sh status` 等指令。

## 使用說明

- **即時交易**：直接執行 `python main.py` 或使用 `./docker-run.sh start`，系統會定期更新行情並依策略自動下單。
- **回測模式**：執行 `python main.py --backtest --start-date YYYY-MM-DD --end-date YYYY-MM-DD`，或使用 `./docker-run.sh backtest <start> <end>` 進行歷史測試（目前功能尚未完整實作）。
- **Web 介面**：啟動後可在瀏覽器調整交易參數並手動觸發策略，相關程式位於 `src/web` 目錄。

## 注意事項

- 本程式僅供教育與研究用途，實際交易風險自負，作者不負任何損失責任。
- 交易前請確認 `.env` 內的 API 金鑰與風險參數設定正確，建議先於 Binance 測試網驗證。

## 授權

本專案以 MIT License 釋出。
