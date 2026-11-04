(function () {
  'use strict';
  var app = document.getElementById('app');
  app.innerHTML = '<main><p>APK2IPK / RECOVERED BROWSER APP</p>' +
    '<h1>This app had no HTML file.</h1><p>The converter generated its entry page from browser JavaScript.</p>' +
    '<button type="button">Press OK to count</button><output aria-live="polite">0</output></main>';
  var button = app.querySelector('button');
  var output = app.querySelector('output');
  var count = 0;
  button.onclick = function () { count += 1; output.textContent = String(count); };
  button.focus();
}());
