/**
 * 特許情報取得プロバイダーのインターフェース
 */
export interface IPatentProvider {
  /**
   * プロバイダー名を取得
   */
  getProviderName(): string;

  /**
   * 特許番号から特許情報を取得
   * @param patentNumber 特許番号（例: "7666636", "US7666636", "JP2020123456"）
   * @returns 特許情報
   */
  fetchPatent(patentNumber: string): Promise<PatentInfo>;

  /**
   * 特許の請求項を取得
   * @param patentNumber 特許番号
   * @returns 請求項のリスト
   */
  fetchClaims(patentNumber: string): Promise<string[]>;
}

/**
 * 特許情報
 */
export interface PatentInfo {
  /**
   * 特許番号
   */
  patentNumber: string;

  /**
   * 発明の名称
   */
  title: string;

  /**
   * 要約
   */
  abstract?: string;

  /**
   * 発明者
   */
  inventors?: string[];

  /**
   * 出願人/権利者
   */
  assignee?: string;

  /**
   * 出願日
   */
  filingDate?: string;

  /**
   * 発行日
   */
  publicationDate?: string;

  /**
   * 請求項（特に請求項1）
   */
  claims?: string[];

  /**
   * 詳細な説明
   */
  description?: string;

  /**
   * 分類（IPC/CPC）
   */
  classifications?: string[];

  /**
   * 引用文献
   */
  citations?: string[];
}