function download(label) {
    document.getElementById('button').disabled = true;
    document.getElementById('button').value = '&#x2705; ' + label;
    document.getElementById('form').submit();
    //this.parent.submit();
}
