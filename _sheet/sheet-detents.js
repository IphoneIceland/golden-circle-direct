/* ============================================================================
   SHEET DETENTS — iOS 26 / iPadOS 26 / macOS 26 scroll-to-resize behaviour
   ---------------------------------------------------------------------------
   Apple's UISheetPresentationController resizes a sheet when its scroll view is
   scrolled at the edge. WWDC21-10063, on the default behaviour:

       "because the scroll view is scrolled to top, scrolling the scroll view
        will also expand the sheet"
       "PrefersScrollingExpandsWhenScrolledToEdge. By default, this property is
        true, so setting it to false prevents scrolling from expanding."

   We mirror that on BOTH edges, which is what Ritchie asked for:
       at the BOTTOM, keep pulling up   -> panel expands to the tall detent
       at the TOP,    keep pulling down -> panel collapses to the short detent

   ⚠️ Heights are set as INLINE !important, never CSS. Three other scripts in
   this app write inline !important (SUBFIX, VG-PHONE, the runtime style tags)
   and a stylesheet rule loses to all of them. Same reason the 56px monster-pin
   bug happened. Do not "tidy" this into the stylesheet.
   ========================================================================== */
(function () {
  'use strict';
  if (window.__sheetDetents) return;
  window.__sheetDetents = true;

  var PANELS = '#orientbar,#setbar,#sightsbar,#geobar,#hydrobar,#biobar,#landbar,' +
               '#zfbar,#platebar,#regionbar,#sagabar,#legpop,#tabbar,' +
               '.card-body,.vsheet-body';

  var PULL     = 34;    // px of over-pull past the edge before a detent changes
  var COOLDOWN = 420;   // ms — one gesture must not toggle twice
  var EDGE     = 2;     // px tolerance for "at the edge"
  var TALL     = '86vh';
  var EASE     = 'max-height .34s cubic-bezier(.32,.72,0,1)';

  var reduce = false;
  try { reduce = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}

  var state = new WeakMap();   // el -> {tall:bool, at:0, pull:0, lock:0}

  function st(el) {
    var s = state.get(el);
    if (!s) { s = { tall: false, at: 0, pull: 0, lock: 0 }; state.set(el, s); }
    return s;
  }

  // Only worth doing where the panel is actually height-constrained and scrolls.
  function eligible(el) {
    return el && el.scrollHeight - el.clientHeight > 24;
  }

  function setTall(el, tall) {
    var s = st(el);
    if (s.tall === tall) return false;
    s.tall = tall;
    s.lock = Date.now() + COOLDOWN;
    s.pull = 0;
    if (!reduce) el.style.setProperty('transition', EASE, 'important');
    if (tall) el.style.setProperty('max-height', TALL, 'important');
    else      el.style.removeProperty('max-height');
    el.classList.toggle('sheet-tall', tall);
    try {
      el.dispatchEvent(new CustomEvent('sheetdetent', {
        bubbles: true, detail: { tall: tall }
      }));
    } catch (e) {}
    return true;
  }

  // dy > 0 means the finger moved UP / content scrolls down = "toward the bottom"
  function nudge(el, dy) {
    var s = st(el);
    if (Date.now() < s.lock) return;
    if (!eligible(el)) return;

    var top    = el.scrollTop <= EDGE;
    var bottom = el.scrollTop + el.clientHeight >= el.scrollHeight - EDGE;

    if (bottom && dy > 0 && !s.tall) {
      s.pull += dy;
      if (s.pull >= PULL) setTall(el, true);
      return;
    }
    if (top && dy < 0 && s.tall) {
      s.pull += -dy;
      if (s.pull >= PULL) setTall(el, false);
      return;
    }
    s.pull = 0;   // moved off the edge — start the count again
  }

  function panelFrom(node) {
    return node && node.closest ? node.closest(PANELS) : null;
  }

  document.addEventListener('touchstart', function (e) {
    var el = panelFrom(e.target);
    if (!el) return;
    st(el).at = e.touches[0].clientY;
    st(el).pull = 0;
  }, { passive: true });

  document.addEventListener('touchmove', function (e) {
    var el = panelFrom(e.target);
    if (!el) return;
    var y = e.touches[0].clientY, s = st(el);
    nudge(el, s.at - y);          // finger up = positive
    s.at = y;
  }, { passive: true });

  // macOS 26 / iPadOS trackpad + wheel get the same behaviour.
  document.addEventListener('wheel', function (e) {
    var el = panelFrom(e.target);
    if (el) nudge(el, e.deltaY);
  }, { passive: true });

  // A panel that gets hidden goes back to its short detent, so it never
  // reopens already-expanded from a gesture the user has forgotten making.
  function reset(el) { if (st(el).tall) setTall(el, false); }
  try {
    var mo = new MutationObserver(function (recs) {
      for (var i = 0; i < recs.length; i++) {
        var el = recs[i].target;
        if (el.matches && el.matches(PANELS) && el.offsetParent === null) reset(el);
      }
    });
    mo.observe(document.body, {
      subtree: true, attributes: true, attributeFilter: ['style', 'class', 'hidden']
    });
  } catch (e) {}

  window.__sheetDetentPanels = PANELS;
})();
