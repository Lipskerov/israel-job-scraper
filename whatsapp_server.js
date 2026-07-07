#!/usr/bin/env node
/**
 * WhatsApp bridge server for the Israel Job Scraper Streamlit app.
 * Wraps whatsapp-web.js behind a simple HTTP API on localhost:8765.
 *
 * Endpoints:
 *   GET  /status       → { status, qr }
 *   GET  /connect      → start client initialisation
 *   GET  /groups       → [{ id, name, participants }]
 *   GET  /messages     → ?chat_id=...&limit=200  → [{ id, body, author, timestamp }]
 *   POST /disconnect   → logout + destroy
 */

const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const QRCode = require('qrcode');
const path = require('path');

const PORT = 8765;
const AUTH_DIR = path.join(__dirname, '.wwebjs_auth');

const app = express();
app.use(express.json());

let waClient = null;
let currentQR = null;           // base64 PNG data URL
let connStatus = 'disconnected'; // 'disconnected' | 'initializing' | 'qr_pending' | 'connected'

// ─── Client factory ───────────────────────────────────────────────────────────

function createClient() {
    const c = new Client({
        authStrategy: new LocalAuth({ dataPath: AUTH_DIR }),
        puppeteer: {
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
        },
    });

    c.on('qr', async (qr) => {
        connStatus = 'qr_pending';
        currentQR = await QRCode.toDataURL(qr);
        console.log('[WA] QR ready — scan with WhatsApp');
    });

    c.on('authenticated', () => {
        console.log('[WA] Authenticated');
        currentQR = null;
    });

    c.on('ready', () => {
        connStatus = 'connected';
        currentQR = null;
        console.log('[WA] Client ready');
    });

    c.on('disconnected', (reason) => {
        console.log('[WA] Disconnected:', reason);
        connStatus = 'disconnected';
        currentQR = null;
        waClient = null;
    });

    c.on('auth_failure', (msg) => {
        console.error('[WA] Auth failure:', msg);
        connStatus = 'disconnected';
        waClient = null;
    });

    return c;
}

// ─── Routes ───────────────────────────────────────────────────────────────────

app.get('/status', (_req, res) => {
    res.json({ status: connStatus, qr: currentQR });
});

app.get('/connect', (_req, res) => {
    if (connStatus === 'connected') {
        return res.json({ status: 'already_connected' });
    }
    if (connStatus === 'initializing' || connStatus === 'qr_pending') {
        return res.json({ status: connStatus, qr: currentQR });
    }
    connStatus = 'initializing';
    waClient = createClient();
    waClient.initialize().catch((err) => {
        console.error('[WA] Init error:', err.message);
        connStatus = 'disconnected';
        waClient = null;
    });
    res.json({ status: 'initializing' });
});

app.get('/groups', async (_req, res) => {
    if (connStatus !== 'connected' || !waClient) {
        return res.status(400).json({ error: 'Not connected' });
    }

    const timer = setTimeout(() => {
        if (!res.headersSent) res.status(504).json({ error: 'Timed out loading groups — try again' });
    }, 50000);

    try {
        const chats = await waClient.getChats();
        clearTimeout(timer);
        if (res.headersSent) return;

        const groups = chats
            .filter(c => c.isGroup)
            .map(c => ({
                id: c.id._serialized,
                name: c.name || '(unnamed)',
                participants: Array.isArray(c.groupMetadata?.participants)
                    ? c.groupMetadata.participants.length
                    : 0,
            }))
            .sort((a, b) => a.name.localeCompare(b.name));
        res.json(groups);
    } catch (e) {
        clearTimeout(timer);
        if (res.headersSent) return;

        // Detached frame = browser was killed; reset so UI can reconnect cleanly
        if (e.message && e.message.includes('detached Frame')) {
            console.log('[WA] Detached frame detected — resetting client');
            try { await waClient.destroy(); } catch {}
            waClient = null;
            connStatus = 'disconnected';
            return res.status(503).json({ error: 'DETACHED_FRAME' });
        }
        res.status(500).json({ error: e.message });
    }
});

app.get('/messages', async (req, res) => {
    if (connStatus !== 'connected' || !waClient) {
        return res.status(400).json({ error: 'Not connected' });
    }
    const { chat_id, limit = '200' } = req.query;
    if (!chat_id) return res.status(400).json({ error: 'chat_id required' });

    try {
        const chat = await waClient.getChatById(chat_id);
        const messages = await chat.fetchMessages({ limit: parseInt(limit, 10) });

        const result = [];
        for (const m of messages) {
            const body = (m.body || '').trim();
            if (body.length < 20) continue;

            // Resolve author display name
            let author = '';
            try {
                const contact = await m.getContact();
                author = contact.pushname || contact.name || contact.number || m.author || '';
            } catch {
                author = m.author || '';
            }

            // Deep link (wa.me can't link to specific message; use group name slug)
            const groupSlug = encodeURIComponent(chat.name || chat_id);

            result.push({
                id: m.id._serialized,
                body,
                author,
                timestamp: m.timestamp,
                date_str: new Date(m.timestamp * 1000).toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
                source_url: `https://wa.me/${chat.id.user}`,
            });
        }
        res.json(result);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/disconnect', async (_req, res) => {
    if (waClient) {
        try { await waClient.logout(); } catch {}
        try { await waClient.destroy(); } catch {}
        waClient = null;
    }
    connStatus = 'disconnected';
    currentQR = null;
    res.json({ status: 'disconnected' });
});

// ─── Start ────────────────────────────────────────────────────────────────────

app.listen(PORT, '127.0.0.1', () => {
    console.log(`[WA] Bridge server listening on http://127.0.0.1:${PORT}`);
});
