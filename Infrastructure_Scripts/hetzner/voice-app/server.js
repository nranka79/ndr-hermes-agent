const express = require('express');
const path = require('path');
const http = require('http');
const https = require('https');
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
const PROCESS_WEBHOOK_URL = process.env.PROCESS_WEBHOOK_URL;
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
const SESSION_SECRET = process.env.SESSION_SECRET || 'voice-transcription-secret';

// Middleware
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

app.post('/api/webhook/:type', isAuthenticated, async (req, res) => {
  try {
    const webhookMap = {
      save: SAVE_WEBHOOK_URL,
      whatsapp: WHATSAPP_WEBHOOK_URL,
      cleantext: CLEANTEXT_WEBHOOK_URL,
      process: PROCESS_WEBHOOK_URL,
    };
    const targetUrl = webhookMap[req.params.type];
    if (!targetUrl) return res.status(400).json({ error: 'Unknown webhook type' });

    const bodyToSend = JSON.stringify(req.body);
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

// Serve the main HTML page - PROTECTED (must be BEFORE static middleware)
app.get('/', isAuthenticated, (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'index.html'));
});

// Static files (CSS, JS assets) - MUST be AFTER protected routes
app.use(express.static(path.join(__dirname, 'public')));

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Voice Transcription Tool server running on port ${PORT}`);
});
