const express = require('express');
const path = require('path');
const http = require('http');
const https = require('https');
const net = require('net');
const { URL } = require('url');
const fs = require('fs-extra');
const session = require('express-session');
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;

const app = express();
const PORT = process.env.PORT || 3000;
const AUTH_FILE = process.env.AUTH_FILE || path.join(__dirname, '.auth');

// Trust proxy for Railway/nginx (HTTPS behind proxy)
app.set('trust proxy', 1);

// Environment variables
const ASSEMBLYAI_API_KEY_FALLBACK = process.env.ASSEMBLYAI_API_KEY;
const SAVE_WEBHOOK_URL = process.env.SAVE_WEBHOOK_URL;
const WHATSAPP_WEBHOOK_URL = process.env.WHATSAPP_WEBHOOK_URL;
const CLEANTEXT_WEBHOOK_URL = process.env.CLEANTEXT_WEBHOOK_URL;
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const GWS_VAULT_SOCKET = process.env.GWS_VAULT_SOCKET;
const GWS_VAULT_SECRET = process.env.GWS_VAULT_SECRET;
const VOCAB_SERVICE = 'vocab';
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
const SESSION_SECRET = process.env.SESSION_SECRET || 'voice-transcription-secret';
// Free Whisper microservice (isolated faster-whisper container) — reachable
// by compose service name on the shared internal docker network. Same
// pattern as OPENAI_API_BASE_URL: http://hermes:8642/v1 used elsewhere.
const FREE_WHISPER_URL = process.env.FREE_WHISPER_URL || 'http://free-whisper:8000';

// ---------------------------------------------------------------------------
// GWS Vault client (Unix socket, NDJSON protocol)
// ---------------------------------------------------------------------------
function vaultRequest(op, payload) {
  return new Promise((resolve, reject) => {
    if (!GWS_VAULT_SOCKET) return reject(new Error('GWS_VAULT_SOCKET not set'));
    const reqObj = JSON.stringify({ op, ...payload }) + '\n';
    const client = net.createConnection(GWS_VAULT_SOCKET, () => {
      client.write(reqObj);
    });
    let buf = '';
    client.on('data', (chunk) => { buf += chunk.toString(); });
    client.on('end', () => {
      try {
        const lines = buf.trim().split('\n').filter(Boolean);
        const last = JSON.parse(lines[lines.length - 1] || '{}');
        if (last.ok === false) reject(new Error(last.error || 'vault error'));
        else resolve(last);
      } catch (e) { reject(new Error('vault parse error: ' + e.message)); }
    });
    client.on('error', reject);
  });
}

async function resolveUser(email) {
  const resp = await vaultRequest('resolve', { identity_type: 'email', identity_value: email });
  return resp.user_id;
}

async function getVocab(userId) {
  const resp = await vaultRequest('get', { user_id: userId, service: VOCAB_SERVICE, session_uid: userId });
  if (!resp.token_json) return [];
  let data;
  try { data = JSON.parse(resp.token_json); } catch (e) { return []; }
  if (Array.isArray(data)) return data.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
  if (typeof data === 'object' && data !== null) return Object.values(data).map((v) => typeof v === 'object' ? v.word || v : String(v));
  return [];
}

async function setVocab(userId, terms) {
  const cleaned = [...new Set(terms.map((t) => t.trim()).filter(Boolean))].sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
  await vaultRequest('set', { user_id: userId, service: VOCAB_SERVICE, token_json: JSON.stringify(cleaned), vault_secret: GWS_VAULT_SECRET });
  return cleaned;
}

// ---------------------------------------------------------------------------
// Middleware
// ---------------------------------------------------------------------------
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true }));

// Session management - 2 weeks persistent cookie
app.use(session({
  secret: SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    maxAge: 14 * 24 * 60 * 60 * 1000, // 14 days
    secure: true, // Always true with trust proxy set
    httpOnly: true,
    sameSite: 'lax'
  }
}));

app.use(passport.initialize());
app.use(passport.session());

