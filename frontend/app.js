/* Lightweight real-time client for GCID backend */
const frameImg = document.getElementById('frame');
const overlay = document.getElementById('overlay');
const ctx = overlay.getContext('2d');
const statusEl = document.getElementById('status');
const gesturesEl = document.getElementById('gestures');
const toolEl = document.getElementById('tool');
const pageEl = document.getElementById('page');
const wsUrlInput = document.getElementById('wsUrl');

let ws = null;
let reconnectInterval = 1500;
let lastFrameTime = performance.now();
let fps = 0;

function resizeCanvas() {
  overlay.width = frameImg.clientWidth;
  overlay.height = frameImg.clientHeight;
}
window.addEventListener('resize', resizeCanvas);
frameImg.addEventListener('load', resizeCanvas);

function setStatus(s, color = '#0a0'){
  statusEl.textContent = s;
  statusEl.style.background = color === '#0a0' ? '#e6fff1' : '#ffefef';
  statusEl.style.color = color === '#0a0' ? '#046633' : '#900';
}

function connect(){
  const url = wsUrlInput.value;
  ws = new WebSocket(url);

  ws.addEventListener('open', ()=>{ setStatus('Connected', '#0a0'); });
  ws.addEventListener('close', ()=>{ setStatus('Disconnected', '#900'); setTimeout(connect,reconnectInterval); });
  ws.addEventListener('error', (e)=>{ setStatus('Error', '#900'); console.error('ws error', e); ws.close(); });

  ws.addEventListener('message', (ev)=>{
    try{
      const msg = JSON.parse(ev.data);
      handleMessage(msg);
    }catch(err){ console.warn('non-json message or image chunk:', err); }
  });
}

function handleMessage(msg){
  if(msg.type === 'frame'){
    // image is base64 jpeg
    frameImg.src = 'data:image/jpeg;base64,' + msg.image;
    // landmarks could be used to draw cursor markers
    drawLandmarks(msg.landmarks || {});
    const now = performance.now();
    fps = 1000 / (now - lastFrameTime);
    lastFrameTime = now;
  } else if(msg.type === 'state'){
    // update UI state
    toolEl.textContent = msg.tool || '-';
    pageEl.textContent = `${(msg.page_index || 0) + 1}/${msg.total_pages || '?'}`;

    // If server sends canvas we can optionally overlay it
    if(msg.canvas){
      drawCanvas(msg.canvas);
    }
  }

  if(msg.gestures){
    gesturesEl.textContent = (msg.gestures.length ? msg.gestures.join(', ') : '-');
  }
}

function drawLandmarks(landmarks){
  ctx.clearRect(0,0,overlay.width,overlay.height);
  ctx.fillStyle = 'rgba(0,255,0,0.9)';
  for(const k in landmarks){
    const [x,y] = landmarks[k];
    // transform coord from image to displayed size
    const rect = frameImg.getBoundingClientRect();
    const scaleX = overlay.width / rect.width;
    const scaleY = overlay.height / rect.height;
    ctx.beginPath();
    ctx.arc(x*scaleX, y*scaleY, 6, 0, Math.PI*2);
    ctx.fill();
  }
}

function drawCanvas(b64){
  const img = new Image();
  img.onload = ()=>{
    // draw canvas into overlay with light transparency
    ctx.globalAlpha = 0.95;
    ctx.drawImage(img,0,0,overlay.width,overlay.height);
    ctx.globalAlpha = 1.0;
  };
  img.src = 'data:image/jpeg;base64,' + b64;
}

// send a command to server
function sendCommand(action, params={}){
  if(!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({type:'command', action, params}));
}

// UI bindings
document.getElementById('btnConnect').addEventListener('click', ()=>{ if(ws && ws.readyState===WebSocket.OPEN){ ws.close(); } connect(); });
document.getElementById('btnUndo').addEventListener('click', ()=>sendCommand('undo'));
document.getElementById('btnRedo').addEventListener('click', ()=>sendCommand('redo'));
document.getElementById('btnNewPage').addEventListener('click', ()=>sendCommand('new_page'));
document.getElementById('btnEraseAll').addEventListener('click', ()=>sendCommand('erase_all'));
document.getElementById('btnToggleDrawing').addEventListener('click', ()=>sendCommand('set_tool',{tool:'pen'}));
document.getElementById('btnEraser').addEventListener('click', ()=>sendCommand('set_tool',{tool:'eraser'}));

const colorPicker = document.getElementById('colorPicker');
colorPicker.addEventListener('input', ()=>{
  const hex = colorPicker.value;
  const rgb = hexToRgb(hex);
  sendCommand('set_color',{color:[rgb.r, rgb.g, rgb.b]});
});

document.getElementById('thickness').addEventListener('input', (e)=>{
  sendCommand('set_thickness',{thickness: parseInt(e.target.value,10)});
});

document.getElementById('btnDownloadCanvas').addEventListener('click', ()=>{
  // ask server for latest serialized canvas via state call
  // we actually maintain the last state canvas in the UI by drawing it
  const link = document.createElement('a');
  // capture current overlay as png
  const data = overlay.toDataURL('image/png');
  link.href = data;
  link.download = 'gcid_canvas.png';
  link.click();
});

function hexToRgb(hex){
  const bigint = parseInt(hex.slice(1), 16);
  return {r:(bigint>>16)&255, g:(bigint>>8)&255, b:bigint&255};
}

// start disconnected; only connect when user asks
setStatus('Disconnected', '#900');

// Optionally auto-connect on load
// connect();