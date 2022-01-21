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
        Object.keys(tm_data).forEach((key, i) => {
          hitSpan = document.createElement('span');
          hitSpan.className = 'tm-hit'
          sourceP = document.createElement('p');
          sourceP.innerHTML = tm_data[key]['source'];
          hitSpan.appendChild(sourceP);
          //hitSpan.appendChild(document.createElement('hr'));
          targetP = document.createElement('p');
          targetP.innerHTML = tm_data[key]['target'];
          hitSpan.appendChild(targetP);

          hitDetailsSpan = document.createElement('span');
          hitDetailsSpan.className = 'details';
          userP = document.createElement('p');
          userP.className = 'detail';
          userP.textContent = tm_data[key]['updated_by'];
          hitDetailsSpan.appendChild(userP);
          datetimeP = document.createElement('p');
          datetimeP.className = 'detail';
          datetimeP.textContent = new Date(tm_data[key]['updated_at']).toLocaleString();
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

    targetCell.onkeydown = function(e) {
      if (e.ctrlKey || e.cmdKey) {
        if (e.code === 'Insert') {
          let sourceCell = this.parentNode.children[1];
          insertInnerHTML(sourceCell, this);
        } else if (e.code === 'Enter') {
          this.parentNode.classList.remove('blank', 'error', 'draft', 'reviewed');

          if (this.innerHTML !== '') {
            this.parentNode.classList.add('translated');
            this.parentNode.setAttribute('status', 'translated');
          } else {
            this.parentNode.classList.add('blank');
            this.parentNode.setAttribute('status', 'blank');
          }

          if (!e.shiftKey)
          {
            targetList = [...document.getElementsByClassName('target')];
            let isNext = false;
            for (i = 0; i < targetList.length; i++)
            {
              nextTarget = targetList[i];

              if (nextTarget == this)
              {
                isNext = true;
                continue;
              }
              if (isNext && !nextTarget.parentNode.classList.contains('translated'))
              {
                nextTarget.focus();
                break;
              }
            }
          }

        }
      }
      else {
        this.parentNode.classList.remove('blank', 'error', 'translated', 'reviewed');
        this.parentNode.classList.add('draft');
        this.parentNode.setAttribute('status', 'draft');
      }
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
