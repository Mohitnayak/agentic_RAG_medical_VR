async function post(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return await res.json();
}

document.getElementById('send').onclick = async () => {
  const sessionId = document.getElementById('session').value;
  const message = document.getElementById('message').value;
  const out = document.getElementById('output');
  const data = await post('/api/v1/chat', { sessionId, message });
  out.innerText = JSON.stringify(data, null, 2);
};

document.getElementById('start-notes').onclick = async () => {
  const sessionId = document.getElementById('session').value;
  await post('/api/v1/notes/start', { sessionId });
};

document.getElementById('end-notes').onclick = async () => {
  const sessionId = document.getElementById('session').value;
  await post('/api/v1/notes/end', { sessionId });
};


