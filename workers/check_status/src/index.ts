import { CronJob } from 'cron';
import { db } from '@factura-cr/db';

console.log('🕒 Check Status Worker starting...');

// Poll Hacienda for pending invoices every 5 minutes
const job = new CronJob('*/5 * * * *', async () => {
  console.log('[Worker] Checking pending invoices...');
  
  try {
    const pendingDocs = await db.haciendaDocument.findMany({
      where: { haciendaStatus: 'procesando' },
      include: { invoice: true }
    });

    for (const doc of pendingDocs) {
      console.log(`[Worker] Polling Hacienda for Clave: ${doc.invoice.clave}`);
      
      try {
        const response = await fetch(`${process.env.BACKEND_URL}/invoices/${doc.invoice.id}/status/refresh`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.INTERNAL_WORKER_TOKEN}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const result = await response.json();
          console.log(`[Worker] Updated status for Invoice ${doc.invoice.id}: ${result.hacienda_status}`);
        } else {
          console.error(`[Worker] Failed to update status for ${doc.invoice.id}: ${response.statusText}`);
        }
      } catch (err) {
        console.error(`[Worker] Network error for ${doc.invoice.id}:`, err);
      }
    }
  } catch (error) {
    console.error('[Worker] Error polling invoices:', error);
  }
});

job.start();
