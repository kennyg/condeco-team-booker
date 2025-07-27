# Condeco Team Area Booking System

An automated booking system for Condeco workspace management that ensures your team has reserved areas for Tuesdays and Wednesdays.

## Features

- 🔐 **Secure Authentication**: Browser-based login with secure credential storage using keyring
- 🧪 **Dry Run Mode**: Test bookings without actually making reservations
- 📅 **Automated Scheduling**: Automatically books Tuesdays and Wednesdays up to 4 weeks ahead
- 🎯 **Smart Room Selection**: Prioritizes preferred rooms and uses keywords to find team areas
- 📊 **Rich CLI Interface**: Beautiful command-line interface with progress tracking and results tables
- 🔍 **Comprehensive Testing**: Full test suite with 95%+ coverage
- 📝 **Detailed Logging**: Complete audit trail of all booking attempts

## 🚀 Quick Install

**At Work (Recommended):**
```bash
uvx install git+https://github.com/your-username/condeco-team-booker.git
```

**For Development:**
```bash
git clone https://github.com/your-username/condeco-team-booker.git
cd condeco-team-booker
git clone https://github.com/Matthew1471/Hybrid-Worker.git
uv sync
```

📖 **[Full Installation Guide](INSTALL.md)** - Complete setup instructions for work environments

## Quick Start

### 1. Initial Setup
Configure authentication with your Condeco system:

```bash
team-booker setup --unique-key your-company.condecosoftware.com
```

This will:
- Send a magic link to your email
- Guide you through entering the validation code
- Securely store your authentication token

### 2. Test with Dry Run
Before booking anything, test the configuration:

```bash
team-booker book \
  --location-id "LOC001" \
  --group-id "GRP001" \
  --user-id "USR001" \
  --dry-run
```

### 3. Book Team Areas
Once you've verified the dry run works:

```bash
team-booker book \
  --location-id "LOC001" \
  --group-id "GRP001" \
  --user-id "USR001" \
  --keywords "team,collaboration,huddle" \
  --weeks 4
```

## Configuration

### Finding Your IDs

You'll need to find your Condeco IDs. These can typically be found by:

1. **Logging into Condeco web interface**
2. **Inspecting network requests** in browser developer tools when booking manually
3. **Checking URLs** - they often contain location and group IDs

### Room Selection Priority

The system selects rooms in this order:
1. **Preferred rooms** (if specified with `--preferred-rooms`)
2. **Keyword matches** (rooms containing words like "team", "collaboration")
3. **Any available room** (as fallback)

### Keywords

Default keywords that identify team areas:
- team
- collaboration  
- meeting
- huddle

Override with: `--keywords "custom,keywords,here"`

## Command Reference

### `team-booker setup`
Initial authentication setup
- `--unique-key`: Your Condeco domain (e.g., company.condecosoftware.com)

### `team-booker book`
Book team areas for upcoming Tuesdays and Wednesdays

**Required:**
- `--location-id`: Condeco location identifier
- `--group-id`: Condeco group identifier  
- `--user-id`: Your Condeco user identifier

**Optional:**
- `--floor-id`: Specific floor (if applicable)
- `--keywords`: Comma-separated keywords for team area identification
- `--preferred-rooms`: Comma-separated list of preferred room names
- `--weeks`: Number of weeks ahead to book (default: 4)
- `--dry-run`: Test mode - show what would be booked
- `--date`: Specific date to book (YYYY-MM-DD format, can be used multiple times)

### `team-booker status`
Check authentication status and configuration

### `team-booker clear`
Clear all stored credentials and configuration

## Scheduling Automation

### Cron Setup (Linux/macOS)
Add to your crontab to run weekly on Fridays at 9 AM:

```bash
# Edit crontab
crontab -e

# Add this line (adjust path to your installation)
0 9 * * 5 /usr/local/bin/team-booker book --location-id LOC001 --group-id GRP001 --user-id USR001
```

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger for weekly on Fridays
4. Set action to run: `team-booker book [your options]`

### GitHub Actions / CI/CD
You can also run this in GitHub Actions or other CI/CD systems using environment variables:

```yaml
name: Book Team Areas
on:
  schedule:
    - cron: '0 9 * * 5'  # Fridays at 9 AM
  
jobs:
  book:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          git clone https://github.com/Matthew1471/Hybrid-Worker.git
          pip install -e .
      - name: Book team areas
        env:
          CONDECO_TOKEN: ${{ secrets.CONDECO_TOKEN }}
        run: |
          team-booker book --location-id ${{ vars.LOCATION_ID }} --group-id ${{ vars.GROUP_ID }} --user-id ${{ vars.USER_ID }}
```

## Security

- **Tokens** are stored securely using the system keyring (Keychain on macOS, Credential Manager on Windows)
- **Configuration files** have restricted permissions (600)
- **No passwords** are stored - only JWT tokens with expiration
- **Environment variable fallback** available for CI/CD scenarios

## Development

### Running Tests
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=team_booker --cov-report=html
```

### Code Quality
```bash
# Format code
black team_booker/ tests/

# Lint code  
flake8 team_booker/ tests/

# Type checking
mypy team_booker/
```

## Troubleshooting

### Authentication Issues
```bash
# Check current status
team-booker status

# Clear and reconfigure if needed
team-booker clear
team-booker setup
```

### Booking Failures
1. **Test with dry run first**: `--dry-run` flag
2. **Check IDs are correct**: Verify location-id, group-id, user-id
3. **Review logs**: Check `team_booker.log` for detailed error messages
4. **Token expiration**: Tokens expire - re-run setup if needed

### No Available Rooms
- Adjust `--keywords` to match your organization's room naming
- Use `--preferred-rooms` to specify exact room names
- Increase `--weeks` to book further in advance
- Check if rooms exist in Condeco for your location/group

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built on top of [Hybrid-Worker](https://github.com/Matthew1471/Hybrid-Worker) by Matthew1471
- Uses the Condeco mobile API for workspace booking