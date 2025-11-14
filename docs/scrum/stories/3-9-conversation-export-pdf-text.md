# Story 3.9: Conversation Export (PDF/Text)

Status: drafted

## Story

As a team leader,
I want to export conversations as PDF or text files,
so that I can include coaching guidance in meeting notes or share offline.

## Acceptance Criteria

1. **Export Options:**
   - Given I am viewing a conversation
   - When I click "Export" from the three-dot menu
   - Then I see export format options: PDF (formatted, with citations), Text (plain text, markdown)

2. **Export as PDF:**
   - Given I select "Export as PDF"
   - When the export generates
   - Then a PDF file is created with: conversation title, date/timestamp, all messages (user and assistant), citations formatted and preserved, Solution Tree branding/footer
   - And the PDF downloads to my device

3. **Export as Text:**
   - Given I select "Export as Text"
   - When the export generates
   - Then a .txt or .md file is created with: markdown formatting, message timestamps, citations preserved
   - And the file downloads to my device

## Tasks / Subtasks

- [ ] Create export endpoint (AC: #2, #3)
  - [ ] GET /api/conversations/{id}/export?format=pdf|text
  - [ ] Return PDF or text file as download
  - [ ] Set appropriate content-type headers

- [ ] Implement PDF generation (AC: #2)
  - [ ] Use library: WeasyPrint (Python) or pdfkit
  - [ ] Template with header (title, date)
  - [ ] Message formatting (user/assistant styling)
  - [ ] Citations section at bottom
  - [ ] Footer with Solution Tree branding

- [ ] Implement text export (AC: #3)
  - [ ] Markdown format with headers
  - [ ] Timestamps for each message
  - [ ] Citations in markdown format
  - [ ] Return as .md file

- [ ] Add Export to three-dot menu (AC: #1)
  - [ ] "Export" option
  - [ ] Sub-menu or modal with format options
  - [ ] Trigger download

- [ ] Testing and validation (AC: all)
  - [ ] Unit test: PDF generation creates valid PDF
  - [ ] Unit test: Text export creates markdown
  - [ ] Integration test: Download triggers correctly
  - [ ] Manual test: PDF formatting and branding

## Dev Notes

### PDF Generation Libraries
- Python: WeasyPrint, ReportLab, pdfkit
- Consider wkhtmltopdf for HTML to PDF conversion
- Template with Jinja2 for consistent formatting

### File Naming
- Format: `conversation_{title}_{date}.pdf`
- Sanitize title for filename safety

[Source: docs/epics/epic-3-conversations-history.md#Story-3.9]

## Dev Agent Record

### Context Reference

<!-- Will be filled by story-context workflow -->

### File List

<!-- Will be filled during implementation -->
