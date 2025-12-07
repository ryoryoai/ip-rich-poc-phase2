import { prisma } from '@/lib/prisma';

/**
 * テスト用DBヘルパー関数
 */

export async function cleanupTestJobs(patentNumber: string) {
  try {
    // テスト用の特許番号に関連する未完了のジョブをクリーンアップ
    const deleted = await prisma.analysis_jobs.deleteMany({
      where: {
        patentNumber: patentNumber,
        status: { in: ['pending', 'researching'] }
      }
    });
    console.log(`Cleaned up ${deleted.count} test jobs for patent ${patentNumber}`);
    return deleted.count;
  } catch (error) {
    console.error('Failed to cleanup test jobs:', error);
    return 0;
  }
}

export async function getJobByPatentNumber(patentNumber: string) {
  return await prisma.analysis_jobs.findFirst({
    where: {
      patentNumber: patentNumber
    },
    orderBy: {
      createdAt: 'desc'
    }
  });
}

export async function getJobById(jobId: string) {
  return await prisma.analysis_jobs.findUnique({
    where: { id: jobId }
  });
}

export async function waitForJobStatus(
  jobId: string,
  expectedStatus: string[],
  maxRetries: number = 10,
  delayMs: number = 1000
): Promise<any> {
  for (let i = 0; i < maxRetries; i++) {
    const job = await getJobById(jobId);
    if (job && expectedStatus.includes(job.status)) {
      return job;
    }
    await new Promise(resolve => setTimeout(resolve, delayMs));
  }
  throw new Error(`Timeout waiting for job ${jobId} to reach status: ${expectedStatus.join(', ')}`);
}

export async function getAllJobsWithStatus(status: string) {
  return await prisma.analysis_jobs.findMany({
    where: { status },
    orderBy: { createdAt: 'desc' }
  });
}

/**
 * テスト終了後のクリーンアップ
 */
export async function disconnectPrisma() {
  await prisma.$disconnect();
}