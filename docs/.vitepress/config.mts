import { defineConfig, type DefaultTheme } from "vitepress";

const platform =
  process.env.DOCS_PLATFORM ??
  (process.env.GITHUB_ACTIONS === "true" ? "github" : "local");
if (!["local", "github", "domestic", "gitee"].includes(platform))
  throw new Error("Unknown DOCS_PLATFORM");
const defaultLang =
  process.env.DOCS_DEFAULT_LANG ?? (platform === "github" ? "en" : "zh");
if (!["zh", "en"].includes(defaultLang))
  throw new Error("DOCS_DEFAULT_LANG must be zh or en");
const prefix = (process.env.DOCS_BASE ?? "").trim().replace(/^\/+|\/+$/g, "");
if (
  prefix &&
  !prefix
    .split("/")
    .every((part) => /^[\w.-]+$/.test(part) && part !== "." && part !== "..")
) {
  throw new Error("DOCS_BASE must be a static URL path such as /w1-docs/");
}
const base = prefix ? "/" + prefix + "/" : "/";

type Entry = [string, string, string];
const chapters: { title: [string, string]; pages: Entry[] }[] = [
  {
    title: ["认识 W1", "Product guide"],
    pages: [
      ["产品概览", "Overview", "product/overview"],
      ["型号与规格", "Models and specifications", "product/specifications"],
      ["部件与接口", "Components and ports", "product/interfaces"],
    ],
  },
  {
    title: ["快速开始", "Getting started"],
    pages: [["首次接入", "First connection", "guide/quick-start"]],
  },
  {
    title: ["SDK 开发", "SDK guides"],
    pages: [
      ["集成 SDK", "SDK integration", "sdk/integration"],
      ["读取状态示例", "Read device state", "sdk/read-state"],
    ],
  },
  {
    title: ["API 参考", "API reference"],
    pages: [["公共接口", "Public interfaces", "api/reference"]],
  },
  {
    title: ["版本与支持", "Releases and support"],
    pages: [
      ["兼容性", "Compatibility", "support/compatibility"],
      ["发行说明", "Release notes", "support/releases"],
      [
        "故障排查与支持",
        "Troubleshooting and support",
        "support/troubleshooting",
      ],
    ],
  },
];

function locale(lang: "zh" | "en") {
  const zh = lang === "zh";
  const i = zh ? 0 : 1;
  const sidebar = chapters.map(({ title, pages }) => ({
    text: title[i],
    collapsed: false,
    items: pages.map((page) => ({
      text: page[i],
      link: "/" + lang + "/" + page[2],
    })),
  }));
  const themeConfig: DefaultTheme.Config = {
    nav: chapters.map(({ title }, n) => ({
      text: title[i],
      link: sidebar[n].items[0].link,
    })),
    sidebar,
    outline: { level: [2, 3], label: zh ? "本页目录" : "On this page" },
    docFooter: {
      prev: zh ? "上一页" : "Previous page",
      next: zh ? "下一页" : "Next page",
    },
    sidebarMenuLabel: zh ? "文档目录" : "Contents",
    langMenuLabel: zh ? "选择语言" : "Languages",
    returnToTopLabel: zh ? "回到顶部" : "Back to top",
    darkModeSwitchLabel: zh ? "外观" : "Appearance",
    lightModeSwitchTitle: zh ? "切换到浅色" : "Use light appearance",
    darkModeSwitchTitle: zh ? "切换到深色" : "Use dark appearance",
  };
  return {
    label: zh ? "简体中文" : "English",
    lang: zh ? "zh-CN" : "en",
    title: zh ? "W1 文档中心" : "W1 Documentation",
    themeConfig,
  };
}

export default defineConfig({
  base,
  title: "W1 Documentation",
  lang: defaultLang === "zh" ? "zh-CN" : "en",
  locales: { zh: locale("zh"), en: locale("en") },
  transformPageData(page) {
    if (page.relativePath === "index.md")
      return {
        frontmatter: {
          ...page.frontmatter,
          head: [
            [
              "meta",
              {
                "http-equiv": "refresh",
                content: "0;url=" + base + defaultLang + "/",
              },
            ],
          ],
        },
      };
  },
  themeConfig: {
    search: {
      provider: "local",
      options: {
        locales: {
          zh: {
            translations: {
              button: { buttonText: "搜索文档", buttonAriaLabel: "搜索文档" },
              modal: {
                displayDetails: "显示详情",
                resetButtonTitle: "清除搜索",
                backButtonTitle: "返回",
                noResultsText: "没有找到结果",
                footer: {
                  selectText: "打开",
                  navigateText: "选择",
                  closeText: "关闭",
                },
              },
            },
          },
        },
      },
    },
  },
});
