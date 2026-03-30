/* ── BARRE DE PROGRESSION NAVIGATION ── */
const navProgress = document.getElementById('navProgress');

document.querySelectorAll('a[href]').forEach(link => {
  // Seulement les liens internes, pas les ancres ni liens externes
  const href = link.getAttribute('href');
  if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto') || href.startsWith('tel') || href.startsWith('https://wa')) return;
  link.addEventListener('click', () => {
    if (navProgress) {
      navProgress.classList.add('loading');
    }
  });
});

window.addEventListener('pageshow', () => {
  if (navProgress) {
    navProgress.classList.remove('loading');
    navProgress.classList.add('done');
    setTimeout(() => navProgress.classList.remove('done'), 700);
  }
});

/* ── NAVBAR SCROLL ── */
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });
}

/* ── MOBILE MENU ── */
const navToggle = document.getElementById('navToggle');
const navLinks  = document.getElementById('navLinks');
if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    const spans = navToggle.querySelectorAll('span');
    spans[0].style.transform = open ? 'rotate(45deg) translate(4px,4px)' : '';
    spans[1].style.opacity   = open ? '0' : '';
    spans[2].style.transform = open ? 'rotate(-45deg) translate(4px,-4px)' : '';
  });
  document.addEventListener('click', (e) => {
    if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
      navLinks.classList.remove('open');
    }
  });
}

/* ── SCROLL REVEAL ── */
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => entry.target.classList.add('visible'), i * 60);
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });

document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

/* ── AUTO DISMISS FLASH ── */
document.querySelectorAll('.flash').forEach(f => {
  setTimeout(() => {
    f.style.transition = 'opacity 0.4s';
    f.style.opacity = '0';
    setTimeout(() => f.remove(), 400);
  }, 5000);
});
