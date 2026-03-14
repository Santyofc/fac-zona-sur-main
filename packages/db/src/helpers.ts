import { db } from './index'

export async function getCompany(companyId: string) {
  return db.company.findUnique({
    where: { id: companyId },
    include: {
      users: true,
      plan: true, // If we add a separate Plan model later
    }
  })
}

export async function createUsageEvent(data: { companyId: string, type: string, metadata?: any }) {
  // Logic for tracking usage (SaaS style)
  console.log(`[Usage] ${data.type} for company ${data.companyId}`)
}
