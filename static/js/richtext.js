document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".richtext-widget").forEach(widget => {
    const textarea = widget.querySelector(".richtext-input");
    const preview = widget.querySelector(".richtext-preview");

    // Insert buttons
    widget.querySelectorAll(".insert-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        let insertText = btn.dataset.insert;
        const cursorPlaceholder = "|";

        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        const selectedText = text.slice(start, end);

        if (selectedText.length > 0 && insertText.includes(cursorPlaceholder)) {
          // Split the insert string into "before" and "after"
          const [before, after] = insertText.split(cursorPlaceholder);

          // Wrap the selection
          const newText = text.slice(0, start) + before + selectedText + after + text.slice(end);
          textarea.value = newText;

          // Keep the selection wrapped
          const newStart = start + before.length;
          const newEnd = newStart + selectedText.length;
          textarea.focus();
          textarea.setSelectionRange(newStart, newEnd);

        } else if (insertText.includes(cursorPlaceholder)) {
          // No selection, just insert with cursor placeholder
          const placeholderIndex = insertText.indexOf(cursorPlaceholder);
          const cleanInsert = insertText.replace(cursorPlaceholder, "");

          const newText = text.slice(0, start) + cleanInsert + text.slice(end);
          textarea.value = newText;

          const cursorPos = start + placeholderIndex;
          textarea.focus();
          textarea.setSelectionRange(cursorPos, cursorPos);

        } else {
          // Fallback: insert raw
          const newText = text.slice(0, start) + insertText + text.slice(end);
          textarea.value = newText;

          const cursorPos = start + insertText.length;
          textarea.focus();
          textarea.setSelectionRange(cursorPos, cursorPos);
        }

        updatePreview();
      });



    });

    // Update preview
    function updatePreview() {
      const url = widget.dataset.previewUrl;
      fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
        },
        body: JSON.stringify({ text: textarea.value })
      })
      .then(res => res.text())
      .then(html => {
            preview.innerHTML = html;
            if (window.MathJax) {
                MathJax.typesetPromise([preview]);
            }
        });

    }

    textarea.addEventListener("input", updatePreview);
    updatePreview();  // initial
  });
});
