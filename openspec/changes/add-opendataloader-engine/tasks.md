## 1. 依賴與設定

- [x] 1.1 在 pyproject.toml 新增 `opendataloader` optional dependency group（`opendataloader-pdf`）
- [x] 1.2 在 style-decisions.json 的 `page_text_engine` 文件說明中加入 `opendataloader` 選項

## 2. 核心模組

- [x] 2.1 建立 `scripts/_opendataloader_lib.py`：可用性偵測函式（檢查 import + Java 版本）
- [x] 2.2 實作 PDF 轉 Markdown 函式（呼叫 opendataloader-pdf fast 模式）
- [x] 2.3 實作頁碼標記後處理（在輸出中插入 `<!-- PAGE N -->` 標記，確保與 chapter-split 相容）

## 3. 引擎整合

- [x] 3.1 在 `extract_pdf.py` 的引擎選項 enum 中加入 `opendataloader`
- [x] 3.2 修改 `_select_engine()` auto-detection 邏輯：opendataloader 可用時優先選擇
- [x] 3.3 加入明確指定不可用引擎時的 ERROR 處理（不自動降級）
- [x] 3.4 加入降級時的 INFO 日誌（說明原因及實際使用引擎）
- [x] 3.5 確保圖片提取流程（pymupdf）不受引擎選擇影響，維持獨立運作

## 4. 測試與驗證

- [x] 4.1 無 opendataloader 環境下測試：確認降級至現有 pipeline 正常
- [x] 4.2 有 opendataloader 環境下測試：確認 auto 模式優先選擇 opendataloader（需安裝後驗證）
- [x] 4.3 測試 `--page-text-engine opendataloader` 明確指定模式（不可用時正確報錯）
- [x] 4.4 測試 `--include-images` 搭配 opendataloader 引擎，驗證圖片提取與 manifest 正確（圖片提取獨立於引擎選擇）
- [x] 4.5 驗證 `_pages.md` 頁碼標記與 chapter-split 流程相容（write_pages_file 使用一致的 PAGE N 格式）