// Passport Google Strategy
passport.use(new GoogleStrategy({
    clientID: GOOGLE_CLIENT_ID,
    clientSecret: GOOGLE_CLIENT_SECRET,
    callbackURL: "/auth/callback",
    proxy: true
  },
  async (accessToken, refreshToken, profile, done) => {
    const email = profile.emails[0].value;
    try {
      const authData = await fs.readJson(AUTH_FILE);
      const user = authData.users[email];

      if (user && user.authorized) {
        return done(null, {
          email,
          name: user.name || profile.displayName,
          assemblyai_key: user.assemblyai_key
        });
      } else {
        return done(null, false, { message: 'Unauthorized' });
      }
    } catch (err) {
      console.error('[AUTH] Error reading .auth file:', err.message);
      return done(null, false, { message: 'Auth file error' });
    }
  }
));

passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser(async (user, done) => {
  try {
    const authData = await fs.readJson(AUTH_FILE);
    const latestUser = authData.users[user.email];
    if (latestUser && latestUser.authorized) {
      user.assemblyai_key = latestUser.assemblyai_key;
    }
  } catch (err) {
    console.log('[DESERIALIZE] Error reading .auth file:', err.message);
  }
  done(null, user);
});

// Auth Middleware
const isAuthenticated = (req, res, next) => {
  if (req.isAuthenticated()) return next();
  res.redirect('/login');
};

const isAuthenticatedApi = (req, res, next) => {
  if (req.isAuthenticated()) return next();
  res.status(401).json({ error: 'Unauthorized' });
};

// --- Auth Routes ---

app.get('/login', (req, res) => {
  if (req.isAuthenticated()) return res.redirect('/');
  res.send(`
    <html>
      <head>
        <title>Login - Voice Transcription</title>
        <style>
          body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; }
          .card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
          .btn { background: #4361ee; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 1rem; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1>Voice Transcription</h1>
          <p>Please sign in with your Google account to continue.</p>
          <a href="/auth/google" class="btn">Sign in with Google</a>
        </div>
      </body>
    </html>
  `);
});

app.get('/auth/google', passport.authenticate('google', { scope: ['profile', 'email'] }));

app.get('/auth/callback',
  passport.authenticate('google', { failureRedirect: '/unauthorized' }),
  (req, res) => res.redirect('/')
);

app.get('/unauthorized', (req, res) => {
  res.status(403).send(`
    <html>
      <head><title>Unauthorized</title></head>
      <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
        <h1>Access Denied</h1>
        <p>Your email is not authorized to access this application.</p>
        <p>Please contact the administrator for access.</p>
        <a href="/login">Back to Login</a>
      </body>
    </html>
  `);
});

app.get('/setup-key', (req, res) => {
  if (!req.isAuthenticated()) return res.redirect('/login');
  if (req.user.assemblyai_key) return res.redirect('/');

  res.send(`
    <html>
      <head>
        <title>Setup AssemblyAI Key</title>
        <style>
          body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; }
          .card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 400px; }
          input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
          button { background: #4361ee; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%; }
        </style>
      </head>
      <body>
        <div class="card">
          <h2>AssemblyAI API Key Required</h2>
          <p>Please enter your AssemblyAI API key to continue.</p>
          <form action="/setup-key" method="POST">
            <input type="text" name="apiKey" placeholder="Your AssemblyAI Key" required />
            <button type="submit">Save and Continue</button>
          </form>
        </div>
      </body>
    </html>
  `);
});

app.post('/setup-key', async (req, res) => {
  if (!req.isAuthenticated()) return res.status(401).send('Unauthorized');
  const { apiKey } = req.body;
  if (!apiKey) return res.status(400).send('API Key is required');

  try {
    const authData = await fs.readJson(AUTH_FILE);
    if (authData.users[req.user.email]) {
      authData.users[req.user.email].assemblyai_key = apiKey;
      await fs.writeJson(AUTH_FILE, authData, { spaces: 2 });
      req.user.assemblyai_key = apiKey;
      req.session.save((err) => {
        if (err) return res.status(500).send('Error saving session');
        res.redirect('/');
      });
    } else {
      res.status(403).send('User not found in auth file');
    }
  } catch (err) {
    res.status(500).send('Error saving API key');
  }
});

app.get('/logout', (req, res, next) => {
  req.logout((err) => {
    if (err) return next(err);
    res.redirect('/login');
  });
});

