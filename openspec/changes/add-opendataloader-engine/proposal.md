## Why

現有的 PDF 提取 pipeline（pymupdf + markitdown）在表格（0.40）和標題層級（0.41）的精度偏低，對遊戲規則書中大量的數值表格、裝備清單、骰表等結構化內容造成顯著的手動修正成本。opendataloader-pdf hybrid 模式在這兩項分別達到 0.93 和 0.83，經實測品質確認良好。

## What Changes

- 新增 `opendataloader` 作為 `extract_pdf.py` 的第四個 `page_text_engine` 選項
- 將 `opendataloader` 設為 auto-detection 的優先引擎（有 Java 環境時）
- 現有 pymupdf / markitdown / ocr 引擎保留為 fallback
- `style-decisions.json` 的 `page_text_engine` 支援新值 `opendataloader`
- 新增 Java 11+ 為可選依賴（無 Java 時自動降級至現有引擎）

## Capabilities

### New Capabilities

- `opendataloader-engine`: opendataloader-pdf 引擎整合，包含安裝偵測、呼叫介面、輸出轉換
- `engine-auto-fallback`: 引擎自動偵測與優雅降級邏輯（有 Java → opendataloader 優先；無 Java → 現有 pipeline）

### Modified Capabilities

（無現有 spec 需修改）

## Impact

- **scripts/extract_pdf.py**: 新增引擎選項與 auto-detection 邏輯
- **新增 scripts/_opendataloader_lib.py**: opendataloader 呼叫封裝
- **pyproject.toml**: 新增 `opendataloader-pdf` 為可選依賴
- **style-decisions.json schema**: `page_text_engine` enum 擴充
- **外部依賴**: Java 11+（可選）、`opendataloader-pdf` Python 套件
