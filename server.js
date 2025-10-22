import { createServer } from 'http';
import { stat } from 'fs/promises';
import { createReadStream } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const PORT = process.env.PORT || 3000;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PUBLIC_DIR = path.join(__dirname, 'public');

const raffles = [
  {
    id: 'r1',
    name: 'Dream Vacation Giveaway',
    description: 'Win a 7-night stay at a luxury resort.',
    prize: '7-night resort stay',
    odds: 2.5,
    deadline: new Date(Date.now() + 1000 * 60 * 60 * 24 * 2).toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'r2',
    name: 'Electric Bike Bonanza',
    description: 'Get a brand-new electric bike delivered to your door.',
    prize: 'Electric bike',
    odds: 5.8,
    deadline: new Date(Date.now() + 1000 * 60 * 60 * 6).toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'r3',
    name: 'Gourmet Cooking Kit',
    description: 'Premium cookware and ingredients for aspiring chefs.',
    prize: 'Cooking kit',
    odds: 12.2,
    deadline: new Date(Date.now() + 1000 * 60 * 60 * 48).toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'r4',
    name: 'Concert VIP Experience',
    description: 'Two VIP tickets to your favorite artist with backstage access.',
    prize: 'VIP concert tickets',
    odds: 1.6,
    deadline: new Date(Date.now() + 1000 * 60 * 60 * 1.5).toISOString(),
    updatedAt: new Date().toISOString()
  }
];

function randomizeRaffles() {
  raffles.forEach((raffle) => {
    const oddsShift = (Math.random() - 0.5) * 0.6;
    const newOdds = Math.max(0.5, +(raffle.odds + oddsShift).toFixed(2));
    raffle.odds = newOdds;

    const deadlineShift = Math.floor((Math.random() - 0.5) * 60 * 60 * 1000);
    const newDeadline = new Date(new Date(raffle.deadline).getTime() + deadlineShift);
    raffle.deadline = newDeadline.toISOString();
    raffle.updatedAt = new Date().toISOString();
  });
}

setInterval(randomizeRaffles, 15000);

function respondJson(res, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(body)
  });
  res.end(body);
}

function handleApiRequest(url, res) {
  if (url.pathname !== '/api/raffles') {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
    return;
  }

  const { searchParams } = url;
  const sort = searchParams.get('sort');
  const maxOddsParam = searchParams.get('max_odds');
  const endsBeforeParam = searchParams.get('ends_before');

  let result = [...raffles];

  if (maxOddsParam) {
    const maxOddsNumber = Number(maxOddsParam);
    if (!Number.isNaN(maxOddsNumber)) {
      result = result.filter((raffle) => raffle.odds <= maxOddsNumber);
    }
  }

  if (endsBeforeParam) {
    const endsBeforeDate = new Date(endsBeforeParam);
    if (!Number.isNaN(endsBeforeDate.getTime())) {
      result = result.filter((raffle) => new Date(raffle.deadline) <= endsBeforeDate);
    }
  }

  if (sort === 'odds') {
    result.sort((a, b) => a.odds - b.odds);
  } else if (sort === 'deadline') {
    result.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
  }

  respondJson(res, {
    data: result,
    meta: {
      count: result.length,
      total: raffles.length,
      generatedAt: new Date().toISOString()
    }
  });
}

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon'
};

async function serveStatic(url, res) {
  try {
    let filePath = path.join(PUBLIC_DIR, decodeURIComponent(url.pathname));
    const fileInfo = await stat(filePath).catch(() => null);

    if (!fileInfo) {
      // fallback to index.html for non-existent paths
      filePath = path.join(PUBLIC_DIR, 'index.html');
    } else if (fileInfo.isDirectory()) {
      filePath = path.join(filePath, 'index.html');
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    const stream = createReadStream(filePath);
    stream.on('open', () => {
      res.writeHead(200, { 'Content-Type': contentType });
    });
    stream.on('error', (error) => {
      console.error('Static file error', error);
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Internal Server Error');
    });
    stream.pipe(res);
  } catch (error) {
    console.error('Failed to serve static asset', error);
    res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Internal Server Error');
  }
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === 'GET' && url.pathname.startsWith('/api/')) {
    handleApiRequest(url, res);
  } else if (req.method === 'GET') {
    serveStatic(url, res);
  } else {
    res.writeHead(405, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Method Not Allowed');
  }
});

server.listen(PORT, () => {
  console.log(`Raffle server running on http://localhost:${PORT}`);
});
