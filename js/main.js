// Hero background slideshow
const slides = document.querySelectorAll('.hero__slide');
if (slides.length > 1) {
  let current = 0;
  setInterval(() => {
    slides[current].classList.remove('active');
    current = (current + 1) % slides.length;
    slides[current].classList.add('active');
  }, 5000);
}

// Nav: position below banner at top, stick to top once banner scrolls away
const nav = document.getElementById('nav');
const banner = document.querySelector('.edition-banner');
if (nav) {
  const updateNav = () => {
    const bannerHeight = banner ? banner.offsetHeight : 0;
    const pastBanner = window.scrollY >= bannerHeight;
    nav.classList.toggle('scrolled', pastBanner);
    nav.style.top = pastBanner ? '0' : bannerHeight + 'px';
    // Keep mobile menu top in sync with nav bottom
    // (nav.offsetTop is always 0 for fixed elements, so calculate manually)
    const navLinks = document.getElementById('navLinks');
    if (navLinks) {
      navLinks.style.top = (pastBanner ? 0 : bannerHeight) + nav.offsetHeight + 'px';
    }
  };
  window.addEventListener('scroll', updateNav, { passive: true });
  updateNav();
}

// Mobile menu toggle
const navToggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');

// On mobile, hoist navLinks to <body> to escape the nav's fixed stacking context.
// On desktop, keep it inside nav for the flexbox layout.
if (navLinks && navToggle) {
  const mq = window.matchMedia('(max-width: 768px)');
  const syncNavLinksParent = (e) => {
    if (e.matches && navLinks.parentElement !== document.body) {
      document.body.appendChild(navLinks);
    } else if (!e.matches && navLinks.parentElement === document.body) {
      nav.insertBefore(navLinks, navToggle);
    }
  };
  mq.addEventListener('change', syncNavLinksParent);
  syncNavLinksParent(mq);
}

if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('open');
    navToggle.classList.toggle('open', isOpen);
    nav.classList.toggle('menu-open', isOpen);
    navToggle.setAttribute('aria-expanded', isOpen);
    navToggle.setAttribute('aria-label', isOpen ? 'Menu sluiten' : 'Menu openen');
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });

  const closeMenu = () => {
    navLinks.classList.remove('open');
    navToggle.classList.remove('open');
    nav.classList.remove('menu-open');
    navToggle.setAttribute('aria-expanded', false);
    document.body.style.overflow = '';
  };

  // Close on link click
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', closeMenu);
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!nav.contains(e.target) && !navLinks.contains(e.target) && navLinks.classList.contains('open')) {
      closeMenu();
    }
  });
}

// Contact form (Web3Forms)
const contactForm = document.getElementById('contactForm');
if (contactForm) {
  const status = document.getElementById('contactFormStatus');
  const submitBtn = contactForm.querySelector('button[type="submit"]');

  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    submitBtn.disabled = true;
    status.removeAttribute('data-state');
    status.textContent = 'Bezig met versturen...';

    try {
      const response = await fetch(contactForm.action, {
        method: 'POST',
        headers: { 'Accept': 'application/json' },
        body: new FormData(contactForm)
      });
      const result = await response.json();

      if (result.success) {
        status.setAttribute('data-state', 'success');
        status.textContent = 'Bedankt! Je bericht is verstuurd.';
        contactForm.reset();
      } else {
        throw new Error(result.message || 'Versturen mislukt');
      }
    } catch (err) {
      status.setAttribute('data-state', 'error');
      status.textContent = 'Er ging iets mis. Probeer het later opnieuw of mail naar info.nerorock@gmail.com.';
    } finally {
      submitBtn.disabled = false;
    }
  });
}
