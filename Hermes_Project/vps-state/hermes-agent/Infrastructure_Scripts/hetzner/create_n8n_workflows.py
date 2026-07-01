import json, urllib.request, urllib.error, uuid

NEW_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiYzA2YzgxMC00NGI0LTQ5ZjUtYTIzNS1jMmQ4ZDliNGFhODciLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiYTgxNjlhZGQtOTNmMi00Yjc0LThlZjEtODgzNTA2YWEwY2Y2IiwiaWF0IjoxNzc3NDM2NTM0fQ.4Qy5Kf-PyY95OYh3hZt8AZ_uln2If0iBeKyOkjeHoqM'
BASE_URL = 'https://transcribe.ahfl.in'
SA_DELEGATED = 'ndr@draas.com'

SA_AUTH_JS = r"""
const fetch = (url, {method='GET',headers={},body}={}) => new Promise((resolve,reject) => {
  const mod = require('https');
  const {URL:UrlCls} = require('url');
  const u = new UrlCls(url);
  const req = mod.request(
    {hostname:u.hostname,port:443,path:u.pathname+(u.search||''),method,headers},
    res => {
      const buf=[];
      res.on('data',c=>buf.push(c));
      res.on('end',()=>{
        const text=Buffer.concat(buf).toString();
        resolve({status:res.statusCode,ok:res.statusCode<300,
          text:()=>Promise.resolve(text),
          json:()=>Promise.resolve(JSON.parse(text))});
      });
    });
  req.on('error',reject);
  if(body)req.write(typeof body==='string'?body:JSON.stringify(body));
  req.end();
});
async function getGoogleToken(scope) {
  const sa = JSON.parse($env.GOOGLE_SA_KEY);
  const b64url = obj => Buffer.from(JSON.stringify(obj)).toString('base64')
    .replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_');
  const now = Math.floor(Date.now()/1000);
  const header = b64url({alg:'RS256',typ:'JWT'});
  const claims = b64url({iss:sa.client_email,sub:'""" + SA_DELEGATED + r"""',
    aud:'https://oauth2.googleapis.com/token',iat:now,exp:now+3600,scope});
  const crypto = require('crypto');
  const signer = crypto.createSign('RSA-SHA256');
  signer.update(header+'.'+claims);
  const sig = signer.sign(sa.private_key,'base64')
    .replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_');
  const jwt = `${header}.${claims}.${sig}`;
  const tr = await fetch('https://oauth2.googleapis.com/token',{
    method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:`grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`
  });
  const t = await tr.json();
  if(!t.access_token) throw new Error('Token error: '+JSON.stringify(t));
  return t.access_token;
}
async function gapi(token,method,url,body,qs) {
  let u = url;
  if(qs) {
    const enc = encodeURIComponent;
    const parts = [];
    for(const [k,v] of Object.entries(qs)) {
      if(Array.isArray(v)) v.forEach(vi => parts.push(enc(k)+'='+enc(vi)));
      else parts.push(enc(k)+'='+enc(String(v)));
    }
    u += '?' + parts.join('&');
  }
  const opts = {method, headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'}};
  if(body && method!=='GET' && method!=='DELETE') opts.body = JSON.stringify(body);
  const r = await fetch(u, opts);
  const text = await r.text();
  try { return JSON.parse(text); } catch { return {raw:text,status:r.status}; }
}
"""

SHEETS_JS = SA_AUTH_JS + r"""
const body = $input.first().json.body || $input.first().json;
const op = body.operation, sid = body.spreadsheetId;
const base = `https://sheets.googleapis.com/v4/spreadsheets/${sid}/values`;
const enc = s => encodeURIComponent(s);
const token = await getGoogleToken('https://www.googleapis.com/auth/spreadsheets');
let result;
if(op==='values.get') {
  result = await gapi(token,'GET',`${base}/${enc(body.range)}`);
} else if(op==='values.append') {
  result = await gapi(token,'POST',`${base}/${enc(body.range)}:append`,{values:body.values},{valueInputOption:'USER_ENTERED',insertDataOption:'INSERT_ROWS'});
} else if(op==='values.update') {
  result = await gapi(token,'PUT',`${base}/${enc(body.range)}`,{values:body.values},{valueInputOption:'USER_ENTERED'});
} else if(op==='values.batchGet') {
  result = await gapi(token,'GET',`${base}:batchGet`,null,{ranges:body.ranges});
} else { throw new Error('Unknown op: '+op); }
return [{json:{success:true,data:result}}];
"""

