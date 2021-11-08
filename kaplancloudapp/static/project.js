function downloadTranslation(button, fileId, fileName)
{
  fileFormData = new FormData();
  fileFormData.append('task', 'download_translation');
  fileFormData.append('file_id', fileId);

  fetch('',
        {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCSRFToken()
          },
          body: fileFormData
        }
    )
    .then(response => response.blob())
    .then(blob => {
      let file = window.URL.createObjectURL(blob);
      let link = document.createElement('a');
      link.href = file;
      link.download = fileName;
      link.click();
    })
    .catch(error => {
      console.error(error);
    })
}

function getCSRFToken() {
  return document.getElementsByTagName('input')[0].value;
}

function toggleExpand(span)
{
  if (span.textContent === 'expand_more')
  {
    span.textContent = 'expand_less';
    span.parentNode.parentNode.nextSibling.nextElementSibling.hidden = false;
  } else
  {
    span.textContent = 'expand_more';
    span.parentNode.parentNode.nextSibling.nextElementSibling.hidden = true;
  }
}
