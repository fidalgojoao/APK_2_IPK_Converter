(function () {
  'use strict';
  var buttons = document.querySelectorAll('button');
  var result = document.getElementById('result');
  var selected = 0;
  function back() {
    if (window.webOS && typeof window.webOS.platformBack === 'function') {
      window.webOS.platformBack();
    } else {
      result.textContent = 'Back received. TV exit behavior requires device validation.';
    }
  }
  document.getElementById('count').onclick = function () {
    try {
      var count = (parseInt(localStorage.getItem('apk2ipk-count'), 10) || 0) + 1;
      localStorage.setItem('apk2ipk-count', String(count));
      result.textContent = 'Stored button presses: ' + count;
    } catch (e) { result.textContent = 'Storage unavailable: ' + e.message; }
  };
  document.getElementById('reset').onclick = function () {
    try { localStorage.removeItem('apk2ipk-count'); result.textContent = 'Storage cleared.'; }
    catch (e) { result.textContent = 'Storage unavailable: ' + e.message; }
  };
  document.getElementById('back').onclick = back;
  document.addEventListener('keydown', function (event) {
    document.getElementById('keys').textContent = 'Last key code: ' + event.keyCode;
    if (event.keyCode === 37 || event.keyCode === 39) {
      var active = Array.prototype.indexOf.call(buttons, document.activeElement);
      selected = (Math.max(0, active) + (event.keyCode === 39 ? 1 : -1) + buttons.length) % buttons.length;
      buttons[selected].focus();
      event.preventDefault();
    } else if (event.keyCode === 461) { back(); event.preventDefault(); }
  });
  buttons[0].focus();
}());
