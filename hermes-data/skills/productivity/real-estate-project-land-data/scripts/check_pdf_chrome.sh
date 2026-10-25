#!/usr/bin/env bash
# check_pdf_chrome.sh — verify no chromium chrome (file:// footer + date header) in rendered PDFs
# Usage: bash check_pdf_chrome.sh <file1.pdf> [file2.pdf ...]
# Exit 0 if ALL files pass. Exit 1 with filenames if any fail.
# Also checks that `pdfinfo` reports an expected page count (optional).

FAIL=0

for PDF in "$@"; do
    if [ ! -f "$PDF" ]; then
        echo "MISSING: $PDF"
        FAIL=1
        continue
    fi

    FOOTER_HITS=$(pdftotext -layout "$PDF" - 2>/dev/null | grep -c 'file:/tmp\|file:///')
    HEADER_HITS=$(pdftotext -layout -f 1 -l 1 "$PDF" - 2>/dev/null | grep -cP '^\d{1,2}/\d{1,2}/\d{2,4}')

    if [ "$FOOTER_HITS" -gt 0 ] || [ "$HEADER_HITS" -gt 0 ]; then
        echo "FAIL: $PDF  (footer=$FOOTER_HITS  header=$HEADER_HITS)"
        FAIL=1
    else
        PAGES=$(pdfinfo "$PDF" 2>/dev/null | grep Pages | awk '{print $2}')
        echo "OK: $PDF  (${PAGES}p, clean)"
    fi
done

exit $FAIL