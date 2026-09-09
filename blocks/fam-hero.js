  // Family reel: same player as the visitors page (pitch overlay = paused
  // state, corner controls), with the overlay fading out at frame 28 and
  // back in at frame 325 (29.97 fps: 0.934s / 10.844s).
  (function(){
    var hero = document.querySelector('.fam-hero');
    var v = document.getElementById('famVideo');
    var overlay = document.getElementById('famOverlay');
    var watch = document.getElementById('watchBtn');
    var ht = document.getElementById('heroToggle');
    var hs = document.getElementById('heroSound');
    if (!hero || !v || !overlay) return;

    var FPS = 30000 / 1001;
    var OUT = 28 / FPS, IN = 325 / FPS;

    var syncPlay = function(){
      var paused = v.paused;
      hero.classList.toggle('is-playing', !paused);
      ht.innerHTML = paused ? '&#9654;' : '&#10073;&#10073;';
      var label = (paused ? 'Play' : 'Pause') + ' video';
      ht.setAttribute('aria-label', label);
      ht.setAttribute('title', label);
    };
    var syncSound = function(){
      hs.innerHTML = v.muted ? '&#128263;' : '&#128266;';
      var label = (v.muted ? 'Unmute' : 'Mute') + ' video';
      hs.setAttribute('aria-label', label);
      hs.setAttribute('title', label);
    };

    watch.addEventListener('click', function(){ v.play(); });
    // The whole overlay starts the reel, but links and buttons keep their jobs
    overlay.addEventListener('click', function(e){
      if (e.target.closest('a,button')) return;
      v.play();
    });
    ht.addEventListener('click', function(){
      if (v.paused) { v.play(); } else { v.pause(); }
    });
    hs.addEventListener('click', function(){
      v.muted = !v.muted;
      syncSound();
    });

    // When the reel finishes, bring the pitch back with its full cascade
    v.addEventListener('ended', function(){
      var items = overlay.querySelectorAll('.reveal');
      items.forEach(function(el){ el.classList.remove('in'); });
      void overlay.offsetWidth;
      items.forEach(function(el){ el.classList.add('in'); });
    });

    v.addEventListener('play', syncPlay);
    v.addEventListener('pause', syncPlay);
    v.addEventListener('ended', syncPlay);
    v.addEventListener('volumechange', syncSound);
    syncPlay(); syncSound();

    // Frame-timed overlay: hidden between frames 28 and 325 while playing
    var tick = function(){
      var t = v.currentTime;
      hero.classList.toggle('is-watching', !v.paused && t > OUT && t < IN);
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  })();
