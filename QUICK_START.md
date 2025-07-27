# Quick Start Guide

## 🚀 Getting Started

Your Condeco Team Area Booking System is ready! Here's how to get started:

### 1. Test the Installation
```bash
team-booker --help
```

### 2. Set Up Authentication  
You'll need to authenticate with your work Condeco system:

```bash
team-booker setup --unique-key your-company.condecosoftware.com
```

**Note:** Replace `your-company.condecosoftware.com` with your actual Condeco domain.

This will:
- Send a magic link to your work email
- Ask you to enter the validation code
- Securely store your authentication token

### 3. Test with Dry Run
**IMPORTANT:** Always test first with `--dry-run` before booking anything!

```bash
team-booker book \
  --location-id "YOUR_LOCATION_ID" \
  --group-id "YOUR_GROUP_ID" \
  --user-id "YOUR_USER_ID" \
  --dry-run
```

### 4. Find Your IDs
You'll need to find your Condeco IDs. Here's how:

1. **Log into your Condeco web interface at work**
2. **Open browser developer tools** (F12)
3. **Go to Network tab**
4. **Try to book a room manually**
5. **Look at the network requests** to find:
   - `locationID` 
   - `groupID`
   - `userID`
   - `floorID` (optional)

### 5. Book Team Areas
Once your dry run works, remove `--dry-run` to actually book:

```bash
team-booker book \
  --location-id "YOUR_LOCATION_ID" \
  --group-id "YOUR_GROUP_ID" \
  --user-id "YOUR_USER_ID" \
  --keywords "team,collaboration,huddle" \
  --weeks 4
```

## 🛡️ Safety Features

- **Dry Run Mode**: Always test first with `--dry-run`
- **Secure Storage**: Credentials stored in system keyring
- **Smart Room Selection**: Prioritizes team areas by keywords
- **Comprehensive Logging**: Full audit trail in `team_booker.log`

## 📅 Automation

To run this weekly, add to your crontab (Friday at 9 AM):
```bash
0 9 * * 5 team-booker book --location-id LOC001 --group-id GRP001 --user-id USR001
```

## 🔧 Commands Quick Reference

```bash
# Check auth status
team-booker status

# Clear credentials if needed  
team-booker clear

# Book specific dates
team-booker book --location-id LOC001 --group-id GRP001 --user-id USR001 --date 2024-02-06 --date 2024-02-07

# Verbose logging
team-booker -v book --location-id LOC001 --group-id GRP001 --user-id USR001 --dry-run
```

## 🆘 Troubleshooting

**Authentication Issues:**
```bash
team-booker status  # Check current status
team-booker clear   # Clear and start over if needed
```

**No Available Rooms:**
- Try different `--keywords` (e.g., "meeting,conference,boardroom")
- Use `--preferred-rooms "Room Name A,Room Name B"`
- Increase `--weeks` to book further ahead

**Import Errors:**
- Make sure you're in the project directory
- Check that `Hybrid-Worker/` exists in the current directory

---

**Need help?** Check the full README.md for detailed documentation and troubleshooting.