import { preview } from 'vite';

const port = Number.parseInt(process.env.PORT ?? '4173', 10);
const host = process.env.HOST ?? '127.0.0.1';

async function start() {
  try {
    const server = await preview({
      preview: {
        host,
        port,
        strictPort: true,
      },
    });

    server.printUrls();

    const close = async () => {
      await server.close();
    };

    for (const signal of ['SIGINT', 'SIGTERM']) {
      process.once(signal, async () => {
        await close();
        process.exit(0);
      });
    }
  } catch (error) {
    if (error && typeof error === 'object' && 'code' in error && error.code === 'EADDRINUSE') {
      console.error(`Port ${port} is already in use. Please stop the existing process or choose a different port.`);
    } else {
      console.error('Failed to start preview server:', error);
    }
    process.exit(1);
  }
}

start();
