// CSRF token helpers (must be global)
function getCSRFToken() {
  return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function getHeaders() {
  return {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken()
  };
}

// Username/session/leaderboard logic
window.addEventListener('DOMContentLoaded', () => {
  const usernameSection = document.getElementById('usernameSection');
  const usernameInput = document.getElementById('usernameInput');
  const startBtn = document.getElementById('startBtn');
  const usernameError = document.getElementById('usernameError');
  const gameSection = document.getElementById('gameSection');
  const leaderboardBody = document.getElementById('leaderboardBody');
  const userOutcomeBox = document.getElementById('userOutcomeBox');

  if (gameSection) {
    // On the main game page, always show the game section (user is authenticated)
    gameSection.style.display = '';
  }

  // Fetch and display leaderboard
  async function fetchLeaderboard() {
    try {
      const res = await fetch('/leaderboard');
      const data = await res.json();
      const leaderboardBody = document.getElementById('leaderboardBody');
      leaderboardBody.innerHTML = '';
      
      data.forEach(([user, score, avoidedTwists, streak], idx) => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${idx + 1}</td>
          <td>${user}</td>
          <td>${score}</td>
          <td>${avoidedTwists}</td>
          <td>${streak}</td>
        `;
        leaderboardBody.appendChild(row);
      });
    } catch (e) {
      const leaderboardBody = document.getElementById('leaderboardBody');
      leaderboardBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #ff6b6b;">Could not load leaderboard.</td></tr>';
    }
  }
  fetchLeaderboard();
  
  // Make fetchLeaderboard globally accessible
  window.fetchLeaderboard = fetchLeaderboard;

  startBtn.onclick = async () => {
    const username = usernameInput.value.trim();
    if (!username) {
      usernameError.textContent = 'Please enter a username.';
      return;
    }
    try {
      const res = await fetch('/set_username', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ username })
      });
      const data = await res.json();
      if (data.success) {
        usernameSection.style.display = 'none';
        gameSection.style.display = '';
        usernameError.textContent = '';
        
        // Initialize spellbook functionality after game section is shown
        initializeSpellbook();
      } else {
        usernameError.textContent = data.error || 'Could not set username.';
      }
    } catch (e) {
      usernameError.textContent = 'Server error.';
    }
  };

  // Track spellbook uses
  let currentSpellbookUses = 0;
  let gameOver = false;
});

// Global spellbook variables
let spellbookModal, wishSuggestions;

// Initialize spellbook functionality
function initializeSpellbook() {
  console.log('Initializing spellbook...');
  const spellbookIcon = document.querySelector('.spellbook-icon');
  spellbookModal = document.getElementById('spellbookModal');
  const closeBtn = document.querySelector('.close');
  wishSuggestions = document.getElementById('wishSuggestions');

  console.log('Spellbook icon found:', spellbookIcon);
  console.log('Spellbook modal found:', spellbookModal);
  console.log('Close button found:', closeBtn);

  // Open spellbook modal
  spellbookIcon.addEventListener('click', (e) => {
    console.log('Spellbook clicked!');
    openSpellbook();
  });

  // Close modal when clicking X
  closeBtn.addEventListener('click', (e) => {
    console.log('Close button clicked!');
    closeSpellbook();
  });

  // Close modal when clicking outside
  window.addEventListener('click', (event) => {
    if (event.target === spellbookModal) {
      closeSpellbook();
    }
  });

  // Close modal with Escape key
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && spellbookModal.style.display === 'block') {
      closeSpellbook();
    }
  });
}

// Spellbook functions
function openSpellbook() {
  console.log('openSpellbook called');
  const modal = document.getElementById('spellbookModal');
  modal.style.display = 'block';
  generateWishSuggestions();
}

function closeSpellbook() {
  const modal = document.getElementById('spellbookModal');
  modal.style.display = 'none';
}

function generateWishSuggestions() {
  // Show loading state
  const wishSuggestions = document.getElementById('wishSuggestions');
  wishSuggestions.innerHTML = '<div class="loading">Consulting the ancient texts...</div>';
  
  // Call the AI-powered suggestion API
  fetch('/generate_suggestions', {
    method: 'POST',
    headers: getHeaders()
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      // Show error message
      wishSuggestions.innerHTML = `<div class="error-message">${data.error}</div>`;
      return;
    }
    
    const suggestions = data.suggestions;
    
    // Clear loading and display AI suggestions
    wishSuggestions.innerHTML = '';
    
    suggestions.forEach((suggestion, index) => {
      const suggestionDiv = document.createElement('div');
      suggestionDiv.className = 'wish-suggestion';
      suggestionDiv.innerHTML = `<p class="wish-text">${suggestion}</p>`;
      
      // Add click handler to fill wish input
      suggestionDiv.addEventListener('click', () => {
        const wishInput = document.getElementById('wishInput');
        wishInput.value = suggestion;
        closeSpellbook();
        wishInput.focus();
      });
      
      wishSuggestions.appendChild(suggestionDiv);
    });
  })
  .catch(error => {
    console.error('Error generating suggestions:', error);
    // Fallback to static suggestions
    showFallbackSuggestions();
  });
}

function showFallbackSuggestions() {
  const suggestions = [
    "I wish for the wisdom to make the best decisions in the next 24 hours",
    "I wish for the strength to help someone in need today",
    "I wish for a moment of genuine gratitude for what I already have",
    "I wish for the courage to face one small challenge today",
    "I wish for the patience to learn something new this week"
  ];

  // Shuffle and take 3 random suggestions
  const shuffled = suggestions.sort(() => 0.5 - Math.random());
  const selectedSuggestions = shuffled.slice(0, 3);

  // Clear and display suggestions
  const wishSuggestions = document.getElementById('wishSuggestions');
  wishSuggestions.innerHTML = '';
  
  selectedSuggestions.forEach((suggestion, index) => {
    const suggestionDiv = document.createElement('div');
    suggestionDiv.className = 'wish-suggestion';
    suggestionDiv.innerHTML = `<p class="wish-text">${suggestion}</p>`;
    
    // Add click handler to fill wish input
    suggestionDiv.addEventListener('click', () => {
      const wishInput = document.getElementById('wishInput');
      wishInput.value = suggestion;
      closeSpellbook();
      wishInput.focus();
    });
    
    wishSuggestions.appendChild(suggestionDiv);
  });
}

async function makeWish() {
  const wish = document.getElementById('wishInput').value;
  const resultDiv = document.getElementById('twistResult');
  const streakDiv = document.getElementById('streakDisplay');
  const wishesCountSpan = document.getElementById('wishesCount');
  const avoidedTwistsCountSpan = document.getElementById('avoidedTwistsCount');
  const winMsgDiv = document.getElementById('winMessage');
  const pawImg = document.getElementById('pawImage');
  const gameOverDiv = document.getElementById('gameOverMsg');
  const userOutcomeBox = document.getElementById('userOutcomeBox');
  resultDiv.innerHTML = 'Summoning the cursed paw...';
  winMsgDiv.innerHTML = '';
  gameOverDiv.innerHTML = '';
  userOutcomeBox.style.display = 'none';
  userOutcomeBox.textContent = '';

  try {
    const response = await fetch('/wish', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ wish }),
    });

    const text = await response.text();
    console.log('Raw response:', text);
    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      console.error('JSON parse error:', e);
      resultDiv.innerHTML = "<span style='color:crimson;'>Server returned invalid JSON.</span>";
      return;
    }

    if (typeof data.streak !== 'undefined') {
      streakDiv.childNodes[0].textContent = `🔥 Current Streak: ${data.streak} `;
    }
    if (typeof data.wishes_made !== 'undefined' && wishesCountSpan) {
      wishesCountSpan.textContent = `✨ Wishes Made: ${data.wishes_made}`;
    }
    if (typeof data.avoided_twists !== 'undefined' && avoidedTwistsCountSpan) {
      avoidedTwistsCountSpan.textContent = `🛡️ Avoided Twists: ${data.avoided_twists}`;
    }
    if (typeof data.failed_wishes !== 'undefined') {
      let fails = Math.max(0, Math.min(5, data.failed_wishes));
      if (pawImg) pawImg.src = `/static/images/paw_${fails}.png`;
    }
    if (data.game_over) {
      gameOverDiv.innerHTML = '☠️ The paw has claimed your soul.';
      streakDiv.childNodes[0].textContent = '🔥 Current Streak: 0 ';
      if (wishesCountSpan) wishesCountSpan.textContent = '✨ Wishes Made: 0';
      if (avoidedTwistsCountSpan) avoidedTwistsCountSpan.textContent = '🛡️ Avoided Twists: 0';
      if (pawImg) pawImg.src = '/static/images/paw_0.png';
      resultDiv.innerHTML = `<strong>💀 Twisted!</strong><br/><em>${data.twist}</em>`;
      winMsgDiv.innerHTML = '';
      userOutcomeBox.style.display = 'none';
      userOutcomeBox.textContent = '';
      // Refresh leaderboard after game over
      if (window.fetchLeaderboard) window.fetchLeaderboard();
      return;
    }
    if (data.result === "win") {
      resultDiv.innerHTML = `<strong>🎉 You win!</strong><br/><em>${data.twist}</em>`;
      winMsgDiv.innerHTML = `🎉 You survived the paw! Streak: ${data.streak}`;
    } else if (data.result === "lose") {
      resultDiv.innerHTML = `<strong>💀 Twisted!</strong><br/><em>${data.twist}</em>`;
      winMsgDiv.innerHTML = '';
    } else {
      resultDiv.innerHTML = `<span style='color:crimson;'>Error: ${data.error}</span>`;
      winMsgDiv.innerHTML = '';
    }

    // After displaying the twist, extract and show user outcome
    let outcomeMatch = /User outcome: (WIN|LOSE)/i.exec(data.twist);
    if (outcomeMatch) {
      const outcome = outcomeMatch[1].toUpperCase();
      userOutcomeBox.style.display = '';
      userOutcomeBox.textContent = outcome === 'WIN' ? 'You WIN!' : 'You LOSE!';
      userOutcomeBox.style.background = outcome === 'WIN' ? '#1fa672' : '#b91c1c';
      userOutcomeBox.style.color = '#fff';
      userOutcomeBox.style.border = outcome === 'WIN' ? '2px solid #1fa672' : '2px solid #b91c1c';
    } else {
      userOutcomeBox.style.display = 'none';
      userOutcomeBox.textContent = '';
    }
  } catch (err) {
    resultDiv.innerHTML = `<span style='color:crimson;'>Failed to connect to the server.</span>`;
    winMsgDiv.innerHTML = '';
    gameOverDiv.innerHTML = '';
  }
} 