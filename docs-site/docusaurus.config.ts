import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

const config: Config = {
  title: "My Documentation",
  tagline: "Documentation site powered by Docusaurus",
  favicon: "img/favicon.ico",

  // Future flags
  future: {
    v4: true,
  },

  // Set the production url of your site here
  url: "https://docs.example.com",
  // Set the /<baseUrl>/ pathname under which your site is served
  baseUrl: "/",

  // GitHub pages deployment config
  organizationName: "your-org",
  projectName: "your-project",

  onBrokenLinks: "warn",
  onBrokenMarkdownLinks: "warn",

  // Internationalization
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.ts",
          routeBasePath: "/",
          editUrl: "https://github.com/your-org/your-project/tree/main/docs-site/",
        },
        blog: false,
        theme: {
          customCss: "./src/css/custom.css",
        },
      } satisfies Preset.Options,
    ],
  ],

  markdown: {
    mermaid: true,
  },
  themes: ["@docusaurus/theme-mermaid"],

  themeConfig: {
    image: "img/docusaurus-social-card.jpg",
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: "My Docs",
      logo: {
        alt: "My Docs Logo",
        src: "img/logo.svg",
      },
      items: [
        {
          type: "docSidebar",
          sidebarId: "docsSidebar",
          position: "left",
          label: "Documentation",
        },
        {
          href: "https://github.com/your-org/your-project",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Docs",
          items: [
            {
              label: "Getting Started",
              to: "/",
            },
          ],
        },
        {
          title: "More",
          items: [
            {
              label: "GitHub",
              href: "https://github.com/your-org/your-project",
            },
          ],
        },
      ],
      copyright: `Copyright � ${new Date().getFullYear()} My Project. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
