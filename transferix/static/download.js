function download(btn) {
    btn.disabled = true;
    btn.value = btn.dataset.done;
    btn.form.submit();
}
