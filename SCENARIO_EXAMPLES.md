# Real-World Usage Scenarios

## Scenario 1: Existing Bookings + Future Automation

**Situation**: You have Wed/Thu booked for 10th floor, want to ensure next 4 weeks are booked.

### Solution Approach:

**1. Test Current Setup (Mock Mode)**
```bash
team-booker book \
  --location-id "YOUR_LOCATION_ID" \
  --group-id "YOUR_GROUP_ID" \
  --user-id "YOUR_USER_ID" \
  --floor-id "FLOOR_10_ID" \
  --preferred-rooms "Your Regular Room Name" \
  --keywords "team,collaboration,meeting" \
  --weeks 4 \
  --mock --dry-run
```

**2. Real Test (Dry Run)**
```bash
team-booker book \
  --location-id "YOUR_LOCATION_ID" \
  --group-id "YOUR_GROUP_ID" \
  --user-id "YOUR_USER_ID" \
  --floor-id "FLOOR_10_ID" \
  --preferred-rooms "Your Regular Room Name" \
  --dry-run
```

**3. Book Available Slots**
```bash
team-booker book \
  --location-id "YOUR_LOCATION_ID" \
  --group-id "YOUR_GROUP_ID" \
  --user-id "YOUR_USER_ID" \
  --floor-id "FLOOR_10_ID" \
  --preferred-rooms "Your Regular Room Name"
```

### Smart Features for This Scenario:

**Preferred Rooms**: System will try your usual room first
```bash
--preferred-rooms "10th Floor Team Room A,10th Floor Conference B"
```

**Specific Dates**: Target only Wed/Thu
```bash
--date 2025-08-06 --date 2025-08-07 --date 2025-08-13 --date 2025-08-14
```

**Floor Filtering**: Focus on 10th floor only
```bash
--floor-id "FLOOR_10_ID"
```

### Automation Strategy:

**Weekly Automation** (Run Fridays to book 4 weeks ahead):
```bash
# Add to crontab (Friday 5 PM)
0 17 * * 5 team-booker book --location-id LOC001 --group-id GRP001 --user-id USR001 --floor-id FLR10 --preferred-rooms "Team Room A"
```

**Conflict Handling**: The system will:
- ✅ Skip dates already booked (won't double-book)
- ✅ Try alternative rooms if preferred room taken
- ✅ Log all attempts for review
- ✅ Email-style reporting in logs

## Scenario 2: Team Lead Managing Multiple Spaces

**Situation**: Need to book different team areas for different teams.

```bash
# Team A - Tuesdays
team-booker book --location-id LOC001 --group-id TEAM_A --user-id USR001 --date 2025-08-05 --preferred-rooms "Team A Space"

# Team B - Wednesdays  
team-booker book --location-id LOC001 --group-id TEAM_B --user-id USR001 --date 2025-08-06 --preferred-rooms "Team B Huddle"
```

## Scenario 3: Backup Room Strategy

**Situation**: Primary room often booked, need fallback options.

```bash
team-booker book \
  --location-id LOC001 \
  --group-id GRP001 \
  --user-id USR001 \
  --preferred-rooms "Primary Team Room,Secondary Conference,Backup Huddle" \
  --keywords "team,collaboration,meeting,conference"
```

**Priority Logic**:
1. Try "Primary Team Room" first
2. Fall back to "Secondary Conference"  
3. Fall back to "Backup Huddle"
4. Search by keywords if all preferred rooms taken

## Scenario 4: Handling Booking Conflicts

**What happens if your regular room is taken?**

The system automatically:
1. **Logs the conflict**: "Primary room unavailable for 2025-08-06"
2. **Tries alternatives**: Checks preferred rooms list
3. **Keyword search**: Finds similar rooms ("team", "collaboration")
4. **Books best match**: Reports which room was booked instead

**Review booking results**:
```bash
# Check what was actually booked
tail -n 20 team_booker.log

# Or view results table after booking
team-booker book --dry-run  # Shows current availability
```

## Pro Tips:

### 1. Finding Your IDs
- Log into Condeco web interface
- Open browser dev tools (F12) → Network tab
- Try booking manually, watch network requests
- Extract `locationID`, `groupID`, `userID`, `floorID`

### 2. Testing Strategy
```bash
# Start with mock mode
team-booker book --mock --dry-run --location-id TEST --group-id TEST --user-id TEST

# Then real system dry run
team-booker book --dry-run --location-id REAL_LOC --group-id REAL_GRP --user-id REAL_USR

# Finally live booking
team-booker book --location-id REAL_LOC --group-id REAL_GRP --user-id REAL_USR
```

### 3. Monitoring
```bash
# Check authentication status
team-booker status

# View recent activity
tail -f team_booker.log

# Clear credentials if needed
team-booker clear
```