GMAIL_JS = SA_AUTH_JS + r"""
const body = $input.first().json.body || $input.first().json;
const op = body.operation;
const base = 'https://gmail.googleapis.com/gmail/v1/users/me';
const token = await getGoogleToken('https://www.googleapis.com/auth/gmail.modify');
let result;
if(op==='messages.list') {
  result = await gapi(token,'GET',`${base}/messages`,null,{q:body.query||'',maxResults:body.maxResults||20});
} else if(op==='messages.get') {
  result = await gapi(token,'GET',`${base}/messages/${body.messageId}`,null,{format:'full'});
} else if(op==='threads.get') {
  result = await gapi(token,'GET',`${base}/threads/${body.threadId}`,null,{format:'full'});
} else if(op==='messages.send'||op==='messages.send-reply') {
  const hdrs = [`To: ${body.to}`,`Subject: ${body.subject}`,'Content-Type: text/plain; charset=utf-8'];
  if(body.cc) hdrs.push(`Cc: ${body.cc}`);
  if(body.replyTo) hdrs.push(`In-Reply-To: ${body.replyTo}`,`References: ${body.replyTo}`);
  const raw = Buffer.from(hdrs.join('\r\n')+'\r\n\r\n'+body.body).toString('base64')
    .replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_');
  result = await gapi(token,'POST',`${base}/messages/send`,{raw});
} else { throw new Error('Unknown op: '+op); }
return [{json:{success:true,data:result}}];
"""

CALENDAR_JS = SA_AUTH_JS + r"""
const body = $input.first().json.body || $input.first().json;
const op = body.operation;
const calId = encodeURIComponent(body.calendarId || 'ndr@draas.com');
const base = `https://www.googleapis.com/calendar/v3/calendars/${calId}/events`;
const token = await getGoogleToken('https://www.googleapis.com/auth/calendar');
let result;
if(op==='events.list') {
  const qs = {singleEvents:true,orderBy:'startTime'};
  if(body.timeMin) qs.timeMin=body.timeMin;
  if(body.timeMax) qs.timeMax=body.timeMax;
  if(body.query) qs.q=body.query;
  if(body.maxResults) qs.maxResults=body.maxResults;
  result = await gapi(token,'GET',base,null,qs);
} else if(op==='events.get') {
  result = await gapi(token,'GET',`${base}/${body.eventId}`);
} else if(op==='events.create') {
  const tz = body.timeZone||'Asia/Kolkata';
  const ev = {summary:body.summary,start:{dateTime:body.start,timeZone:tz},end:{dateTime:body.end,timeZone:tz}};
  if(body.description) ev.description=body.description;
  if(body.location) ev.location=body.location;
  if(body.attendees) ev.attendees=body.attendees.map(e=>({email:e}));
  result = await gapi(token,'POST',base,ev);
} else if(op==='events.update') {
  result = await gapi(token,'PATCH',`${base}/${body.eventId}`,body.updates);
} else if(op==='events.delete') {
  await gapi(token,'DELETE',`${base}/${body.eventId}`);
  result = {deleted:true};
} else { throw new Error('Unknown op: '+op); }
return [{json:{success:true,data:result||{deleted:true}}}];
"""

DOCS_JS = SA_AUTH_JS + r"""
const body = $input.first().json.body || $input.first().json;
const op = body.operation;
const base = 'https://docs.googleapis.com/v1/documents';
const token = await getGoogleToken('https://www.googleapis.com/auth/documents');
let result;
if(op==='documents.get') {
  result = await gapi(token,'GET',`${base}/${body.documentId}`);
} else if(op==='documents.create') {
  result = await gapi(token,'POST',base,{title:body.title});
} else if(op==='documents.append') {
  const doc = await gapi(token,'GET',`${base}/${body.documentId}`);
  const endIndex = doc.body.content[doc.body.content.length-1].endIndex - 1;
  result = await gapi(token,'POST',`${base}/${body.documentId}:batchUpdate`,
    {requests:[{insertText:{location:{index:endIndex},text:body.content}}]});
} else { throw new Error('Unknown op: '+op); }
return [{json:{success:true,data:result}}];
"""

