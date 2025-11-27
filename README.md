# ⚖️ Litigation Tracker

A modern, portable web-based platform for tracking litigations. Built with Python FastAPI and SQLite for easy deployment on any system.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### Case Management
- **Auto-generated Case IDs** in `YYYY001` format
- **Multiple Forums**: CAT, HC, SC, Other Tribunals
- **Case Status Tracking**: Filed, Admission, Hearing, Dismissed, Adjourned, Reserved, Allowed
- **Appeal Management** with Lower Court details
- **Connected Cases** support

### Party Management
- Multiple Petitioners (P1, P2, etc.)
- Multiple Respondents (R1, R2, etc.)
- Name and Address tracking

### Document Management
- Upload and store case documents
- Document types: Affidavits, Counter Affidavits, Rejoinders, Court Orders
- Filing date tracking
- Download functionality

### Hearing Chronology
- Track all hearing dates
- Brief notes for each hearing
- Automatic last hearing date update

### Dashboard
- **Statistics Overview**: Total cases, by status, by forum
- **Upcoming Hearings**: Cases with hearing in next 10 days
- **Recent Updates**: Latest modified cases

### Access Control
- Admin user management
- Maximum 10 users
- User activation/deactivation
- Audit trail (created by, updated by)

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone/Download the project**
   ```bash
   cd LitigationTracker
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Open in browser**
   ```
   http://localhost:8000
   ```

### Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Important**: Change the default password after first login!

## 📁 Project Structure

```
LitigationTracker/
├── main.py              # FastAPI application
├── models.py            # Database models (SQLAlchemy)
├── auth.py              # Authentication utilities
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── litigation_tracker.db # SQLite database (auto-created)
├── uploads/             # Document storage
├── static/
│   ├── css/
│   │   └── style.css    # Application styles
│   └── js/
│       └── app.js       # JavaScript utilities
└── templates/
    ├── base.html        # Base template
    ├── login.html       # Login page
    ├── dashboard.html   # Dashboard
    ├── cases.html       # Case listing
    ├── case_form.html   # Create/Edit case
    ├── case_view.html   # Case details
    └── users.html       # User management
```

## 🔧 Configuration

### Security Settings
Edit `auth.py` to change:
```python
SECRET_KEY = "your-secure-secret-key"  # Change in production!
ACCESS_TOKEN_EXPIRE_MINUTES = 480       # Session duration
```

### Database
The application uses SQLite by default. The database file `litigation_tracker.db` is created automatically in the project root.

To use a different database, modify `DATABASE_URL` in `models.py`:
```python
# For PostgreSQL
DATABASE_URL = "postgresql://user:password@localhost/litigation_tracker"

# For MySQL
DATABASE_URL = "mysql://user:password@localhost/litigation_tracker"
```

## 🖥️ Deployment

### Using Docker (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t litigation-tracker .
docker run -p 8000:8000 -v ./uploads:/app/uploads -v ./litigation_tracker.db:/app/litigation_tracker.db litigation-tracker
```

### Using systemd (Linux)

Create `/etc/systemd/system/litigation-tracker.service`:
```ini
[Unit]
Description=Litigation Tracker
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/LitigationTracker
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable litigation-tracker
sudo systemctl start litigation-tracker
```

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Redirect to dashboard/login |
| GET/POST | `/login` | Authentication |
| GET | `/logout` | Logout |
| GET | `/dashboard` | Main dashboard |
| GET | `/cases` | List all cases |
| GET/POST | `/cases/new` | Create new case |
| GET | `/cases/{id}` | View case details |
| GET/POST | `/cases/{id}/edit` | Edit case |
| POST | `/cases/{id}/parties` | Add party |
| POST | `/cases/{id}/documents` | Upload document |
| POST | `/cases/{id}/hearings` | Add hearing |
| GET | `/documents/{id}/download` | Download document |
| GET | `/users` | User management (admin) |
| POST | `/users` | Create user (admin) |
| GET | `/api/stats` | Dashboard statistics |

## 🔐 Security Notes

1. **Change the SECRET_KEY** in production
2. **Use HTTPS** in production (use a reverse proxy like nginx)
3. **Change default admin password** immediately
4. **Regular backups** of `litigation_tracker.db` and `uploads/` folder
5. **Set proper file permissions** on the database and uploads directory

## 📝 Data Backup

### Backup
```bash
# Backup database
cp litigation_tracker.db backup/litigation_tracker_$(date +%Y%m%d).db

# Backup uploads
tar -czf backup/uploads_$(date +%Y%m%d).tar.gz uploads/
```

### Restore
```bash
# Restore database
cp backup/litigation_tracker_YYYYMMDD.db litigation_tracker.db

# Restore uploads
tar -xzf backup/uploads_YYYYMMDD.tar.gz
```

## 🐛 Troubleshooting

### Port already in use
```bash
# Change port
uvicorn main:app --port 8001
```

### Database locked
```bash
# Ensure no other process is using the database
lsof litigation_tracker.db
```

### Permission issues
```bash
# Fix permissions
chmod 755 uploads/
chmod 644 litigation_tracker.db
```

## 📄 License

MIT License - feel free to use and modify for your needs.

## 🤝 Support

For issues or feature requests, please create an issue in the repository.

---

Built with ❤️ using FastAPI, SQLAlchemy, and modern web technologies.

