export const config = {
  api: {
    bodyParser: {
      sizeLimit: '4.5mb',
    },
  },
};

const ALLOWED_METHODS = new Set(['sendMessage', 'answerCallbackQuery', 'getUpdates']);

export default async function handler(req, res) {
  // Add CORS headers just in case
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const {
      bot_token,
      method,
      chat_id,
      text,
      parse_mode,
      reply_markup,
      voice_base64,
      caption,
      filename,
      callback_query_id,
      show_alert,
      offset,
      timeout,
      limit,
    } = req.body || {};

    if (!bot_token) {
      return res.status(400).json({ error: 'Missing bot_token' });
    }

    // 1. Voice bubble upload (sendVoice)
    if (voice_base64) {
      if (!chat_id) {
        return res.status(400).json({ error: 'Missing chat_id' });
      }
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

      const response = await fetch(url, { method: 'POST', body: formData });
      const data = await response.json();
      return res.status(response.status).json(data);
    }

    // 2. Allowlisted Telegram Bot API methods (sendMessage, answerCallbackQuery, getUpdates)
    const targetMethod = method || 'sendMessage';
    if (!ALLOWED_METHODS.has(targetMethod)) {
      return res.status(400).json({ error: `Unsupported Telegram method: ${targetMethod}` });
    }

    let forwardPayload = {};
    if (targetMethod === 'sendMessage') {
      if (!chat_id || !text) {
        return res.status(400).json({ error: 'Missing chat_id or text' });
      }
      forwardPayload = { chat_id, text };
      if (parse_mode) forwardPayload.parse_mode = parse_mode;
      if (reply_markup) forwardPayload.reply_markup = reply_markup;
    } else if (targetMethod === 'answerCallbackQuery') {
      if (!callback_query_id) {
        return res.status(400).json({ error: 'Missing callback_query_id' });
      }
      forwardPayload = { callback_query_id };
      if (text) forwardPayload.text = text;
      if (typeof show_alert === 'boolean') forwardPayload.show_alert = show_alert;
    } else if (targetMethod === 'getUpdates') {
      if (typeof offset === 'number') forwardPayload.offset = offset;
      if (typeof timeout === 'number') forwardPayload.timeout = timeout;
      if (typeof limit === 'number') forwardPayload.limit = limit;
    }

    const url = `https://api.telegram.org/bot${bot_token}/${targetMethod}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(forwardPayload),
    });

    const data = await response.json();
    return res.status(response.status).json(data);
  } catch (error) {
    console.error('[Vercel Proxy] Error forwarding to Telegram:', error);
    return res.status(500).json({ error: error.message || 'Internal Server Error' });
  }
}
