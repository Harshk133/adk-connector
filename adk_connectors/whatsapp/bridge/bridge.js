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
                    await sock.sendMessage(to, { text });
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
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('Connection closed due to ', lastDisconnect?.error, ', reconnecting ', shouldReconnect);
            if (shouldReconnect) {
                connectToWhatsApp();
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
        if (m.type === 'notify') {
            for (const msg of m.messages) {
                if (!msg.key.fromMe && msg.message) {
                    const sender = msg.key.remoteJid;
                    const text = msg.message.conversation || 
                                 msg.message.extendedTextMessage?.text || 
                                 msg.message.imageMessage?.caption || "";
                    
                    const messageId = msg.key.id;
                    const senderName = msg.pushName || sender.split('@')[0];

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

