const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const WebSocket = require('ws');
const qrcode = require('qrcode-terminal');
const pino = require('pino');
const path = require('path');
const fs = require('fs');

const PORT = process.env.BRIDGE_PORT || 3001;
const AUTH_DIR = process.env.AUTH_DIR || path.join(__dirname, 'auth');
const BRIDGE_TOKEN = process.env.BRIDGE_TOKEN || '';

const logger = pino({ level: 'silent' });

// Global Python client and WhatsApp socket references
let pyClient = null;
let sock = null;
const sentMessageIds = new Set();

function normalizeJid(jid) {
    if (!jid) return jid;
    if (jid.includes('@')) {
        const [user, domain] = jid.split('@');
        return `${user.split(':')[0]}@${domain}`;
    }
    return jid.split(':')[0];
}


// Start WebSocket Server once
const wss = new WebSocket.Server({ port: PORT, host: '127.0.0.1' });
console.log(`WebSocket bridge server listening on ws://127.0.0.1:${PORT}`);

wss.on('connection', (ws, req) => {
    console.log("Python client connected to bridge.");
    pyClient = ws;

    ws.on('message', async (message) => {
        try {
            const data = JSON.parse(message);
            
            if (data.type === 'auth') {
                if (data.token !== BRIDGE_TOKEN) {
                    console.error("Authentication failed: Invalid token");
                    ws.send(JSON.stringify({ type: 'error', message: 'Unauthorized' }));
                    ws.close();
                } else {
                    console.log("Python client authenticated successfully.");
                    ws.send(JSON.stringify({ type: 'authenticated' }));
                }
                return;
            }

            if (data.type === 'send') {
                const { to, text } = data;
                if (sock) {
                    console.log(`Sending message to ${to}: ${text}`);
                    const sentMsg = await sock.sendMessage(to, { text });
                    if (sentMsg && sentMsg.key && sentMsg.key.id) {
                        sentMessageIds.add(sentMsg.key.id);
                    }
                } else {
                    console.error("Cannot send message: WhatsApp socket not initialized.");
                }
            }
        } catch (err) {
            console.error("Error processing message from python client:", err);
        }
    });

    ws.on('close', () => {
        console.log("Python client disconnected.");
        pyClient = null;
    });
});

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    
    sock = makeWASocket({
        auth: state,
        logger,
        printQRInTerminal: false
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            console.log("📱 Scan this QR code with WhatsApp (Linked Devices):");
            qrcode.generate(qr, { small: true });
            
            if (pyClient) {
                pyClient.send(JSON.stringify({ type: 'qr', qr }));
            }
        }

        if (connection === 'close') {
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const shouldReconnect = statusCode !== DisconnectReason.loggedOut && statusCode !== 401 && statusCode !== 403;
            console.log('Connection closed due to ', lastDisconnect?.error, ', reconnecting ', shouldReconnect);
            if (shouldReconnect) {
                connectToWhatsApp();
            } else {
                console.log('Credentials expired or logged out. Scheduling auth directory cleanup to force a new QR code...');
                // Wait for Baileys to release file handles before deleting
                setTimeout(() => {
                    try {
                        if (fs.existsSync(AUTH_DIR)) {
                            fs.rmSync(AUTH_DIR, { recursive: true, force: true });
                            console.log('Auth directory cleaned up successfully.');
                        }
                    } catch (e) {
                        console.error("Failed to delete auth directory (files may still be locked by the OS):", e.message);
                        console.log("Please manually delete the folder:", AUTH_DIR);
                    }
                    connectToWhatsApp();
                }, 1500);
            }
        } else if (connection === 'open') {
            console.log('Connected to WhatsApp Web via Baileys!');
            if (pyClient) {
                pyClient.send(JSON.stringify({ type: 'connected' }));
            }
        }
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('messages.upsert', async (m) => {
        console.log(`[Diagnostic] messages.upsert received, type: ${m.type}, count: ${m.messages?.length}`);
        if (m.type === 'notify') {
            for (const msg of m.messages) {
                console.log(`[Diagnostic] message details: key=${JSON.stringify(msg.key)}, hasMessage=${!!msg.message}`);
                if (!msg.message) continue;

                const messageId = msg.key.id;

                // Ignore messages sent by the bot itself
                if (sentMessageIds.has(messageId)) {
                    console.log(`[Diagnostic] Ignoring message sent by bot itself: ${messageId}`);
                    sentMessageIds.delete(messageId);
                    continue;
                }

                const sender = msg.key.remoteJid;
                const isFromMe = msg.key.fromMe;

                const myJid = sock.user ? normalizeJid(sock.user.id) : null;
                const myLid = sock.user && sock.user.lid ? normalizeJid(sock.user.lid) : null;
                const normSender = normalizeJid(sender);
                const normSenderAlt = msg.key.remoteJidAlt ? normalizeJid(msg.key.remoteJidAlt) : null;

                const isSelf = (myJid && (normSender === myJid || normSenderAlt === myJid)) || 
                               (myLid && normSender === myLid);

                console.log(`[Diagnostic] Filter check: myJid=${myJid}, myLid=${myLid}, sender=${sender}, normSender=${normSender}, normSenderAlt=${normSenderAlt}, isFromMe=${isFromMe}, isSelf=${isSelf}`);

                // Process the message if it is not from me,
                // OR if it is from me in the "Message Yourself" self-chat
                if (!isFromMe || isSelf) {
                    const text = msg.message.conversation || 
                                 msg.message.extendedTextMessage?.text || 
                                 msg.message.imageMessage?.caption || "";
                    
                    const senderName = msg.pushName || (isSelf ? "You" : sender.split('@')[0]);

                    console.log(`Received message from ${senderName} (${sender}): ${text}`);

                    if (pyClient) {
                        pyClient.send(JSON.stringify({
                            type: 'message',
                            id: messageId,
                            sender: sender,
                            senderName: senderName,
                            text: text,
                            timestamp: msg.messageTimestamp
                        }));
                    }
                }
            }
        }
    });
}

connectToWhatsApp().catch(err => {
    console.error("Error starting WhatsApp client:", err);
});

