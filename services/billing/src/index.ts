import express, { Request, Response } from 'express';
import { db } from '@factura-cr/db';

const app = express();
app.use(express.json());

const PORT = (process.env.PORT as string) || '3001';

// ─── Usage Events Endpoint ──────────────────────────────────
// Inspired by Lago: ingestion of usage data
app.post('/events', async (req: Request, res: Response) => {
  const { companyId, eventType, metadata } = req.body;

  if (!companyId || !eventType) {
    return res.status(400).json({ error: 'Missing companyId or eventType' });
  }

  try {
    // Track event for usage metering
    // In a real scenario, this might go to Kafka/Redis first
    console.log(`[Billing] Event received: ${eventType} for company ${companyId}`);
    
    // We could store this in a UsageEvent table (needs to be added to Prisma)
    // For now, let's just log and acknowledge
    res.status(202).json({ status: 'accepted', eventId: Math.random().toString(36).substring(7) });
  } catch (error) {
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// ─── Subscription Status ────────────────────────────────────
app.get('/subscription/:companyId', async (req: Request, res: Response) => {
  const { companyId } = req.params;
  
  try {
    const company = await db.company.findUnique({
      where: { id: companyId },
      select: { plan: true, planExpiresAt: true, isActive: true }
    });
    
    if (!company) return res.status(404).json({ error: 'Company not found' });
    
    res.json(company);
  } catch (error) {
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Billing Service running on port ${PORT}`);
});