// Admin endpoint to add authorized emails
app.get('/admin/add-user', async (req, res) => {
  const { email, name } = req.query;
  if (!email) return res.status(400).send('Email query param required');

  try {
    const authData = await fs.readJson(AUTH_FILE);
    authData.users[email] = {
      assemblyai_key: null,
      name: name || email.split('@')[0],
      authorized: true
    };
    await fs.writeJson(AUTH_FILE, authData, { spaces: 2 });
    res.send(`User ${email} added successfully.`);
  } catch (err) {
    res.status(500).send('Error adding user');
  }
});

// --- API Proxy Helpers ---

function proxyRequest(targetUrl, method, headers, body) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(targetUrl);
    const lib = parsed.protocol === 'https:' ? https : http;

    const options = {
      hostname: parsed.hostname,
      port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
      path: parsed.pathname + parsed.search,
      method: method,
      headers: headers,
    };

    const req = lib.request(options, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => {
        const buffer = Buffer.concat(chunks);
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: buffer,
        });
      });
    });

    req.on('error', (err) => reject(err));
    req.setTimeout(300000, () => req.destroy(new Error('Request timed out')));

    if (body) req.write(body);
    req.end();
  });
}

// --- Protected API Routes ---

app.get('/api/user-info', isAuthenticatedApi, async (req, res) => {
  try {
    const authData = await fs.readJson(AUTH_FILE);
    const userData = authData.users[req.user.email];
    const actualKey = (userData && userData.assemblyai_key) || req.user.assemblyai_key || null;

    let apiKeyMasked = null;
    if (actualKey) {
      apiKeyMasked = actualKey.substring(0, 6) + '...' + actualKey.substring(actualKey.length - 4);
    }

    const response = {
      email: req.user.email,
      name: req.user.name,
      apiKeyMasked: apiKeyMasked,
      hasKey: !!actualKey
    };

    if (req.query.showKey === 'true') {
      response.apiKey = actualKey;
    }

    res.json(response);
  } catch (err) {
    res.status(500).json({ error: 'Failed to load user info' });
  }
});

app.post('/api/update-key', isAuthenticatedApi, async (req, res) => {
  try {
    const { apiKey } = req.body;
    if (!apiKey || !apiKey.trim()) {
      return res.status(400).json({ error: 'API key is required' });
    }

    const authData = await fs.readJson(AUTH_FILE);
    if (!authData.users[req.user.email]) {
      return res.status(403).json({ error: 'User not found in auth file' });
    }

    authData.users[req.user.email].assemblyai_key = apiKey.trim();
    await fs.writeJson(AUTH_FILE, authData, { spaces: 2 });

    req.user.assemblyai_key = apiKey.trim();
    req.session.save((err) => {
      if (err) return res.status(500).json({ error: 'Failed to persist session' });
      res.json({ success: true, message: 'API key updated successfully' });
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to update API key' });
  }
});

app.post('/api/assemblyai/upload', isAuthenticated, async (req, res) => {
  try {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', async () => {
      try {
        const audioBuffer = Buffer.concat(chunks);
        const result = await proxyRequest(
          'https://api.assemblyai.com/v2/upload',
          'POST',
          {
            'Authorization': req.user.assemblyai_key || ASSEMBLYAI_API_KEY_FALLBACK,
            'Content-Type': 'application/octet-stream',
            'Content-Length': audioBuffer.length,
          },
          audioBuffer
        );
        res.status(result.status).set('Content-Type', 'application/json').send(result.body);
      } catch (err) {
        res.status(502).json({ error: 'Upload proxy failed: ' + err.message });
      }
    });
  } catch (err) {
    res.status(502).json({ error: 'Upload proxy failed: ' + err.message });
  }
});

