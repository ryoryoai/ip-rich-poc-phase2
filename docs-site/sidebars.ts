import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  docsSidebar: [
    "intro",
    "environments",
    {
      type: "category",
      label: "ワークフロー",
      items: [
        "workflow/overview",
        "workflow/infringement-analysis",
        "workflow/revenue-estimation",
      ],
    },
    {
      type: "category",
      label: "アーキテクチャ",
      items: ["architecture/phase2"],
    },
    {
      type: "category",
      label: "開発計画",
      items: [
        "phase2-development",
      ],
    },
  ],
};

export default sidebars;
