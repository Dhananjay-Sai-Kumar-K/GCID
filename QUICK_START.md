# 🚀 Quick Start Guide - Gesture Craft

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.9 or higher
- ✅ Node.js 18 or higher
- ✅ A working webcam
- ✅ Git (optional, for version control)

---

## 🎯 Installation (3 Steps)

### Step 1: Setup Python Backend

```powershell
# Navigate to project root
cd c:\Users\dhana\AppData\Local\Programs\Python\Python39\GCID

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Setup React Frontend

```powershell
# Navigate to frontend directory
cd frontend-aaa

# Install Node.js dependencies
npm install
```

### Step 3: Verify Installation

```powershell
# Check if backend dependencies are installed
python -c "import fastapi, cv2, mediapipe; print('✅ Backend ready!')"

# Check if frontend dependencies are installed
npm list react framer-motion lucide-react
```

---

## 🎮 Running the Application

### Option A: Web Browser Mode (Recommended for Testing)

**Terminal 1 - Backend:**
```powershell
cd c:\Users\dhana\AppData\Local\Programs\Python\Python39\GCID
.venv\Scripts\activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd c:\Users\dhana\AppData\Local\Programs\Python\Python39\GCID\frontend-aaa
npm run dev
```

Then open your browser to: **http://localhost:5173**

### Option B: Electron Desktop App (AAA Experience)

**Terminal 1 - Backend:**
```powershell
cd c:\Users\dhana\AppData\Local\Programs\Python\Python39\GCID
.venv\Scripts\activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Electron:**
```powershell
cd c:\Users\dhana\AppData\Local\Programs\Python\Python39\GCID\frontend-aaa
npm run electron:dev
```

### Option C: Use Launch Scripts (Easiest)

```powershell
# Terminal 1
.\start-backend.ps1

# Terminal 2 (choose one)
.\start-frontend.ps1   # For web browser
.\start-electron.ps1   # For desktop app
```

---

## 🎨 First Time Usage

1. **Start Backend** - Wait for "Application startup complete"
2. **Start Frontend** - Wait for the UI to load
3. **Click "Connect"** - Establish WebSocket connection
4. **Allow Camera Access** - Grant permission when prompted
5. **Wave Your Hand** - See real-time tracking!

---

## 🔧 Troubleshooting

### Backend Won't Start

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```powershell
# Make sure virtual environment is activated
.venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Won't Start

**Problem:** `Cannot find module 'react'`

**Solution:**
```powershell
cd frontend-aaa
npm install
```

### Camera Not Working

**Problem:** Black screen or "Camera access denied"

**Solution:**
1. Check Windows camera permissions: Settings > Privacy > Camera
2. Ensure no other app is using the camera
3. Try a different browser (Chrome recommended)

### WebSocket Connection Failed

**Problem:** "Disconnected" status in UI

**Solution:**
1. Ensure backend is running on port 8000
2. Check WebSocket URL in UI: `ws://localhost:8000/ws`
3. Check firewall settings

### Electron Won't Start

**Problem:** `Error: Cannot find module 'electron'`

**Solution:**
```powershell
cd frontend-aaa
npm install electron electron-is-dev --save-dev
```

---

## 📊 Expected Behavior

### When Everything Works:

1. **Backend Console:**
   ```
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

2. **Frontend UI:**
   - Status badge shows "Connected" (green)
   - FPS counter shows 25-30 FPS
   - Camera feed displays in viewport
   - Hand landmarks appear as purple dots

3. **Gesture Detection:**
   - Open your palm → "OPEN_PALM" badge appears
   - Close your fist → "FIST" badge appears
   - Pinch thumb and index → "PINCH" badge appears

---

## 🎯 Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads in browser/Electron
- [ ] WebSocket connects successfully
- [ ] Camera feed displays
- [ ] Hand landmarks appear when hand is visible
- [ ] Gestures are detected and displayed
- [ ] Tools can be switched (pen/eraser)
- [ ] Color picker works
- [ ] Thickness slider works
- [ ] Undo/redo buttons work
- [ ] New page creates a new canvas
- [ ] Erase all clears the canvas
- [ ] Download saves canvas as PNG

---

## 🚀 Next Steps

Once everything is working:

1. **Explore the UI** - Try all tools and controls
2. **Test Gestures** - Practice different hand poses
3. **Read Documentation** - Check README.md and SYSTEM_DESIGN.md
4. **Customize** - Modify colors, add features
5. **Deploy** - Build for production

---

## 📚 Additional Resources

- **README.md** - Full documentation
- **SYSTEM_DESIGN.md** - Architecture details
- **PROJECT_SUMMARY.md** - Feature overview

---

## 🆘 Still Having Issues?

If you encounter problems:

1. Check Python version: `python --version` (should be 3.9+)
2. Check Node.js version: `node --version` (should be 18+)
3. Check if ports are available: 8000 (backend), 5173 (frontend)
4. Review error messages in console
5. Restart both backend and frontend

---

## 🎉 Success!

If you see:
- ✅ Green "Connected" status
- ✅ Live camera feed
- ✅ Purple hand landmarks
- ✅ Gesture badges appearing

**Congratulations! Your AAA-grade hand tracking studio is running!** 🎊

---

**Happy Tracking!** 👋

*Built with ❤️ using the AAA Stack*