app.post('/api/assemblyai/transcript', isAuthenticated, async (req, res) => {
  try {
    const bodyStr = JSON.stringify(req.body);
    const userEmail = req.user.email || 'unknown';
    const keyUsed = req.user.assemblyai_key ? 'user-key' : 'fallback-key';
    console.log(`[TRANSCRIPT] User: ${userEmail}, Key: ${keyUsed}`);
    console.log(`[TRANSCRIPT] Request body: ${bodyStr}`);
    const result = await proxyRequest(
      'https://api.assemblyai.com/v2/transcript',
      'POST',
      {
        'Authorization': req.user.assemblyai_key || ASSEMBLYAI_API_KEY_FALLBACK,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(bodyStr),
      },
      bodyStr
    );
    console.log(`[TRANSCRIPT] Response status: ${result.status}`);
    if (result.status !== 200) {
      console.log(`[TRANSCRIPT] Error response: ${result.body}`);
    }
    res.status(result.status).set('Content-Type', 'application/json').send(result.body);
  } catch (err) {
    console.log(`[TRANSCRIPT] Exception: ${err.message}`);
    res.status(502).json({ error: 'Transcript proxy failed: ' + err.message });
  }
});

app.get('/api/assemblyai/transcript/:id', isAuthenticated, async (req, res) => {
  try {
    const result = await proxyRequest(
      `https://api.assemblyai.com/v2/transcript/${req.params.id}`,
      'GET',
      {
        'Authorization': req.user.assemblyai_key || ASSEMBLYAI_API_KEY_FALLBACK,
      },
      null
    );
    res.status(result.status).set('Content-Type', 'application/json').send(result.body);
  } catch (err) {
    res.status(502).json({ error: 'Transcript status proxy failed: ' + err.message });
  }
});

// Free Whisper — proxies raw recorded/uploaded audio to the isolated
// free-whisper-svc container (faster-whisper, self-hosted, no API key,
// no per-request cost). Mirrors the AssemblyAI upload route above but is
// a single request/response — no async job polling needed.
app.post('/api/whisper/transcribe', isAuthenticated, async (req, res) => {
  try {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', async () => {
      try {
        const audioBuffer = Buffer.concat(chunks);
        const language = (req.query.language || '').toString();
        const result = await proxyRequest(
          `${FREE_WHISPER_URL}/transcribe`,
          'POST',
          {
            'Content-Type': req.headers['content-type'] || 'application/octet-stream',
            'Content-Length': audioBuffer.length,
            'X-Hermes-User-Email': req.user.email || 'unknown',
            'X-Whisper-Language': language,
          },
          audioBuffer
        );
        res.status(result.status).set('Content-Type', 'application/json').send(result.body);
      } catch (err) {
        res.status(502).json({ success: false, error: 'Free Whisper proxy failed: ' + err.message });
      }
    });
  } catch (err) {
    res.status(502).json({ success: false, error: 'Free Whisper proxy failed: ' + err.message });
  }
});

