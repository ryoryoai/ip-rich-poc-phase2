import fs from 'fs/promises';
import path from 'path';
import type { IStorageProvider } from '@/interfaces/IStorageProvider';
import type { AnalysisResult } from '@/types/analysis';

/**
 * ローカルファイルシステムを使用したストレージプロバイダー
 * データはJSON形式で保存される
 */
export class LocalStorageProvider implements IStorageProvider {
  private dataDir: string;

  constructor(dataDir: string = './data/results') {
    this.dataDir = dataDir;
  }

  async saveAnalysis(data: AnalysisResult): Promise<string> {
    // データディレクトリを作成（存在しない場合）
    await fs.mkdir(this.dataDir, { recursive: true });

    const fileName = `analysis_${data.patentNumber}_${Date.now()}.json`;
    const filePath = path.join(this.dataDir, fileName);

    await fs.writeFile(filePath, JSON.stringify(data, null, 2), 'utf-8');

    console.log(`[LocalStorageProvider] Saved analysis to: ${filePath}`);
    return filePath;
  }

  async getAnalysis(id: string): Promise<AnalysisResult | null> {
    try {
      const data = await fs.readFile(id, 'utf-8');
      return JSON.parse(data) as AnalysisResult;
    } catch (error) {
      console.error(`[LocalStorageProvider] Failed to read analysis: ${id}`, error);
      return null;
    }
  }

  async listAnalyses(limit: number = 10): Promise<AnalysisResult[]> {
    try {
      const files = await fs.readdir(this.dataDir);
      const jsonFiles = files.filter((f) => f.endsWith('.json')).slice(0, limit);

      const analyses = await Promise.all(
        jsonFiles.map(async (file) => {
          const filePath = path.join(this.dataDir, file);
          const data = await fs.readFile(filePath, 'utf-8');
          return JSON.parse(data) as AnalysisResult;
        })
      );

      return analyses;
    } catch (error) {
      console.error('[LocalStorageProvider] Failed to list analyses', error);
      return [];
    }
  }

  getProviderName(): string {
    return 'Local Storage';
  }
}
