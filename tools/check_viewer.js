// Minimal DOM integration check for generated viewer logic; not a TV/browser test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.children = []; this.value = ''; this.textContent = ''; this.disabled = false; }
  appendChild(child) { this.children.push(child); return child; }
  removeChild(child) { this.children.splice(this.children.indexOf(child), 1); }
  get firstChild() { return this.children[0] || null; }
  setAttribute(key, value) { this[key] = value; }
  focus() { document.activeElement = this; }
}
const ids = {};
for (const name of ['files', 'preview', 'search', 'filter', 'previous', 'next', 'title', 'count']) {
  ids[name] = new Element(name === 'search' ? 'input' : name === 'filter' ? 'select' : ['previous', 'next'].includes(name) ? 'button' : 'section');
}
ids.filter.value = 'all';
let keydown;
const document = {
  activeElement: null,
  getElementById: id => { assert.ok(ids[id], 'unknown required element'); return ids[id]; },
  createElement: tag => new Element(tag),
  addEventListener: (name, callback) => { if (name === 'keydown') keydown = callback; },
  querySelectorAll: () => [ids.search, ids.filter, ids.previous, ids.next, ...ids.files.children.filter(x => x.tagName === 'BUTTON')].filter(x => !x.disabled)
};
const context = {document};
vm.runInNewContext(fs.readFileSync(process.argv[2], 'utf8'), context, {timeout: 3000});
assert.ok(ids.count.textContent.includes('files'));
assert.ok(ids.files.children.length <= 20);
assert.equal(document.activeElement, ids.search);
keydown({keyCode: 40, preventDefault() {}});
assert.equal(document.activeElement, ids.filter, 'D-pad must leave search input');
ids.search.value = 'nonexistent-file-329478234'; ids.search.oninput();
assert.ok(ids.count.textContent.startsWith('0 files'));
ids.search.value = ''; ids.search.oninput();
if (context.APK_CONTENT.items.some(x => x.kind === 'image')) {
  ids.filter.value = 'image'; ids.filter.onchange();
  assert.ok(ids.files.children.every(x => x.tagName === 'BUTTON'));
  ids.files.children[0].onclick();
  assert.ok(ids.preview.children.some(x => x.tagName === 'IMG' && x.src.startsWith('apk-content/')));
}
ids.filter.value = 'all'; ids.filter.onchange();
if (!ids.next.disabled) {
  ids.next.onclick();
  assert.ok(ids.count.textContent.includes('Page 2'));
  ids.previous.onclick();
  assert.ok(ids.count.textContent.includes('Page 1'));
}
console.log('PASS: viewer script initialized, searched, filtered, previewed available images, paginated, and handled D-pad focus in a minimal DOM.');
