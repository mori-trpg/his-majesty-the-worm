## ADDED Requirements

### Requirement: auto-detection 優先使用 opendataloader
當 `page_text_engine` 為 `auto` 時，引擎選擇 SHALL 優先檢查 opendataloader 可用性。

#### Scenario: opendataloader 可用時優先
- **WHEN** page_text_engine 為 auto 且 opendataloader 可用
- **THEN** 系統 SHALL 使用 opendataloader 作為預設引擎

#### Scenario: opendataloader 不可用時降級
- **WHEN** page_text_engine 為 auto 且 opendataloader 不可用
- **THEN** 系統 SHALL 回退至現有 auto-detection 邏輯（pymupdf 品質探測 → markitdown → ocr）

### Requirement: 優雅降級與日誌
引擎降級時 SHALL 提供清晰的日誌訊息。

#### Scenario: 降級時記錄原因
- **WHEN** opendataloader 不可用導致降級
- **THEN** 系統 SHALL 輸出 INFO 級別日誌，說明降級原因（套件未安裝 / Java 不可用）及實際使用的引擎

#### Scenario: 明確指定不可用引擎時報錯
- **WHEN** 使用者明確指定 `--page-text-engine opendataloader` 但 opendataloader 不可用
- **THEN** 系統 SHALL 輸出 ERROR 並終止，不自動降級（明確指定表示用戶期望使用該引擎）

### Requirement: 圖片提取流程不受引擎選擇影響
無論選擇哪個文字提取引擎，圖片提取和嵌入邏輯 SHALL 保持獨立運作。

#### Scenario: opendataloader 引擎下圖片提取正常
- **WHEN** 使用 opendataloader 引擎且啟用圖片提取
- **THEN** 圖片提取 SHALL 透過 pymupdf 獨立執行，manifest 格式與內容不變

#### Scenario: 圖片嵌入位置資訊保留
- **WHEN** 使用 opendataloader 引擎提取文字
- **THEN** 頁碼標記（`<!-- PAGE N -->`）SHALL 正確對應原始 PDF 頁碼，確保 chapter-split 流程中圖片按 manifest 的 page 欄位正確嵌入