TASKS_JS = SA_AUTH_JS + r"""
const body = $input.first().json.body || $input.first().json;
const op = body.operation;
const listId = encodeURIComponent(body.tasklistId||'@default');
const base = `https://tasks.googleapis.com/tasks/v1/lists/${listId}/tasks`;
const token = await getGoogleToken('https://www.googleapis.com/auth/tasks');
let result;
if(op==='tasklists.list') {
  result = await gapi(token,'GET','https://tasks.googleapis.com/tasks/v1/users/@me/lists');
} else if(op==='tasks.list') {
  result = await gapi(token,'GET',base,null,{maxResults:body.maxResults||100,showCompleted:false});
} else if(op==='tasks.get') {
  result = await gapi(token,'GET',`${base}/${body.taskId}`);
} else if(op==='tasks.create') {
  const t={title:body.title};
  if(body.notes) t.notes=body.notes;
  if(body.due) t.due=body.due;
  result = await gapi(token,'POST',base,t);
} else if(op==='tasks.update') {
  const p={};
  ['title','notes','status','due'].forEach(k=>{if(body[k]!==undefined)p[k]=body[k];});
  result = await gapi(token,'PATCH',`${base}/${body.taskId}`,p);
} else if(op==='tasks.complete') {
  result = await gapi(token,'PATCH',`${base}/${body.taskId}`,{status:'completed'});
} else if(op==='tasks.delete') {
  await gapi(token,'DELETE',`${base}/${body.taskId}`);
  result = {deleted:true};
} else { throw new Error('Unknown op: '+op); }
return [{json:{success:true,data:result}}];
"""

CONTACTS_JS = SA_AUTH_JS + r"""
const body = $input.first().json.body || $input.first().json;
const op = body.operation;
const fields = 'names,emailAddresses,phoneNumbers,organizations,nicknames';
const base = 'https://people.googleapis.com/v1';
const token = await getGoogleToken('https://www.googleapis.com/auth/contacts');
let result;
if(op==='contacts.list') {
  result = await gapi(token,'GET',`${base}/people/me/connections`,null,{personFields:fields,pageSize:body.maxResults||1000});
} else if(op==='contacts.search') {
  result = await gapi(token,'GET',`${base}/people:searchContacts`,null,{query:body.query,readMask:fields});
} else if(op==='contacts.get') {
  result = await gapi(token,'GET',`${base}/${body.resourceName}`,null,{personFields:fields});
} else if(op==='contacts.create') {
  result = await gapi(token,'POST',`${base}/people:createContact`,body.contactBody,{personFields:fields});
} else { throw new Error('Unknown op: '+op); }
return [{json:{success:true,data:result}}];
"""

SERVICES = {
    'hermes-sheets':   SHEETS_JS,
    'hermes-gmail':    GMAIL_JS,
    'hermes-calendar': CALENDAR_JS,
    'hermes-docs':     DOCS_JS,
    'hermes-tasks':    TASKS_JS,
    'hermes-contacts': CONTACTS_JS,
}

def make_workflow(name, js_code):
    w1, w2, w3 = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    return {
        "name": name,
        "nodes": [
            {"id": w1, "name": "Webhook", "type": "n8n-nodes-base.webhook",
             "typeVersion": 2, "position": [240, 300],
             "parameters": {"httpMethod": "POST", "path": name,
                            "responseMode": "responseNode", "options": {}},
             "webhookId": name},
            {"id": w2, "name": "Run", "type": "n8n-nodes-base.code",
             "typeVersion": 2, "position": [460, 300],
             "parameters": {"jsCode": js_code, "mode": "runOnceForAllItems"}},
            {"id": w3, "name": "Respond", "type": "n8n-nodes-base.respondToWebhook",
             "typeVersion": 1.1, "position": [680, 300],
             "parameters": {"respondWith": "json", "responseBody": "={{ $json }}",
                            "options": {}}}
        ],
        "connections": {
            "Webhook": {"main": [[{"node": "Run", "type": "main", "index": 0}]]},
            "Run":     {"main": [[{"node": "Respond", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1"},
    }

def post_workflow(wf):
    data = json.dumps(wf).encode()
    req = urllib.request.Request(
        f'{BASE_URL}/api/v1/workflows', data=data,
        headers={'X-N8N-API-KEY': NEW_TOKEN, 'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read())
            return resp.get('id'), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:400]

print("Creating N8N workflows...")
for name, code in SERVICES.items():
    wf = make_workflow(name, code)
    wid, err = post_workflow(wf)
    if err:
        print(f"  FAIL {name}: {err[:150]}")
    else:
        print(f"  OK   {name}  id={wid}")
print("Done.")
