window.onload = function() {
  const assignLinguistForm = document.getElementById('assign-linguist-form').children[0];
  const checkboxMain = document.getElementById('checkbox-main');
  const contextMenu = document.getElementById('context-menu');

  let filesList = [];

  checkboxMain.onclick = function() {
    [...document.getElementsByClassName('checkbox')].forEach((item, i) => {
      item.checked = checkboxMain.checked;
    });
  }

  document.oncontextmenu = function(e) {
    e.preventDefault();
    contextMenu.style.display = 'block';
    contextMenu.style.left = e.pageX + "px";
    contextMenu.style.top = e.pageY + "px";

    filesList = getSelectedFiles();
    if (filesList.length === 0)
    {
      filesList = getAllFiles();
    }
  }

  document.onclick = function(e) {
    contextMenu.style.display = 'none';

    if (e.target.id === 'kpp-upload-form' || e.target.id === 'assign-linguist-form')
    {
      e.target.classList.remove('show');
    }
  }

  document.getElementById('context-btn-analyze').onclick = function() {
    fileUuids = []
    filesList.forEach((item, i) => {
      fileUuids.push(item[0])
    });
    analyzeFiles(fileUuids.join(';'));
  }

  document.getElementById('context-btn-download-translation').onclick = function() {
    fileUuids = []
    filesList.forEach((item, i) => {
      fileUuids.push(item[0])
    });
    if (filesList.length > 1) {
      fileName = 'target.zip'
    }
    else {
      fileName = filesList[0][1]
    }
    downloadTranslations(fileUuids.join(';'), fileName)
  }

  document.getElementById('context-btn-export').onclick = function() {
    fileUuids = []
    filesList.forEach((item, i) => {
      fileUuids.push(item[0])
    });
    exportFiles(fileUuids.join(';'));
  }

  document.getElementById('context-btn-import').onclick = function() {
    document.getElementById('kpp-upload-form').className = "show";
  }

  document.getElementById('context-btn-assign-reviewer').onclick = function() {
    displayAssignLinguistForm(1);
  }

  document.getElementById('context-btn-assign-translator').onclick = function() {
    displayAssignLinguistForm();
  }

  function displayAssignLinguistForm(role=0) {
    document.getElementById('assign-linguist-form').className = "show";

    assignLinguistForm['role'].value = role;

    filesList = getSelectedFiles(true);
    if (filesList.length === 0)
    {
      filesList = getAllFiles(true);
    }
    assignLinguistForm['file_uuids'].value = filesList.join(';');

    assignLinguistForm['task'].value = 'assign_linguist';
  }

  function getSelectedFiles(iDOnly=false) {
    let list = [];
    [...document.getElementsByClassName('checkbox')].forEach((item, i) => {
      if (item.checked)
      {
        if (iDOnly)
        {
          list.push(item.parentElement.parentElement.id);
        }
        else
        {
          list.push([item.parentElement.parentElement.id, item.parentElement.parentElement.children[1].textContent]);
        }
      }
    });
    return list;
  }
  function getAllFiles(iDOnly=false) {
    let list = [];
    [...document.getElementsByClassName('file')].forEach((item, i) => {
      if (iDOnly)
      {
        list.push(item.id);
      }
      else
      {
        list.push([item.id, item.children[1].textContent]);
      }
    });

    return list;
  }
}
function analyzeFiles(fileUuids)
{
  fileFormData = new FormData();
  fileFormData.append('task', 'analyze');
  fileFormData.append('file_uuids', fileUuids);
  fetch('',
        {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCSRFToken()
          },
          body: fileFormData
        }
    )
    .then(response => response.json())
    .then(data => {
      checkReport(data['uuid']);
    })
    .catch(error => {
      console.error(error);
    })
}

function checkReport(reportUuid)
{
  var url = new URL(window.location.origin + '/report/' + reportUuid);
  var params = {task:'get_status'};
  url.search = new URLSearchParams(params).toString();

  fetch(url)
  .then(response => response.json())
  .then(data =>
    {
      if (data['status'] == 1 || data['status'] == 2)
      {
        setTimeout(checkReport, 5000, reportUuid);
      }
      else
      {
        document.getElementById('report-toast').className = 'show'
      }
    }
  )
}

function downloadTranslations(fileUuids, fileName)
{
  fileFormData = new FormData();
  fileFormData.append('task', 'download_translations');
  fileFormData.append('file_uuids', fileUuids);

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

function exportFiles(fileUuids) {
  fileFormData = new FormData();
  fileFormData.append('task', 'export');
  fileFormData.append('file_uuids', fileUuids);

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
      link.download = 'Project.kpp';
      link.click();
    })
    .catch(error => {
      console.error(error);
    })
}

function getCSRFToken() {
  let inputs = document.getElementsByTagName('input');
  return inputs[inputs.length-1].value;
}

function toggleExpand(span)
{
  if (span.textContent === 'expand_more')
  {
    span.textContent = 'expand_less';
    span.parentElement.parentElement.nextSibling.nextElementSibling.hidden = false;
  } else
  {
    span.textContent = 'expand_more';
    span.parentElement.parentElement.nextSibling.nextElementSibling.hidden = true;
  }
}
