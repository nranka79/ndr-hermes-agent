#!/usr/bin/env python3
"""
File an invitation card image to the root Invitations folder and create the
calendar event with guests — both deliverables of invitation-capture-workflow.md.

Run with the venv python (vault env vars are NOT available in execute_code):
    /opt/hermes/.venv/bin/python3 scripts/file_invite_to_drive_and_calendar.py

Edit the CONFIG block, then run. Idempotent on BOTH sides:
  * refuses to re-upload a card whose DRIVE_NAME already exists in the folder
    (added 2026-09-28 — first version only guarded the calendar event, so a
    re-run silently created a duplicate Drive card), and
  * refuses to double-book a calendar event whose summary matches EVENT_MATCH
    within the +/- window.

Two hard-won details baked in:
  * Root "Invitations" (1wmXLuD66KOTBtfsDvDQcTWnUjvKEjvt3) is the photo-card
    target — NOT Personal's 10MgC-… (see references/invitations-tracking-folder.md).
  * The calendar insert response's htmlLink can be unreliable — always re-fetch
    via events().list() and report that link.
"""
import sys

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

# ---------------------------------------------------------------- CONFIG
SRC = '/data/hermes/image_cache/img_REPLACE.jpg'   # local card image
DRIVE_NAME = 'YYYYMMDD_Event_HostOrVenue.jpg'
EVENT_TITLE = 'Event Title — Host / Venue'
EVENT_MATCH = 'HostSurname'      # substring used for the double-book guard
DATE = 'YYYY-MM-DD'              # verify the card's weekday actually matches!
START = 'HH:MM'                  # HH:MM local (Asia/Kolkata)
END = 'HH:MM'
TZ = 'Asia/Kolkata'
OFFSET = '+05:30'
LOCATION = 'Host Residence, Area, City'
EXTRA_DESC = ''                  # optional extra description lines
GUESTS = ['rnr@draas.com']       # Roshini is the standing default
# -----------------------------------------------------------------------

ROOT_INVITATIONS = '1wmXLuD66KOTBtfsDvDQcTWnUjvKEjvt3'
SERVICE = 'google-draas'

drive = build_service('drive', 'v3', service_name=SERVICE)
cal = build_service('calendar', 'v3', service_name=SERVICE)

# --- 0. prove the folder is live + idempotent upload -------------------
kids = drive.files().list(
    q=f"'{ROOT_INVITATIONS}' in parents and trashed=false",
    fields='files(id,name)', pageSize=100,
).execute().get('files', [])
print('ROOT INVITATIONS contents (%d):' % len(kids))
for k in kids:
    print('   -', k['name'])
dupe = [k for k in kids if k['name'] == DRIVE_NAME]
if dupe:
    print('ALREADY FILED:', dupe[0]['id'], '— skipping upload')
    fid = dupe[0]['id']
    DRIVE_LINK = 'https://drive.google.com/file/d/%s/view' % fid
else:
    media = MediaFileUpload(SRC, mimetype='image/jpeg', resumable=False)
    f = drive.files().create(
        body={'name': DRIVE_NAME, 'parents': [ROOT_INVITATIONS]},
        media_body=media,
        fields='id,name,parents,webViewLink,size',
    ).execute()
    print('UPLOADED', f['name'])
    print('  id   :', f['id'])
    print('  link :', f['webViewLink'])
    chk = drive.files().get(fileId=f['id'], fields='id,parents').execute()
    assert ROOT_INVITATIONS in chk.get('parents', []), 'not in target folder'
    print('  parents verified:', chk['parents'])
    fid = f['id']
    DRIVE_LINK = f['webViewLink'].split('?')[0]

for g in GUESTS:
    try:
        drive.permissions().create(
            fileId=fid,
            body={'type': 'user', 'role': 'reader', 'emailAddress': g},
            sendNotificationEmail=False, fields='id',
        ).execute()
        print('  shared with', g)
    except Exception as e:
        print('  share note for', g, ':', e)

# --- 2. double-book guard ---------------------------------------------
floor = DATE + 'T00:00:00' + OFFSET
ceil = (DATE[:8] + str(int(DATE[8:10]) + 2)) + 'T00:00:00' + OFFSET
existing = cal.events().list(
    calendarId='primary', q=EVENT_MATCH,
    timeMin=floor, timeMax=ceil, singleEvents=True,
).execute().get('items', [])
if existing:
    print('REFUSING — matching event already exists:')
    for e in existing:
        print('  ', e.get('id'), e.get('summary'), e.get('start'))
    sys.exit(0)

# --- 3. create the event ----------------------------------------------
desc = """Invitation: %s

%s

Original invitation card: %s
""" % (DRIVE_LINK, EXTRA_DESC, DRIVE_LINK)
event = {
    'summary': EVENT_TITLE,
    'location': LOCATION,
    'description': desc,
    'start': {'dateTime': '%sT%s:00%s' % (DATE, START, OFFSET), 'timeZone': TZ},
    'end':   {'dateTime': '%sT%s:00%s' % (DATE, END, OFFSET),   'timeZone': TZ},
    'attendees': [{'email': g} for g in GUESTS],
    'guestsCanSeeOtherGuests': False,
    'reminders': {'useDefault': True},
}
created = cal.events().insert(
    calendarId='primary', body=event, sendUpdates='all',
).execute()
print('CREATED event id:', created['id'])

# --- 4. re-fetch for a valid htmlLink ---------------------------------
items = cal.events().list(
    calendarId='primary', timeMin=floor, timeMax=ceil,
    singleEvents=True, orderBy='startTime',
).execute().get('items', [])
for e in items:
    if e.get('id') == created['id']:
        print('  summary :', e.get('summary'))
        print('  start   :', e['start'].get('dateTime'))
        print('  end     :', e['end'].get('dateTime'))
        print('  location:', e.get('location'))
        print('  guests  :', [a.get('email') for a in e.get('attendees', [])])
        print('  link    :', e.get('htmlLink'))
print('DRIVE LINK:', DRIVE_LINK)