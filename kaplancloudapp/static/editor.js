window.onload = function() {
  [...document.getElementsByTagName('td')].forEach((td, i) => {
    [...td.children].forEach((child, i) => {
      child.contentEditable = 'false';
      child.draggable = 'true';
    });
  });

  const tMHits = document.getElementById('tm-hits');
  const comments = document.getElementById('comments');
  const commentForm = document.getElementById('comment-form');
  const segmentContext = document.getElementById('context-segment');

  const targetCells = document.getElementsByClassName('target');

  let currentSegment;
  let concordanceSearchTimeout;
  let shiftSelectedSegments = [];

  for (i = 0; i < targetCells.length; i++) {
    targetCell = targetCells[i];

    targetCell.onfocus = function(e) {
      currentSegment = this.parentElement;
      commentForm.style.display = 'block';

      while (comments.children.length > 1) {
        comments.removeChild(comments.children[1]);
      }

      var url = new URL(window.location.href);

      var params = {task:'lookup',
                    tu_id:this.parentElement.parentElement.parentElement.id,
                    s_id:this.parentElement.id};
      url.search = new URLSearchParams(params).toString();

      fetch(url)
      .then(response => response.json())
      .then(data => {
        populateTMHits(data['tm']);

        comments_data = data['comments'];
        Object.keys(comments_data).forEach((key, i) => {
          commentSpan = document.createElement('span');
          commentSpan.className = 'comment';

          commentP = document.createElement('p');
          commentP.textContent = comments_data[key]['comment'];
          commentSpan.appendChild(commentP);

          commentDetailsSpan = document.createElement('span');
          commentDetailsSpan.className = 'details';
          userP = document.createElement('p');
          userP.className = 'detail';
          userP.textContent = comments_data[key]['created_by'];
          commentDetailsSpan.appendChild(userP);
          datetimeP = document.createElement('p');
          datetimeP.className = 'detail';
          datetimeP.textContent = new Date(comments_data[key]['created_at']).toLocaleString();
          commentDetailsSpan.appendChild(datetimeP);
          commentSpan.appendChild(commentDetailsSpan);

          comments.appendChild(commentSpan);
        });

      })
      .catch(error => {
        console.error('Could not look up segment #' + params['s_id'] + '.');
        console.error(error);
      })
    }

    targetCell.addEventListener('focusout', function() {
      submitSegment(this);
    })
  }

  let segmentFilter = new URL(window.location).searchParams.get('segments');
  if (segmentFilter && segmentFilter !== 'all')
  {
    filterSegments(segmentFilter);
  }

  document.getElementById('btn-submit-translation').onclick = function(e) {
    const overlaySubmitTranslation = document.getElementById('overlay-submit-translation');
    const untranslatedSegmentsTable = overlaySubmitTranslation.getElementsByTagName('table')[0];
    overlaySubmitTranslation.classList.add('visible');
    overlaySubmitTranslation.children[0].classList.add('visible');

    let untranslatedSegmentFound = false;

    let segmentRows = document.getElementsByClassName('segment');
    let segmentRow;
    for (let i = 0; i < segmentRows.length; i++)
    {
      segmentRow = segmentRows[i];

      if (!segmentRow.classList.contains('translated'))
      {
        untranslatedSegmentFound = true;

        let clonedSegmentRow = segmentRow.cloneNode(true);
        clonedSegmentRow.children[2].removeAttribute('contentEditable');
        clonedSegmentRow.children[2].removeAttribute('class');
        let newRow = untranslatedSegmentsTable.insertRow();
        newRow.innerHTML = clonedSegmentRow.innerHTML;
      }
    }
    overlaySubmitTranslation.children[0].classList.remove('visible');
    if (untranslatedSegmentFound)
    {
      overlaySubmitTranslation.children[2].classList.add('visible');
    }
    else
    {
      overlaySubmitTranslation.children[1].classList.add('visible');
    }
  }

  document.body.oncontextmenu = function(e) {
    if (e.target.classList.contains('sid'))
    {
      e.preventDefault();

      e.target.parentElement.classList.add('selected');

      segmentContext.classList.remove('hidden');
      segmentContext.style.left = e.pageX + "px";
      segmentContext.style.top = e.pageY + "px";
    }
  }

  document.body.oncopy = function(e) {
    let selectedText = window.getSelection().toString().replace(/<[^<>]*>/g, '');

    navigator.clipboard.writeText(selectedText);
  }

  document.body.onkeydown = function(e) {
    if (e.code === 'F3') {
      e.preventDefault();
      document.getElementById('concordance').value = window.getSelection().toString().replace(/<[^<>]*>/g, '');
      document.getElementById('concordance').oninput();
      return;
    }
    if (e.target.tagName.toLowerCase() !== 'td' || e.target.className !== 'target')
    {
      return;
    }
    [...e.target.getElementsByTagName('span')].forEach((item, i) => {
      item.remove();
    });
    [...e.target.getElementsByTagName('br')].forEach((item, i) => {
      item.remove();
    });
    if (e.ctrlKey || e.cmdKey) {
      if (e.code === 'Insert') {
        let sourceCell = e.target.parentElement.children[1];
        insertInnerHTML(sourceCell, e.target);
      } else if (e.code === 'Enter') {
        e.target.parentElement.classList.remove('blank', 'error', 'draft', 'reviewed');

        if (e.target.innerHTML !== '') {
          e.target.parentElement.classList.add('translated');
          e.target.parentElement.setAttribute('status', 'translated');
        } else {
          e.target.parentElement.classList.add('blank');
          e.target.parentElement.setAttribute('status', 'blank');
        }
        e.target.blur();

        if (!e.shiftKey)
        {
          targetList = [...document.getElementsByClassName('target')];
          let isNext = false;
          for (i = 0; i < targetList.length; i++)
          {
            nextTarget = targetList[i];

            if (nextTarget == e.target)
            {
              isNext = true;
              continue;
            }
            if (isNext && !nextTarget.parentElement.classList.contains('translated') && !nextTarget.parentElement.classList.contains('locked'))
            {
              nextTarget.focus();
              break;
            }
          }
        }

      }
    }
    else if (e.key !== 'Tab'
             && e.key !== 'Shift'
             && e.key !== 'Alt'
             && e.key.match('F[0-9]+') == null)
    {
      e.target.parentElement.classList.remove('blank', 'error', 'translated', 'reviewed');
      e.target.parentElement.classList.add('draft');
      e.target.parentElement.setAttribute('status', 'draft');
    }
  }

  document.getElementById('concordance').oninput = function(e) {
    let string = this.value;

    clearTimeout(concordanceSearchTimeout);

    if (this.value.length >= 3)
    {
      concordanceSearchTimeout = setTimeout(concordanceSearch, 250, string);
    }
  }

  document.body.onclick = function(e) {
    if (['ec', 'g', 'sc', 'ph', 'x'].includes(e.target.tagName.toLowerCase())
        && e.target.parentElement.tagName.toLowerCase() === 'td'
        && e.target.parentElement.className === 'source')
    {
      e.target.parentElement.nextElementSibling.innerHTML += e.target.outerHTML;
    }
    else if (e.target.tagName.toLowerCase() === 'button' && e.target.className === 'cancel')
    {
      closeOverlay();
    }
    else if (e.target.tagName.toLowerCase() === 'button' && e.target.className === 'advance-status')
    {
      advanceFileStatus();
    }
    else if (e.target.className === 'tm-hit')
    {
      currentSegment.children[2].innerHTML = e.target.children[1].innerHTML;
      currentSegment.children[2].parentElement.classList.remove('blank', 'error', 'translated', 'reviewed');
      currentSegment.children[2].parentElement.classList.add('draft');
    }
    else if (e.target.parentElement.className === 'tm-hit')
    {
      currentSegment.children[2].innerHTML = e.target.parentElement.children[1].innerHTML;
      currentSegment.children[2].parentElement.classList.remove('blank', 'error', 'translated', 'reviewed');
      currentSegment.children[2].parentElement.classList.add('draft');
    }
    else if (e.target.classList.contains('sid'))
    {
      if (e.shiftKey)
      {
        e.target.parentElement.classList.add('selected');
        shiftSelectedSegments.push(e.target.parentElement);

        if (shiftSelectedSegments.length === 2)
        {
          let applySelect = false;
          [...document.getElementsByClassName('segment')].forEach((segment, i) => {
            if (shiftSelectedSegments.includes(segment))
            {
              shiftSelectedSegments = shiftSelectedSegments.filter(function(item) {
                return item != segment;
              });
              if (shiftSelectedSegments.length == 1)
              {
                applySelect = true;
              }
              else
              {
                applySelect = false;
              }
            }
            if (applySelect)
            {
              segment.classList.add('selected');
            }
          });
        }
      }
      else
      {
        e.target.parentElement.classList.toggle('selected');
        shiftSelectedSegments = []
      }
    }
    else if (e.target.id === 'btn-context-lock')
    {
      changeSelectedSegmentLocks(true);
    }
    else if (e.target.id === 'btn-context-unlock')
    {
      changeSelectedSegmentLocks(false);
    }
    else if (e.target.id === 'btn-filter')
    {
      toggleFilterDropdown()
    }
    else if (e.target.id === 'btn-filter-all')
    {
      filterSegments('all');
      toggleFilterDropdown()
    }
    else if (e.target.id === 'btn-filter-translated')
    {
      filterSegments('translated');
      toggleFilterDropdown()
    }
    else if (e.target.id === 'btn-filter-draft')
    {
      filterSegments('draft');
      toggleFilterDropdown()
    }
    else if (e.target.id === 'btn-filter-blank')
    {
      filterSegments('blank');
      toggleFilterDropdown()
    }
    else
    {
      deselectSegments();
      segmentContext.classList.add('hidden');
    }
  }

  document.getElementById('comment-form').onsubmit = function(e) {
    e.preventDefault();

    commentFormData = new FormData();
    commentFormData.append('task', 'add_comment');
    commentFormData.append('comment', this['comment'].value);
    commentFormData.append('segment_id', currentSegment.id);

    fetch('',
          {
            method: 'POST',
            headers: {
              'X-CSRFToken': getCSRFToken()
            },
            body: commentFormData
          }
      )
      .then(response => response.json())
      .then(data => {
        commentSpan = document.createElement('span');
        commentSpan.className = 'comment';

        commentP = document.createElement('p');
        commentP.textContent = data['comment'];
        commentSpan.appendChild(commentP);

        commentDetailsSpan = document.createElement('span');
        commentDetailsSpan.className = 'details';
        userP = document.createElement('p');
        userP.className = 'detail';
        userP.textContent = data['created_by'];
        commentDetailsSpan.appendChild(userP);
        datetimeP = document.createElement('p');
        datetimeP.className = 'detail';
        datetimeP.textContent = new Date(data['created_at']).toLocaleString();
        commentDetailsSpan.appendChild(datetimeP);
        commentSpan.appendChild(commentDetailsSpan);

        comments.appendChild(commentSpan);
      })
      .catch(error => {
        console.error(error);
        console.error('Could not add comment.');
      })
  }

  function advanceFileStatus() {
    let taskFormData = new FormData();
    taskFormData.append('task', 'advance_file_status');

    fetch('',
          {
            method: 'POST',
            headers: {
              'X-CSRFToken': getCSRFToken()
            },
            body: taskFormData
          }
      )
      .then(response => {
        if (!response.ok)
        {
          throw response;
        }
        else
        {
          location.reload();
        }

      })
      .catch(error => {
        console.error(error);
      })

  }

  function changeSelectedSegmentLocks(lock) {
    let selectedSegments = [...document.getElementsByClassName('segment selected')]
    selectedSegments.forEach((selectedSegment, i) => {
      if (lock) {
        selectedSegment.children[2].removeAttribute('contentEditable');
        selectedSegment.classList.add('locked');
      }
      else {
        selectedSegment.children[2].setAttribute('contentEditable', true);
        selectedSegment.classList.remove('locked');
      }
    });

    let selectedSegmentIds = selectedSegments.map(item => item.children[0].textContent)
    if (selectedSegmentIds === []) {return;}

    let locksFormData = new FormData();
    locksFormData.append('task', 'change_segment_locks');
    if (lock) {
      lock = 'lock';
    }
    else {
      lock = 'unlock';
    }
    locksFormData.append('to_lock', lock);

    locksFormData.append('segments', selectedSegmentIds.join(';'))

    fetch('',
          {
            method: 'POST',
            headers: {
              'X-CSRFToken': getCSRFToken()
            },
            body: locksFormData
          }
      )
      .then(response => {
        if (response.status === 200)
        {
          response.json()
          .then(data => {
            console.log(data);
          })
        }
      }
      )
  }

  function closeOverlay() {
    const overlaySubmitTranslation = document.getElementById('overlay-submit-translation');

    overlaySubmitTranslation.classList.remove('visible');
    overlaySubmitTranslation.children[0].classList.remove('visible');
    overlaySubmitTranslation.children[1].classList.remove('visible');
    overlaySubmitTranslation.children[2].classList.remove('visible');
    overlaySubmitTranslation.children[2].getElementsByTagName('table')[0].innerHTML = null;
  }

  function concordanceSearch(string) {
    var url = new URL(window.location.href);

    var params = {task: 'concordance',
                  query: string};
    url.search = new URLSearchParams(params).toString();

    fetch(url)
    .then(response => response.json())
    .then(data => {
      populateTMHits(data['concordance'], false);
    })
  }

  function deselectSegments() {
    [...document.getElementsByClassName('segment selected')].forEach((item, i) => {
      item.classList.remove('selected');
    });
  }

  function filterSegments(segmentState) {
    const segments = document.body.getElementsByClassName('segment');

    for (i = 0; i < segments.length; i++)
    {
      if (segmentState === 'all')
      {
        segments[i].classList.remove('hidden');
      }
      else if (segments[i].classList.contains(segmentState))
      {
        segments[i].classList.remove('hidden');
      }
      else
      {
        segments[i].classList.add('hidden');
      }
    }


    window.history.pushState('file', 'segments', '?segments='+segmentState)
  }

  function getCSRFToken() {
    return document.getElementsByTagName('input')[0].value;
  }

  function insertInnerHTML(source, target) {
    target.innerHTML = source.innerHTML;
  }

  function populateTMHits(tm_data, display_diff=true) {
    while (tMHits.children.length > 1)
    {
      tMHits.removeChild(tMHits.children[1]);
    }

    tm_data.forEach((tm_hit, i) => {
      hitSpan = document.createElement('span');
      hitSpan.className = 'tm-hit'
      sourceP = document.createElement('p');
      sourceP.innerHTML = tm_hit[1]['source'];
      [...sourceP.children].forEach((child, i) => {
        child.contentEditable = 'false';
        child.draggable = 'true';
      });
      hitSpan.appendChild(sourceP);
      //hitSpan.appendChild(document.createElement('hr'));
      targetP = document.createElement('p');
      targetP.innerHTML = tm_hit[1]['target'];
      [...targetP.children].forEach((child, i) => {
        child.contentEditable = 'false';
        child.draggable = 'true';
      });
      hitSpan.appendChild(targetP);

      hitDetailsSpan = document.createElement('span');
      hitDetailsSpan.className = 'details';
      matchP = document.createElement('p');
      matchP.className = 'detail';
      if (display_diff) {
        matchP.textContent = new Intl.NumberFormat(undefined, {style:'percent'}).format(tm_hit[0]);
      }
      hitDetailsSpan.appendChild(matchP);
      userP = document.createElement('p');
      userP.className = 'detail';
      userP.textContent = tm_hit[1]['updated_by'];
      hitDetailsSpan.appendChild(userP);
      datetimeP = document.createElement('p');
      datetimeP.className = 'detail';
      datetimeP.textContent = new Date(tm_hit[1]['updated_at']).toLocaleString();
      hitDetailsSpan.appendChild(datetimeP);
      hitSpan.appendChild(hitDetailsSpan);

      tMHits.appendChild(hitSpan);
    });
  }

  function submitSegment(targetCell) {
    let status = targetCell.parentElement.getAttribute('status');

    targetCell.parentElement.classList.remove(('blank', 'draft', 'translated', 'error'));
    targetCell.parentElement.classList.add(status);

    segmentFormData = new FormData();
    segmentFormData.append('task', 'update_segment');
    segmentFormData.append('status', status);
    segmentFormData.append('tu_id', targetCell.parentElement.parentElement.parentElement.id);
    segmentFormData.append('s_id', targetCell.parentElement.id);
    segmentFormData.append('target', targetCell.innerHTML);

    fetch('',
          {
            method: 'POST',
            headers: {
              'X-CSRFToken': getCSRFToken()
            },
            body: segmentFormData
          }
      )
      .then(response => {
        if (!response.ok)
        {
          throw 'Could not update segment #' + targetCell.parentElement.id + '.';
        }
        targetCell.parentElement.classList.remove('error');
      })
      .catch(error => {
        console.error(error);
        targetCell.parentElement.classList.add('error');
        targetCell.parentElement.classList.remove('blank', 'draft', 'translated');
      })


  }

  function toggleFilterDropdown() {
    const filterButton = document.getElementById('btn-filter');
    const filterDropdown = document.getElementById('dropdown-filter');

    filterDropdown.style.top = filterButton.offsetHeight + 'px';
    filterDropdown.style.left = filterButton.offsetLeft + 'px';
    filterDropdown.classList.toggle('hidden');
  }

}
function toggleExpand(span)
{
  if (span.textContent === 'expand_more')
  {
    span.textContent = 'expand_less';
    span.parentElement.nextSibling.nextElementSibling.hidden = false;
  } else
  {
    span.textContent = 'expand_more';
    span.parentElement.nextSibling.nextElementSibling.hidden = true;
  }
}
