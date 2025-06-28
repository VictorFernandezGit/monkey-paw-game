// Username/session/leaderboard logic
window.addEventListener('DOMContentLoaded', () => {
  const usernameSection = document.getElementById('usernameSection');
  const usernameInput = document.getElementById('usernameInput');
  const startBtn = document.getElementById('startBtn');
  const usernameError = document.getElementById('usernameError');
  const gameSection = document.getElementById('gameSection');
  const leaderboardList = document.getElementById('leaderboardList');
  const userOutcomeBox = document.getElementById('userOutcomeBox');

  // Hide game section until username is set
  gameSection.style.display = 'none';

  // Fetch and display leaderboard
  async function fetchLeaderboard() {
    try {
      const res = await fetch('/leaderboard');
      const data = await res.json();
      leaderboardList.innerHTML = '';
      data.forEach(([user, score, avoidedTwists], idx) => {
        const li = document.createElement('li');
        li.textContent = `${user}: ${score} (Avoided: ${avoidedTwists})`;
        leaderboardList.appendChild(li);
      });
    } catch (e) {
      leaderboardList.innerHTML = '<li>Could not load leaderboard.</li>';
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
      });
      const data = await res.json();
      if (data.success) {
        usernameSection.style.display = 'none';
        gameSection.style.display = '';
        usernameError.textContent = '';
      } else {
        usernameError.textContent = data.error || 'Could not set username.';
      }
    } catch (e) {
      usernameError.textContent = 'Server error.';
    }
  };
});

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
      headers: {
        'Content-Type': 'application/json',
      },
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