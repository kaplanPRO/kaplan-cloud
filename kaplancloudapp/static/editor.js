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

  let currentSegment;

  const targetCells = document.getElementsByClassName('target');
  for (i = 0; i < targetCells.length; i++) {
    targetCell = targetCells[i];

    targetCell.onfocus = function(e) {
      currentSegment = this.parentNode;
      commentForm.style.display = 'block';

      while (comments.children.length > 1) {
        comments.removeChild(comments.children[1]);
      }

      var url = new URL(window.location.href);

      var params = {task:'lookup',
                    tu_id:this.parentNode.parentNode.parentNode.id,
                    s_id:this.parentNode.id};
      url.search = new URLSearchParams(params).toString();

      fetch(url)
      .then(response => response.json())
      .then(data => {
        tMHits.innerHTML = null;

        tm_data = data['tm'];

        tm_data.forEach((tm_hit, i) => {
          hitSpan = document.createElement('span');
          hitSpan.className = 'tm-hit'
          sourceP = document.createElement('p');
          sourceP.innerHTML = tm_hit[1]['source'];
          hitSpan.appendChild(sourceP);
          //hitSpan.appendChild(document.createElement('hr'));
          targetP = document.createElement('p');
          targetP.innerHTML = tm_hit[1]['target'];
          hitSpan.appendChild(targetP);

          hitDetailsSpan = document.createElement('span');
          hitDetailsSpan.className = 'details';
          matchP = document.createElement('p');
          matchP.className = 'detail';
          matchP.textContent = new Intl.NumberFormat(undefined, {style:'percent'}).format(tm_hit[0]);
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

        if (tMHits.innerHTML == '')
        {
          p = document.createElement('p');
          p.textContent = 'n/a';
          tMHits.appendChild(p);
        }

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

  document.body.onkeydown = function(e) {
    if (e.target.tagName.toLowerCase() !== 'td' || e.target.className !== 'target')
    {
      return;
    }
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
            if (isNext && !nextTarget.parentElement.classList.contains('translated'))
            {
              nextTarget.focus();
              break;
            }
          }
        }

      }
    }
    else {
      e.target.parentElement.classList.remove('blank', 'error', 'translated', 'reviewed');
      e.target.parentElement.classList.add('draft');
      e.target.parentElement.setAttribute('status', 'draft');
    }
  }

  document.body.onclick = function(e) {
    if (['ec', 'g', 'sc', 'ph', 'x'].includes(e.target.tagName.toLowerCase()) && e.target.parentElement.tagName.toLowerCase() === 'td' && e.target.parentElement.className === 'source') {
      e.target.parentElement.nextElementSibling.innerHTML += e.target.outerHTML;
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

  function getCSRFToken() {
    return document.getElementsByTagName('input')[0].value;
  }

  function insertInnerHTML(source, target) {
    target.innerHTML = source.innerHTML;
  }

  function submitSegment(targetCell) {
    let status = targetCell.parentNode.getAttribute('status');

    targetCell.parentNode.classList.remove(('blank', 'draft', 'translated', 'error'));
    targetCell.parentNode.classList.add(status);

    segmentFormData = new FormData();
    segmentFormData.append('task', 'update_segment');
    segmentFormData.append('status', status);
    segmentFormData.append('tu_id', targetCell.parentNode.parentNode.parentNode.id);
    segmentFormData.append('s_id', targetCell.parentNode.id);
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
          throw 'Could not update segment #' + targetCell.parentNode.id + '.';
        }
        targetCell.parentNode.classList.remove('error');
      })
      .catch(error => {
        console.error(error);
        targetCell.parentNode.classList.add('error');
        targetCell.parentNode.classList.remove('blank', 'draft', 'translated');
      })


  }

}
function toggleExpand(span)
{
  if (span.textContent === 'expand_more')
  {
    span.textContent = 'expand_less';
    span.parentNode.nextSibling.nextElementSibling.hidden = false;
  } else
  {
    span.textContent = 'expand_more';
    span.parentNode.nextSibling.nextElementSibling.hidden = true;
  }
}
