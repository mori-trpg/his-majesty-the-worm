## Context

現有 `extract_pdf.py` 支援三個引擎（pymupdf、markitdown、ocr），透過 layout 偵測和品質探測自動選擇。opendataloader-pdf 經實測品質顯著優於現有引擎，需整合為第四個引擎選項並在可用時作為預設。

關鍵現有架構：
- `extract_pdf.py`：主入口，引擎選擇邏輯在 `_select_engine()`
- `_layout_lib.py`：layout 偵測與 pymupdf 品質探測
- `style-decisions.json`：per-document 引擎覆寫設定

## Goals / Non-Goals

**Goals:**
- 將 opendataloader-pdf 整合為 `page_text_engine` 的新選項
- 有 Java + opendataloader-pdf 時自動優先使用
- 無 Java 時無感降級至現有 pipeline
- 保持所有現有引擎功能不變

**Non-Goals:**
- 不整合 opendataloader hybrid 模式（需額外後端服務，複雜度過高）
- 不移除任何現有引擎
- 不修改圖片提取流程（仍用 pymupdf）

## Decisions

### D1: 僅整合 fast 模式，不整合 hybrid

**選擇**: 只用 `opendataloader-pdf` 的 fast（本地）模式

**理由**: Hybrid 需要啟動獨立 Java 後端服務（`opendataloader-pdf-hybrid --port 5002`），對 CLI 工具來說使用門檻過高。Fast 模式品質已經過實測確認足夠好。

**替代方案**: 整合 hybrid → 拒絕，因為需要用戶管理額外服務生命週期。

### D2: 引擎偵測順序

**選擇**: `opendataloader` → `pymupdf`（品質探測）→ `markitdown` → `ocr`

**理由**: opendataloader 在表格和標題的精度全面領先，應在可用時優先。但需先檢查 Java 環境和套件是否安裝。

**替代方案**: 保持現有順序，opendataloader 僅作為手動選項 → 拒絕，因為目標是改善預設體驗。

### D3: 封裝為獨立模組 `_opendataloader_lib.py`

**選擇**: 新增 `scripts/_opendataloader_lib.py` 封裝所有 opendataloader 互動

**理由**: 與現有 `_ocr_lib.py`、`_layout_lib.py` 架構一致。包含：可用性偵測、PDF 轉 Markdown 呼叫、輸出格式適配。

### D4: opendataloader-pdf 作為可選依賴

**選擇**: 在 `pyproject.toml` 中以 optional dependency group `[opendataloader]` 安裝

**理由**: 避免強制所有用戶安裝 Java。`uv pip install -e ".[opendataloader]"` 安裝，無此套件時自動跳過。

## Risks / Trade-offs

- **[Java 依賴]** → 透過可選依賴 + 自動降級緩解；缺少 Java 時 log 提示但不報錯
- **[JVM 啟動延遲]** → 每次 convert() 啟動 JVM，批次處理時較慢 → 可接受，PDF 提取是一次性操作
- **[opendataloader API 變動]** → 專案較新，API 可能變 → 封裝在獨立模組中，影響範圍有限
- **[頁碼標記格式]** → opendataloader 輸出可能無 `<!-- PAGE N -->` 標記 → 需在 lib 中後處理加入，以相容 chapter-split
