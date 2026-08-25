/* TransHimalaya — site behaviour
   Norzin Consultancy, 2026

   The bell (drilbu) replaces the pointer on fine-pointer devices and swings
   from its handle over anything clickable. Touch devices keep the native
   cursor, and the effect is skipped entirely for reduced-motion users who
   would not see the swing anyway. */
(function () {
  var root = document.querySelector('.th-site');
  if (!root) return;
  if (!window.matchMedia || !window.matchMedia('(pointer:fine)').matches) return;

  root.classList.add('cursor-on');

  var cur = document.createElement('div');
  cur.className = 'th-cursor';
  cur.innerHTML = '<div class="bell"></div>';
  cur.style.opacity = '0'; /* hidden until the pointer first moves */
  root.appendChild(cur);

  /* Hotspot sits at the bell's handle — the same point the swing pivots
     around — derived from the rendered size so it tracks the CSS. */
  var box = cur.getBoundingClientRect();
  var hx = box.width * 0.5, hy = box.height * 0.10;

  window.addEventListener('mousemove', function (e) {
    cur.style.transform = 'translate(' + (e.clientX - hx) + 'px,' + (e.clientY - hy) + 'px)';
    cur.style.opacity = '1';
  }, { passive: true });

  var CLICKABLE = 'a, button, input, label, .th-card, .th-field .item';
  document.addEventListener('mouseover', function (e) {
    if (e.target.closest && e.target.closest(CLICKABLE)) cur.classList.add('is-hover');
  });
  document.addEventListener('mouseout', function (e) {
    var to = e.relatedTarget;
    if (e.target.closest && e.target.closest(CLICKABLE) &&
        !(to && to.closest && to.closest(CLICKABLE))) cur.classList.remove('is-hover');
  });
  document.addEventListener('mouseleave', function () { cur.style.opacity = '0'; });
  document.addEventListener('mouseenter', function () { cur.style.opacity = '1'; });
})();

/* Hamburger — collapses the navigation on small screens. */
(function () {
  var burger = document.querySelector('.th-burger');
  var nav = document.getElementById('th-nav');
  if (!burger || !nav) return;

  function setOpen(open) {
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    nav.classList.toggle('is-open', open);
    if (!open) nav.querySelectorAll('.th-item.is-open')
      .forEach(function (i) { i.classList.remove('is-open'); });
  }

  burger.addEventListener('click', function () {
    setOpen(burger.getAttribute('aria-expanded') !== 'true');
  });

  /* Close on Escape, and whenever a link is chosen. */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setOpen(false);
  });
  /* On small screens a parent item opens its submenu instead of navigating.
     Its own page stays reachable through an "All …" entry added to the top. */
  var MOBILE = '(max-width:820px)';
  nav.querySelectorAll('.th-item.has-sub').forEach(function (item) {
    var link = item.firstElementChild;
    var sub = item.querySelector('.th-sub');
    if (!link || !sub) return;

    var href = link.getAttribute('href');
    if (href && href !== '#' && !sub.querySelector('a[href="' + href + '"]')) {
      var all = document.createElement('a');
      all.href = href;
      all.textContent = 'All ' + link.textContent.replace('▾', '').trim();
      sub.insertBefore(all, sub.firstChild);
    }

    link.addEventListener('click', function (e) {
      if (!window.matchMedia(MOBILE).matches) return;
      e.preventDefault();
      var open = item.classList.toggle('is-open');
      link.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });

  nav.addEventListener('click', function (e) {
    var a = e.target.closest('a');
    if (!a) return;
    var item = a.parentElement;
    /* a parent toggle is not navigation, so leave the menu open */
    if (item && item.classList.contains('th-item') && window.matchMedia(MOBILE).matches) return;
    setOpen(false);
  });

  /* Reset when the layout returns to the desktop arrangement. */
  window.matchMedia('(min-width:821px)').addEventListener('change', function (e) {
    if (e.matches) setOpen(false);
  });
})();

/* Share — Facebook and email use their share URLs; copy writes to the clipboard.
   Instagram has no web share endpoint, so it uses the device share sheet where
   one exists and falls back to copying the link. */
(function () {
  var group = document.querySelector('[data-share]');
  if (!group) return;

  function url()   { return location.href; }
  function title() { return document.title.split(' — ')[0]; }

  function copy(btn) {
    var done = function () {
      btn.classList.add('is-done');
      setTimeout(function () { btn.classList.remove('is-done'); }, 1600);
    };
    if (navigator.clipboard) { navigator.clipboard.writeText(url()).then(done, done); return; }
    var f = document.createElement('input');
    f.value = url(); document.body.appendChild(f); f.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(f); done();
  }

  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-share]');
    if (!el) return;
    var kind = el.getAttribute('data-share');
    if (kind === 'copy') { e.preventDefault(); copy(el); return; }
    e.preventDefault();
    if (kind === 'facebook') {
      window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url()),
        'share', 'width=600,height=520');
    } else if (kind === 'email') {
      location.href = 'mailto:?subject=' + encodeURIComponent(title()) +
        '&body=' + encodeURIComponent(url());
    } else if (kind === 'instagram') {
      if (navigator.share) navigator.share({ title: title(), url: url() }).catch(function () {});
      else copy(el.closest('.art-share').querySelector('.sh-cp') || el);
    }
  });
})();

/* In Focus — filter the cards by topic and by a free-text search.
   Everything is already in the page; this only shows and hides. */
(function () {
  var bar = document.querySelector('[data-catfilter]');
  var grid = document.querySelector('.cat-grid');
  if (!bar || !grid) return;

  var cards = Array.prototype.slice.call(grid.querySelectorAll('.th-card'));
  var buttons = Array.prototype.slice.call(bar.querySelectorAll('.cf-btn'));
  var input = bar.querySelector('input[type="search"]');
  var count = bar.querySelector('.cf-count');
  var topic = 'all';

  var empty = document.createElement('p');
  empty.className = 'cat-noresult';
  empty.hidden = true;
  empty.textContent = 'No articles match that search yet.';
  grid.parentNode.insertBefore(empty, grid.nextSibling);

  function apply() {
    var q = (input.value || '').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (c) {
      var okTopic = topic === 'all' || c.getAttribute('data-topic') === topic;
      var okText = !q || (c.getAttribute('data-search') || '').indexOf(q) !== -1;
      var on = okTopic && okText;
      c.classList.toggle('is-hidden', !on);
      if (on) shown++;
    });
    empty.hidden = shown !== 0;
    if (count) {
      count.textContent = (topic === 'all' && !q) ? '' :
        shown + (shown === 1 ? ' article' : ' articles');
    }
  }

  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      topic = b.getAttribute('data-filter');
      buttons.forEach(function (o) { o.classList.toggle('is-on', o === b); });
      apply();
    });
  });
  input.addEventListener('input', apply);
})();
