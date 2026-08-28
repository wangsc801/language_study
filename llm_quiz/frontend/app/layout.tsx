import { NavLink, Outlet } from "react-router";

const links = [
  { to: "/", label: "主页", end: true },
  { to: "/settings", label: "LLM 设置", end: false },
  { to: "/prompts", label: "Prompt 模板", end: false },
  { to: "/quizzes", label: "题目记录", end: false },
  { to: "/languages", label: "语言管理", end: false },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-100">
      <header className="sticky top-0 z-10 border-b border-gray-200 bg-white/80 backdrop-blur dark:border-gray-800 dark:bg-gray-900/80">
        <nav className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
          <span className="font-semibold text-sm tracking-wide">语言学习出题</span>
          <div className="flex gap-1">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.end}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 text-sm transition ${
                    isActive
                      ? "bg-blue-600 text-white"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-gray-100"
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}