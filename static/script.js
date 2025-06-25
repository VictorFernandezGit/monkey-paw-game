async function makeWish() {
  const wish = document.getElementById('wishInput').value;
  const resultDiv = document.getElementById('twistResult');
  const streakDiv = document.getElementById('streakDisplay');
  const winMsgDiv = document.getElementById('winMessage');
  const pawImg = document.getElementById('pawImage');
  const gameOverDiv = document.getElementById('gameOverMsg');
  resultDiv.innerHTML = 'Summoning the cursed paw...';
  winMsgDiv.innerHTML = '';
  gameOverDiv.innerHTML = '';

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
      streakDiv.textContent = `🔥 Current Streak: ${data.streak}`;
    }
    if (typeof data.failed_wishes !== 'undefined') {
      // Clamp between 0 and 5
      let fails = Math.max(0, Math.min(5, data.failed_wishes));
      pawImg.src = `/static/images/paw_${fails}.png`;
    }
    if (data.game_over) {
      gameOverDiv.innerHTML = '☠️ The paw has claimed your soul.';
      streakDiv.textContent = '🔥 Current Streak: 0';
      pawImg.src = '/static/images/paw_0.png';
      resultDiv.innerHTML = `<strong>💀 Twisted!</strong><br/><em>${data.twist}</em>`;
      winMsgDiv.innerHTML = '';
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
  } catch (err) {
    resultDiv.innerHTML = `<span style='color:crimson;'>Failed to connect to the server.</span>`;
    winMsgDiv.innerHTML = '';
    gameOverDiv.innerHTML = '';
  }
} 