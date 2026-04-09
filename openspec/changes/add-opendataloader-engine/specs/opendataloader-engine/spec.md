## ADDED Requirements

### Requirement: opendataloader PDF 轉 Markdown
系統 SHALL 支援透過 opendataloader-pdf（fast 模式）將 PDF 轉換為 Markdown。轉換結果 SHALL 包含完整的標題層級、表格結構、清單格式。

#### Scenario: 成功轉換 PDF
- **WHEN** 使用者指定 `--page-text-engine opendataloader` 執行 extract_pdf.py
- **THEN** 系統使用 opendataloader-pdf 提取 PDF 文字內容並輸出 Markdown

#### Scenario: 輸出包含頁碼標記
- **WHEN** opendataloader 完成 PDF 轉換
- **THEN** 輸出的 `_pages.md` 檔案 SHALL 包含 `<!-- PAGE N -->` 標記，與現有引擎格式一致，以相容 chapter-split 流程

#### Scenario: 圖片提取保持不變
- **WHEN** 使用 opendataloader 引擎且指定 `--include-images`
- **THEN** 系統 SHALL 仍使用 pymupdf 提取圖片，產出 images manifest，與其他引擎行為一致。opendataloader 僅負責文字提取，不影響圖片流程。

### Requirement: opendataloader 可用性偵測
系統 SHALL 在使用前檢查 opendataloader-pdf 套件和 Java 執行環境是否可用。

#### Scenario: 套件已安裝且 Java 可用
- **WHEN** `opendataloader-pdf` 可 import 且 `java --version` 回傳 11+
- **THEN** opendataloader 引擎可用

#### Scenario: 套件未安裝
- **WHEN** `import opendataloader` 失敗
- **THEN** 系統 SHALL 記錄 warning log 並將 opendataloader 標記為不可用

#### Scenario: Java 版本不足
- **WHEN** Java 未安裝或版本低於 11
- **THEN** 系統 SHALL 記錄 warning log 並將 opendataloader 標記為不可用

### Requirement: 封裝為獨立模組
opendataloader 的所有互動邏輯 SHALL 封裝在 `scripts/_opendataloader_lib.py` 中，包含可用性偵測、PDF 轉換呼叫、頁碼標記後處理。

#### Scenario: 模組介面一致
- **WHEN** extract_pdf.py 呼叫 opendataloader 引擎
- **THEN** 透過 `_opendataloader_lib.py` 的公開函式進行，介面風格與 `_ocr_lib.py` 一致

### Requirement: style-decisions.json 支援新引擎值
`page_text_engine` 設定 SHALL 接受 `opendataloader` 作為有效值。

#### Scenario: per-document 覆寫
- **WHEN** style-decisions.json 中某文件設定 `"page_text_engine": "opendataloader"`
- **THEN** 該文件 SHALL 使用 opendataloader 引擎提取，即使 auto-detection 會選擇其他引擎

### Requirement: 可選依賴安裝
opendataloader-pdf SHALL 作為 pyproject.toml 的 optional dependency group 安裝。

#### Scenario: 安裝 opendataloader 支援
- **WHEN** 使用者執行 `uv pip install -e ".[opendataloader]"`
- **THEN** opendataloader-pdf 套件被安裝

#### Scenario: 基礎安裝不含 opendataloader
- **WHEN** 使用者執行 `uv pip install -e .`
- **THEN** opendataloader-pdf 不被安裝，系統正常運作使用其他引擎
