import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { researchRouter } from './routes/research';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3002;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use('/research', researchRouter);

// Health check
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'deep-research-service' });
});

app.listen(PORT, () => {
  console.log(`Deep Research Service running on http://localhost:${PORT}`);
});
