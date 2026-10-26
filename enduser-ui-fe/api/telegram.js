export const config = {
  api: {
    bodyParser: {
      sizeLimit: '4.5mb',
    },
  },
};

export default async function handler(req, res) {
  // Add CORS headers just in case
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { bot_token, chat_id, text, parse_mode, voice_base64, caption, filename } = req.body || {};

    if (!bot_token || !chat_id) {
      return res.status(400).json({ error: 'Missing parameters' });
    }

    if (voice_base64) {
      const url = `https://api.telegram.org/bot${bot_token}/sendVoice`;
      const audioBuffer = Buffer.from(voice_base64, 'base64');
      const formData = new FormData();
      formData.append('chat_id', String(chat_id));
      if (caption) {
        formData.append('caption', String(caption));
      }
      if (parse_mode) {
        formData.append('parse_mode', String(parse_mode));
      }
      const blob = new Blob([audioBuffer], { type: 'audio/wav' });
      formData.append('voice', blob, filename || 'briefing.wav');

      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      return res.status(response.status).json(data);
    }

    if (!text) {
      return res.status(400).json({ error: 'Missing parameters' });
    }

    const url = `https://api.telegram.org/bot${bot_token}/sendMessage`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id, text, parse_mode })
    });
    
    const data = await response.json();
    return res.status(response.status).json(data);
  } catch (error) {
    console.error("[Vercel Proxy] Error forwarding to Telegram:", error);
    return res.status(500).json({ error: error.message || 'Internal Server Error' });
  }
}
