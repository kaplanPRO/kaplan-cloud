window.onload = function() {
  const sourceLanguage = document.forms[0]['source_language'];
  const targetLanguage = document.forms[0]['target_language'];
  const translationMemories = document.forms[0]['translation_memories'];

  sourceLanguage.addEventListener('change', fetchTM);
  targetLanguage.addEventListener('change', fetchTM);

  function fetchTM() {
    if (sourceLanguage.value != '' && targetLanguage.value != '')
    {
      translationMemories.innerHTML = '';
      translationMemories.appendChild(new Option('-----'))

      var url = new URL(new URL(window.location.href).origin + document.forms[0]['tm_link'].value);

      var params = {'source':sourceLanguage.value,
                    'target':targetLanguage.value,
                    'format':'JSON'};
      url.search = new URLSearchParams(params).toString();

      fetch(url)
      .then(response => response.json())
      .then(data => {
        Object.keys(data).forEach((key, i) => {
          translationMemories.appendChild(new Option(data[key], key))
        });

      })

    }
  }
}
