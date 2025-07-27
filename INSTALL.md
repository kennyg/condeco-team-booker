# Installation Guide

## 🚀 Quick Install (Recommended)

### Using uvx (Easiest for work environments)

```bash
# Install directly from GitHub (no local clone needed)
uvx install git+https://github.com/your-username/condeco-team-booker.git

# Or install from PyPI (when published)
uvx install condeco-team-booker
```

**Benefits of uvx:**
- ✅ No need to clone repository
- ✅ Automatic virtual environment management
- ✅ Clean installation that doesn't affect system Python
- ✅ Perfect for work machines with restricted permissions

### Verify Installation
```bash
team-booker --help
```

## 🔧 Development Install

### Prerequisites
- Python 3.8+ 
- uv package manager

### Clone and Install
```bash
# Clone the repository
git clone https://github.com/your-username/condeco-team-booker.git
cd condeco-team-booker

# Ensure Hybrid-Worker dependency is available
git clone https://github.com/Matthew1471/Hybrid-Worker.git

# Install with uv
uv sync

# Run in development mode
uv run team-booker --help
```

## 📋 Alternative Installation Methods

### Using pip
```bash
pip install git+https://github.com/your-username/condeco-team-booker.git
```

### From source
```bash
git clone https://github.com/your-username/condeco-team-booker.git
cd condeco-team-booker
pip install -e .
```

## 🏢 Work Environment Setup

### Step 1: Install at Work
```bash
# One command - no admin rights needed
uvx install git+https://github.com/your-username/condeco-team-booker.git
```

### Step 2: Initial Setup
```bash
# Set up authentication (run once)
team-booker setup --unique-key your-company.condecosoftware.com
```

### Step 3: Test with Mock Mode
```bash
# Test the system without real bookings
team-booker book \
  --location-id "TEST" \
  --group-id "TEST" \
  --user-id "TEST" \
  --mock --dry-run
```

### Step 4: Find Your Real IDs
1. Log into your company's Condeco web interface
2. Open browser Developer Tools (F12) → Network tab
3. Try booking a room manually
4. Look at the network requests to find your:
   - `locationID`
   - `groupID` 
   - `userID`
   - `floorID` (optional)

### Step 5: Real Test
```bash
# Test with your real IDs (dry run first!)
team-booker book \
  --location-id "YOUR_REAL_LOCATION_ID" \
  --group-id "YOUR_REAL_GROUP_ID" \
  --user-id "YOUR_REAL_USER_ID" \
  --dry-run
```

### Step 6: Live Booking
```bash
# Remove --dry-run when ready to actually book
team-booker book \
  --location-id "YOUR_REAL_LOCATION_ID" \
  --group-id "YOUR_REAL_GROUP_ID" \
  --user-id "YOUR_REAL_USER_ID" \
  --preferred-rooms "Your Team Area Name"
```

## 🔄 Updates

### Update uvx Installation
```bash
uvx upgrade condeco-team-booker
```

### Update Development Installation
```bash
cd condeco-team-booker
git pull
uv sync
```

## 🆘 Troubleshooting

### Common Issues

**ImportError: No module named 'hybrid_worker'**
- Make sure `Hybrid-Worker` is cloned in the project directory
- Or use the `--mock` flag for testing without dependencies

**Authentication Failed**
```bash
team-booker status  # Check current status
team-booker clear   # Clear credentials
team-booker setup   # Re-setup authentication
```

**Permission Errors**
- Use uvx instead of pip for work environments
- Check that you have access to your company's Condeco system

**Can't Find Room IDs**
- Use browser dev tools to inspect Condeco network requests
- Try the mock mode first: `--mock --dry-run`

## 💡 Pro Tips

1. **Start with Mock Mode**: Always test with `--mock --dry-run` first
2. **Use Specific Dates**: Target exact dates with `--date YYYY-MM-DD`
3. **Preferred Rooms**: Use `--preferred-rooms` for your regular spaces
4. **Automation**: Set up weekly cron jobs for continuous booking
5. **Logging**: Check `team_booker.log` for detailed operation logs

## 🔒 Security Notes

- Credentials are stored securely using system keyring
- No passwords stored - only JWT tokens with expiration
- All network traffic is HTTPS
- Configuration files have restricted permissions (600)