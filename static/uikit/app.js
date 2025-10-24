// Header Scroll Effect - Add glow when scrolling
    document.addEventListener('DOMContentLoaded', function() {
      const header = document.querySelector('.header');
      let scrollThreshold = 50; // Pixels to scroll before effect triggers

      // Add scroll event listener
      window.addEventListener('scroll', function() {
        if (window.scrollY > scrollThreshold) {
          header.classList.add('scrolled');
        } else {
          header.classList.remove('scrolled');
        }
      });

      // Theme Toggle Functionality
      const themeToggle = document.getElementById('theme-toggle');
      if (themeToggle) {
        themeToggle.addEventListener('click', function() {
          document.body.classList.toggle('dark-theme');
          
          // Save theme preference to localStorage
          const isDark = document.body.classList.contains('dark-theme');
          localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });

        // Load saved theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
          document.body.classList.add('dark-theme');
        }
      }
    });