// ---------------------------------------------------------------------------
// Vocabulary API (per-user, stored in GWS vault)
// ---------------------------------------------------------------------------
app.get('/api/vocab', isAuthenticated, async (req, res) => {
  try {
    const userId = await resolveUser(req.user.email);
    if (!userId) return res.json({ terms: [] });
    const terms = await getVocab(userId);
    const mapped = terms.map((word, i) => ({ id: String(i), word }));
    res.json({ terms: mapped });
  } catch (err) {
    console.error('[VOCAB] get error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/vocab', isAuthenticated, async (req, res) => {
  try {
    const words = req.body.words || (req.body.word ? [req.body.word] : []);
    if (!words.length) return res.status(400).json({ error: 'word or words required' });
    const cleaned = words.map((w) => w.trim()).filter((w) => w.length > 0);
    if (!cleaned.length) return res.status(400).json({ error: 'no valid words provided' });
    const userId = await resolveUser(req.user.email);
    if (!userId) return res.status(500).json({ error: 'user not found' });
    const current = await getVocab(userId);
    const added = [];
    const skipped = [];
    for (const w of cleaned) {
      if (current.includes(w)) { skipped.push(w); }
      else { current.push(w); added.push(w); }
    }
    if (added.length) await setVocab(userId, current);
    res.json({ success: true, added, skipped, count: current.length });
  } catch (err) {
    console.error('[VOCAB] add error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

app.put('/api/vocab/:id', isAuthenticated, async (req, res) => {
  try {
    const { word } = req.body;
    const idx = parseInt(req.params.id, 10);
    if (isNaN(idx) || !word || !word.trim()) return res.status(400).json({ error: 'invalid index or word' });
    const userId = await resolveUser(req.user.email);
    if (!userId) return res.status(500).json({ error: 'user not found' });
    const current = await getVocab(userId);
    if (idx < 0 || idx >= current.length) return res.status(404).json({ error: 'term not found' });
    current[idx] = word.trim();
    await setVocab(userId, current);
    res.json({ success: true });
  } catch (err) {
    console.error('[VOCAB] update error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

app.delete('/api/vocab/:id', isAuthenticated, async (req, res) => {
  try {
    const idx = parseInt(req.params.id, 10);
    if (isNaN(idx)) return res.status(400).json({ error: 'invalid index' });
    const userId = await resolveUser(req.user.email);
    if (!userId) return res.status(500).json({ error: 'user not found' });
    const current = await getVocab(userId);
    if (idx < 0 || idx >= current.length) return res.status(404).json({ error: 'term not found' });
    current.splice(idx, 1);
    await setVocab(userId, current);
    res.json({ success: true });
  } catch (err) {
    console.error('[VOCAB] delete error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ---------------------------------------------------------------------------
// Webhook proxy routes
// ---------------------------------------------------------------------------
app.post('/api/webhook/:type', isAuthenticated, async (req, res) => {
  try {
    const webhookMap = {
      save: SAVE_WEBHOOK_URL,
      whatsapp: WHATSAPP_WEBHOOK_URL,
      cleantext: CLEANTEXT_WEBHOOK_URL,
    };
    const targetUrl = webhookMap[req.params.type];
    if (!targetUrl) return res.status(400).json({ error: 'Unknown webhook type' });

    const body = { ...req.body };
    if (req.params.type === 'whatsapp' || req.params.type === 'cleantext') {
      try {
        const userId = await resolveUser(req.user.email);
        if (userId) {
          const vocab = await getVocab(userId);
          if (vocab.length > 0) body.vocabulary = vocab;
        }
      } catch (vErr) {
        console.error('[WEBHOOK] vocab fetch error (non-fatal):', vErr.message);
      }
    }

    const bodyToSend = JSON.stringify(body);
    const result = await proxyRequest(targetUrl, 'POST', {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(bodyToSend)
    }, bodyToSend);

    const respContentType = result.headers['content-type'] || 'application/json';
    res.status(result.status).set('Content-Type', respContentType).send(result.body);
  } catch (err) {
    res.status(502).json({ error: 'Webhook proxy failed: ' + err.message });
  }
});

app.post('/api/webhook-form/save', isAuthenticated, (req, res) => {
  const chunks = [];
  req.on('data', (chunk) => chunks.push(chunk));
  req.on('end', async () => {
    try {
      const rawBody = Buffer.concat(chunks);
      const result = await proxyRequest(SAVE_WEBHOOK_URL, 'POST', {
        'Content-Type': req.headers['content-type'] || '',
        'Content-Length': rawBody.length,
      }, rawBody);
      const respContentType = result.headers['content-type'] || 'application/json';
      res.status(result.status).set('Content-Type', respContentType).send(result.body);
    } catch (err) {
      res.status(502).json({ error: 'Save webhook proxy failed: ' + err.message });
    }
  });
});

// OpenAI-compatible STT endpoint used by Open WebUI (/v1/audio/transcriptions).
// Accepts multipart/form-data with 'file' (audio binary) + optional 'model' field.
// No auth required -- bound to the internal docker network (open-webui container).
app.post('/v1/audio/transcriptions', async (req, res) => {
  const ctype = req.headers['content-type'] || '';
  const bm = ctype.match(/boundary=(?:"([^"]+)"|([^;]+))/i);
  if (!bm) {
    return res.status(400).json({ error: { message: 'multipart/form-data with boundary required' } });
  }
  const boundary = '--' + (bm[1] || bm[2]).trim();

  const chunks = [];
  req.on('data', (c) => chunks.push(c));
  req.on('end', async () => {
    const t0 = Date.now();
    try {
      const body = Buffer.concat(chunks);
      const parts = splitMultipart(body, boundary);
      const filePart = parts.find((p) => p.name === 'file');
      if (!filePart || !filePart.data || filePart.data.length === 0) {
        return res.status(400).json({ error: { message: "missing or empty 'file' field" } });
      }
      const audioBuffer = filePart.data;
      console.log(`[STT-BRIDGE] received ${audioBuffer.length} bytes, uploading to AssemblyAI`);

      const uploadResp = await proxyRequest(
        'https://api.assemblyai.com/v2/upload',
        'POST',
        {
          Authorization: ASSEMBLYAI_API_KEY_FALLBACK,
          'Content-Type': 'application/octet-stream',
          'Content-Length': audioBuffer.length,
        },
        audioBuffer
      );
      if (uploadResp.status !== 200) {
        return res.status(502).json({
          error: { message: `assemblyai upload failed (${uploadResp.status}): ${uploadResp.body.toString().slice(0, 500)}` },
        });
      }
      const { upload_url } = JSON.parse(uploadResp.body.toString());

      const tReqBody = JSON.stringify({
        audio_url: upload_url,
        speech_models: ['universal-2'],
        language_code: 'en',
      });
      const tResp = await proxyRequest(
        'https://api.assemblyai.com/v2/transcript',
        'POST',
        {
          Authorization: ASSEMBLYAI_API_KEY_FALLBACK,
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(tReqBody),
        },
        tReqBody
      );
      if (tResp.status !== 200) {
        return res.status(502).json({
          error: { message: `assemblyai transcript submit failed (${tResp.status}): ${tResp.body.toString().slice(0, 500)}` },
        });
      }
      const { id } = JSON.parse(tResp.body.toString());
      console.log(`[STT-BRIDGE] submitted transcript id=${id}, polling...`);

      const deadline = Date.now() + 120000;
      let text = null;
      while (Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, 1500));
        const pResp = await proxyRequest(
          `https://api.assemblyai.com/v2/transcript/${id}`,
          'GET',
          { Authorization: ASSEMBLYAI_API_KEY_FALLBACK },
          null
        );
        if (pResp.status !== 200) continue;
        const job = JSON.parse(pResp.body.toString());
        if (job.status === 'completed') { text = job.text; break; }
        if (job.status === 'error') {
          return res.status(502).json({ error: { message: `transcript failed: ${job.error || 'unknown'}` } });
        }
      }
      if (text === null) {
        return res.status(504).json({ error: { message: 'transcript timed out after 120s' } });
      }
      console.log(`[STT-BRIDGE] done in ${Date.now() - t0}ms, ${text.length} chars`);
      res.json({ text });
    } catch (err) {
      console.error(`[STT-BRIDGE] error: ${err.message}`);
      res.status(500).json({ error: { message: err.message } });
    }
  });
  req.on('error', (err) => res.status(500).json({ error: { message: err.message } }));
});

// Minimal multipart/form-data parser. Returns array of {name, data} (Buffer).
function splitMultipart(body, boundary) {
  const boundaryBuf = Buffer.from(boundary);
  const parts = [];
  let pos = 0;
  while (pos < body.length) {
    const start = body.indexOf(boundaryBuf, pos);
    if (start === -1) break;
    pos = start + boundaryBuf.length;
    if (body.slice(pos, pos + 2).toString() === '--') break; // closing boundary
    if (body.slice(pos, pos + 2).toString() === '\r\n') pos += 2;
    const headerEnd = body.indexOf('\r\n\r\n', pos);
    if (headerEnd === -1) break;
    const headerText = body.slice(pos, headerEnd).toString();
    pos = headerEnd + 4;
    const next = body.indexOf(boundaryBuf, pos);
    let dataEnd = next === -1 ? body.length : next - 2;
    if (dataEnd < pos) dataEnd = pos;
    const data = body.slice(pos, dataEnd);
    const cdMatch = headerText.match(/name="([^"]+)"/i);
    parts.push({ name: cdMatch ? cdMatch[1] : '', data });
    pos = next === -1 ? body.length : next;
  }
  return parts;
}

// Serve the main HTML page - PROTECTED (must be BEFORE static middleware)
app.get('/', isAuthenticated, (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'index.html'));
});

// Static files (CSS, JS assets) - MUST be AFTER protected routes
app.use(express.static(path.join(__dirname, 'public')));

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Voice Transcription Tool server running on port ${PORT}`);
});
