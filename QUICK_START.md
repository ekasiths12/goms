# 🚀 Quick Start - Local Development

## ✅ Your Setup is Ready!

I've created everything you need to test changes locally without waiting for Railway deployment.

## 🎯 How to Use

### 1. Start the Backend (Flask API)
```bash
cd backend
python3 main.py
```
**Result:** Flask app runs on http://localhost:8000

### 2. Start the Frontend Server (in a new terminal)
```bash
python3 serve_frontend.py
```
**Result:** Frontend served on http://localhost:3000

### 3. Test Your Changes
- **Backend API:** http://localhost:8000
- **Fabric Invoices:** http://localhost:3000/fabric-invoices.html
- **Health Check:** http://localhost:8000/api/health

## 🔄 Development Workflow

1. **Make changes** to your code
2. **Save files** - Flask auto-reloads (debug mode)
3. **Refresh browser** - See changes immediately
4. **Test functionality** - No waiting for Railway!
5. **Commit & push** when working correctly

## 📁 Files Created

- `run_local.py` - Backend startup script
- `serve_frontend.py` - Frontend server script  
- `LOCAL_DEVELOPMENT.md` - Detailed setup guide
- `QUICK_START.md` - This file

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Backend API | http://localhost:8000 | Flask API server |
| Fabric Invoices | http://localhost:3000/fabric-invoices.html | Main page |
| Health Check | http://localhost:8000/api/health | API status |
| Database Init | http://localhost:8000/api/init-db | Setup database |

## 💡 Pro Tips

- **Keep both servers running** while developing
- **Use browser dev tools** (F12) for debugging
- **Check Flask console** for backend errors
- **Test API endpoints** directly in browser
- **No HTTPS issues** locally (no mixed content errors)

## 🆘 If Something Goes Wrong

1. **Port in use:** `lsof -ti:8000 | xargs kill -9`
2. **Database issues:** Visit http://localhost:8000/api/init-db
3. **Python not found:** Use `python3` instead of `python`

## 🎉 You're All Set!

Now you can test all your changes locally and only deploy to Railway when you're satisfied with the results!
